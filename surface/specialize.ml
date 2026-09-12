(** Retain closed connection arguments before quantity erasure. Each distinct
    application gets a checked private wrapper in the lowering environment. *)
open Kanon_kernel
let ( let* ) = Result.bind
let arguments = function
  | Term.Out (_, Term.APt (Quantity.Zero, text),
      Term.Out (_, Term.APt (Quantity.Zero, models), Term.Global "Db_connect")) -> Some (models, text)
  | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
  | Term.Sec _ | Term.Out _ | Term.Let _ | Term.Ann _ | Term.Global _ | Term.Lit _ | Term.Auto -> None
type state = { globals : Global.t; wrappers : (Term.t * string * Global.entry) list; next : int }
let rec fresh globals index =
  let name = "__lan_connect_" ^ string_of_int index in
  if Option.is_some (Global.find name globals) || Option.is_some (Global.find_family name globals)
  then fresh globals (index + 1) else name, index + 1
let instance state term =
  List.find_opt (fun (source, _name, _entry) -> source = term) state.wrappers
  |> Option.fold ~some:(fun (_source, name, _entry) () -> Ok (state, Term.Global name))
    ~none:(fun () ->
      let c = Check.make state.globals Budget.unlimited in
      let* ty = Check.infer c Quantity.Many term |> Result.map_error (fun _error ->
        Error.Not_yet "Rust emission: connection type arguments must be closed") in
      let* ty = Eval.quote state.globals 0 ty in
      let name, next = fresh state.globals state.next in
      let* entry = Check.check_decl state.globals Budget.unlimited
        { Check.d_name = name; d_kind = Check.Definition; d_ty = ty; d_body = Some term } in
      Ok ({ globals = Global.add name entry state.globals;
            wrappers = (term, name, entry) :: state.wrappers; next }, Term.Global name))
  |> fun create -> create ()
let rec map transform state sources = match sources with
  | [] -> Ok (state, [])
  | source :: rest ->
      let* state, value = transform state source in
      let* state, rest = map transform state rest in Ok (state, value :: rest)
let rec term state source =
  if Option.is_some (arguments source) then instance state source else
  match source with
  | Term.Var _ | Term.Global _ | Term.Lit _ | Term.Auto | Term.Univ _
  | Term.Lan _ | Term.Ran _ -> Ok (state, source)
  | Term.In (shape, address, args) ->
      let ctor = Option.bind (Shape.family shape) (fun name ->
        Option.bind (Global.find_family name state.globals) (fun family ->
          Option.bind (Term.as_actor address) (fun name ->
            List.find_opt (fun ctor -> String.equal ctor.Positivity.c_name name) family.f_ctors))) in
      let* state, address = point state address in
      let* state, args = Option.fold ~none:(fun () -> map term state args)
        ~some:(fun ctor () -> fields state ctor.Positivity.c_args args) ctor () in
      Ok (state, Term.In (shape, address, args))
  | Term.Out (shape, address, head) ->
      let* state, head = term state head in
      let* state, address = point state address in
      Ok (state, Term.Out (shape, address, head))
  | Term.Sec (shape, legs) ->
      let* state, legs = map leg state legs in Ok (state, Term.Sec (shape, legs))
  | Term.Let (name, ty, value, body) ->
      let* state, value = term state value in
      let* state, body = term state body in Ok (state, Term.Let (name, ty, value, body))
  | Term.Ann (body, ty) ->
      let* state, body = term state body in Ok (state, Term.Ann (body, ty))
  | Term.Elim elim ->
      let* state, scrut = term state elim.Term.e_scrut in
      let* state, branches = map (fun state (address, branch) ->
        let* state, branch = leg state branch in Ok (state, (address, branch))) state elim.e_branches in
      Ok (state, Term.Elim { elim with e_scrut = scrut; e_branches = branches })
and point state address = match address with
  | Term.APt (Quantity.Zero, _) | Term.ALeg _ | Term.ACtor _ -> Ok (state, address)
  | Term.APt ((Quantity.One | Quantity.Many as quantity), arg) ->
      let* state, arg = term state arg in Ok (state, Term.APt (quantity, arg))
and leg state (source : Term.leg) =
  let* state, body = term state source.l_body in Ok (state, { source with l_body = body })
and fields state quantities sources = match quantities, sources with
  | [], [] -> Ok (state, [])
  | (quantity, _name, _ty) :: quantities, source :: sources ->
      let* state, value = if Quantity.equal quantity Quantity.Zero then Ok (state, source)
        else term state source in
      let* state, rest = fields state quantities sources in Ok (state, value :: rest)
  | [], _ :: _ | _ :: _, [] -> Error (Error.Mismatch "connection specialization: constructor arity")
let program (checked : Elab.lan_program) =
  let* state, rows = map (fun state (name, entry) -> match entry with
    | Global.Axiom _ | Global.Prim _ -> Ok (state, (name, entry))
    | Global.Def definition ->
        if Option.is_some (arguments definition.def) then Ok (state, (name, entry)) else
        let* state, body = term state definition.def in
        let entry = Global.Def { definition with def = body } in
        Ok ({ state with globals = Global.add name entry state.globals }, (name, entry)))
    { globals = checked.globals; wrappers = []; next = 0 } checked.rows in
  let wrappers = List.rev_map (fun (_source, name, entry) -> name, entry) state.wrappers in
  Ok { checked with globals = state.globals; rows = wrappers @ rows }
