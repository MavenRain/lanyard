(** Specialize finite, checked signature eliminations for crate emission.
    Only values may be substituted. Computations retain call by value lets,
    including unused computations, so foreign calls keep their order and count. *)
open Kanon_kernel
let ( let* ) = Result.bind
let refusal text = Error (Error.Not_yet ("Rust handler fusion: " ^ text))
let mentions names = Term.exists_name ~include_families:true names
let family names shape = Option.fold ~none:false
  ~some:(fun name -> List.mem name names) (Shape.family shape)

let rec value globals = function
  | Term.Var _ | Term.Lit _ | Term.Univ _ | Term.Lan _ | Term.Ran _ -> true
  | Term.Sec (Shape.SPi _, _) -> true
  | Term.Sec ((Shape.SColl _ | Shape.SPar _ | Shape.SMu _ | Shape.SNu _), legs) ->
      List.for_all (fun (leg : Term.leg) -> leg.l_binders = [] && value globals leg.l_body) legs
  | Term.In (shape, address, args) ->
      let point_value = match address with
        | Term.APt (q, point) -> Quantity.equal q Quantity.Zero || value globals point
        | Term.ALeg _ | Term.ACtor _ -> true in
      let fields = Option.bind (Shape.family shape) (fun name ->
        Option.bind (Global.find_family name globals) (fun family ->
          Option.bind (Term.as_actor address) (fun name ->
            List.find_opt (fun ctor -> String.equal ctor.Positivity.c_name name) family.f_ctors))) in
      point_value && (Option.bind fields (fun ctor -> Rules.zip ctor.Positivity.c_args args)
      |> Option.fold ~none:(fun () -> List.for_all (value globals) args)
        ~some:(fun pairs () -> List.for_all (fun ((q, _name, _ty), arg) ->
          Quantity.equal q Quantity.Zero || value globals arg) pairs)
      |> fun decide -> decide ())
  | Term.Ann (body, _ty) -> value globals body
  | Term.Global _ | Term.Out _ | Term.Elim _ | Term.Let _ | Term.Auto -> false

(* Specialization state: the remaining budget and the bodies of the globals
   that are already specialized. A definition is closed, so its specialized
   body is the same at every occurrence. The budget therefore pays for the
   first specialization of a global and for every term that specialization
   creates, never for a second visit to the same shared definition. *)
type state = { fuel : int; seen : (string * Term.t) list }

let remember name body state = { state with seen = (name, body) :: state.seen }

(* The ascriptions a value already carries came from the binders it passed
   through. They are convertible with the binder it now replaces, so they are
   dropped. Without this a chain of substitutions stacks one ascription per
   step and doubles the size of the specialized body at every level. *)
let rec bare = function
  | Term.Ann (body, _stale) -> bare body
  | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
  | Term.Sec _ | Term.Out _ | Term.Let _ | Term.Global _ | Term.Lit _ | Term.Auto as body -> body

(* A substituted value carries the type of the binder it replaces, so positions
   the kernel infers rather than checks keep a type of their own. *)
let annotate ty value = Term.Ann (bare value, ty)

let rec map transform state = function
  | [] -> Ok (state, [])
  | source :: rest ->
      let* state, source = transform state source in
      let* state, rest = map transform state rest in Ok (state, source :: rest)

let rec term globals signatures state source =
  if state.fuel <= 0 then refusal "specialization budget exhausted" else
  let state = { state with fuel = state.fuel - 1 } in
  let next = term globals signatures in
  match source with
  | Term.Var _ | Term.Lit _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.Auto -> Ok (state, source)
  | Term.Global name ->
      Global.find_def name globals
      |> Option.fold ~none:(fun () -> Ok (state, source)) ~some:(fun definition () ->
        if definition.Global.reducible && Option.is_none definition.rec_arg && not definition.partial
        then unfold globals signatures state name definition.def else Ok (state, source))
      |> fun decide -> decide ()
  | Term.Ann (body, ty) ->
      let* state, body = next state body in Ok (state, annotate ty body)
  | Term.Let (name, ty, definition, body) ->
      let* state, definition = next state definition in
      bind globals signatures state name ty definition body
  | Term.Sec (shape, legs) ->
      let* state, legs = map (fun state (leg : Term.leg) ->
        let* state, body = next state leg.l_body in Ok (state, { leg with l_body = body })) state legs in
      Ok (state, Term.Sec (shape, legs))
  | Term.In (shape, address, args) ->
      let* state, args = map next state args in
      construct globals signatures state shape address args
  | Term.Out (shape, address, head) ->
      let* state, head = next state head in
      let* state, address = match address with
        | Term.APt (Quantity.Zero, _) | Term.ALeg _ | Term.ACtor _ -> Ok (state, address)
        | Term.APt ((Quantity.One | Quantity.Many as q), arg) ->
            let* state, arg = next state arg in Ok (state, Term.APt (q, arg)) in
      apply globals signatures state shape address head
  | Term.Elim e ->
      let* state, scrut = next state e.e_scrut in
      eliminate globals signatures state { e with e_scrut = scrut }
and unfold globals signatures state name definition =
  List.assoc_opt name state.seen
  |> Option.fold
    ~none:(fun () -> Result.map (fun (state, body) -> (remember name body state, body))
      (term globals signatures state definition))
    ~some:(fun body () -> Ok (state, body))
  |> fun decide -> decide ()
and bind globals signatures state name ty definition body =
  let next = term globals signatures in
  (* The substituted value carries its binder type, so positions the kernel
     infers rather than checks keep a type of their own. *)
  if value globals definition
  then next state (Term_scope.instantiate [annotate ty definition] body) else
  match definition with
  | Term.Let (inner, inner_ty, inner_value, inner_body) ->
      next state (Term.Let (inner, inner_ty, inner_value,
        Term.Let (name, Term_scope.shift 1 ty, inner_body, Term_scope.shift ~depth:1 1 body)))
  | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
  | Term.Sec _ | Term.Out _ | Term.Ann _ | Term.Global _ | Term.Lit _ | Term.Auto ->
      let* state, body = next state body in Ok (state, Term.Let (name, ty, definition, body))
and construct globals signatures state shape address args =
  if not (family signatures shape) then Ok (state, Term.In (shape, address, args)) else
  let* family = Option.bind (Shape.family shape) (fun name -> Global.find_family name globals)
    |> Option.to_result ~none:(Error.Mismatch "handler family metadata") in
  let* ctor = Option.bind (Term.as_actor address) (fun name ->
      List.find_opt (fun ctor -> String.equal ctor.Positivity.c_name name) family.f_ctors)
    |> Option.to_result ~none:(Error.Mismatch "handler constructor metadata") in
  let* pairs = Rules.zip ctor.c_args args
    |> Option.to_result ~none:(Error.Mismatch "handler constructor arguments") in
  if List.for_all (fun ((q, _name, _ty), arg) -> Quantity.equal q Quantity.Zero || value globals arg) pairs
  then Ok (state, Term.In (shape, address, args)) else
  let count = List.length args in
  let packed = Term.In (shape, address, List.init count (fun index -> Term.Var (count - index - 1))) in
  let function_body = List.fold_right (fun (q, name, ty) body ->
    Term.Sec (Shape.SPi (q, name, ty), [{ Term.l_binders = [q, name]; l_body = body }]))
    ctor.c_args packed in
  let applied, _supplied = List.fold_left (fun (head, supplied) ((q, name, ty), arg) ->
    Term.Out (Shape.SPi (q, name, Term_scope.instantiate supplied ty), Term.APt (q, arg), head),
    supplied @ [arg]) (function_body, []) pairs in
  term globals signatures state applied
and apply globals signatures state shape address head =
  let next = term globals signatures in
  match head with
  | Term.Ann (body, _ty) -> apply globals signatures state shape address body
  | Term.Let (name, ty, definition, body) ->
      let lifted = Term_scope.shift 1 (Term.Out (shape, address, Term.Var 0)) in
      (match lifted with
       | Term.Out (shape, address, _placeholder) ->
           next state (Term.Let (name, ty, definition, Term.Out (shape, address, body)))
       | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
       | Term.Sec _ | Term.Let _ | Term.Ann _ | Term.Global _ | Term.Lit _ | Term.Auto ->
           refusal "application reconstruction")
  | Term.Sec (Shape.SPi (_quantity, _name, dom), [leg]) ->
      (match address, leg.Term.l_binders with
       | Term.APt (q, arg), [(_quantity, name)] ->
           if Quantity.equal q Quantity.Zero || value globals arg
           then next state (Term_scope.instantiate [annotate dom arg] leg.l_body)
           else next state (Term.Let (name, dom, arg, leg.l_body))
       | Term.APt _, ([] | _ :: _ :: _) | (Term.ALeg _ | Term.ACtor _), _ ->
           Ok (state, Term.Out (shape, address, head)))
  | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
  | Term.Sec _ | Term.Out _ | Term.Global _ | Term.Lit _ | Term.Auto ->
      Ok (state, Term.Out (shape, address, head))
and eliminate globals signatures state e =
  let next = term globals signatures in
  let residual () =
    let* state, branches = map (fun state (address, (branch : Term.leg)) ->
      let* state, body = next state branch.l_body in
      Ok (state, (address, { branch with l_body = body }))) state e.Term.e_branches in
    Ok (state, Term.Elim { e with e_branches = branches }) in
  if not (family signatures e.e_shape) then residual () else
  match e.e_scrut with
  | Term.Ann (scrut, _ty) -> eliminate globals signatures state { e with e_scrut = scrut }
  | Term.Let (name, ty, definition, body) ->
      (match Term_scope.shift 1 (Term.Elim e) with
       | Term.Elim lifted -> next state (Term.Let (name, ty, definition,
           Term.Elim { lifted with e_scrut = body }))
       | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Sec _
       | Term.Out _ | Term.Let _ | Term.Ann _ | Term.Global _ | Term.Lit _ | Term.Auto ->
           refusal "elimination reconstruction")
  | Term.In (shape, Term.ACtor name, args) when shape = e.e_shape && value globals e.e_scrut ->
      let* _address, branch =
        List.find_opt (fun (address, _branch) -> address = Term.ACtor name) e.e_branches
        |> Option.to_result ~none:(Error.Mismatch "handler constructor branch") in
      let ascribed = Option.bind (Shape.family shape) (fun family_name ->
          Option.bind (Global.find_family family_name globals) (fun family ->
            Option.bind (List.find_opt (fun ctor ->
                String.equal ctor.Positivity.c_name name) family.f_ctors)
              (fun ctor -> Rules.zip ctor.Positivity.c_args args)))
        |> Option.fold ~none:(fun () -> args) ~some:(fun pairs () ->
          List.rev (fst (List.fold_left (fun (ascribed, supplied) ((_q, _name, ty), arg) ->
            annotate (Term_scope.instantiate supplied ty) arg :: ascribed,
            supplied @ [arg]) ([], []) pairs)))
        |> fun decide -> decide () in
      if List.length args = List.length branch.l_binders
      then next state (Term_scope.instantiate ascribed branch.l_body)
      else refusal "recursive induction hypotheses are unsupported"
  | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
  | Term.Sec _ | Term.Out _ | Term.Global _ | Term.Lit _ | Term.Auto -> residual ()

let program (checked : Elab.lan_program) =
  let* rows = Rules.all_ok (List.map (fun (name, entry) -> match entry with
    | Global.Axiom _ | Global.Prim _ -> Ok (name, entry)
    | Global.Def definition ->
        if not (mentions checked.signatures definition.def) || Option.is_some definition.rec_arg
        then Ok (name, entry) else
        let* _state, body = term checked.globals checked.signatures
          { fuel = 4096; seen = [] } definition.def in
        let* ty = Eval.eval checked.globals [] definition.ty in
        let* () = Check.check_term checked.globals body ty
          |> Result.map_error (fun error -> Error.Not_yet
            ("Rust handler fusion: " ^ name ^ ": kernel recheck: " ^ Error.to_string error)) in
        Ok (name, Global.Def { definition with def = body })) checked.rows) in
  let globals = List.fold_left (fun globals (name, entry) -> Global.add name entry globals)
    checked.globals rows in
  Ok { checked with globals; rows }

let closed (checked : Elab.lan_program) =
  let* () = Rules.all_ok (List.map (fun (name, entry) -> match entry with
    | Global.Axiom _ | Global.Prim _ -> Ok ()
    | Global.Def definition ->
        if mentions checked.signatures definition.def || mentions checked.signatures definition.ty
        then refusal (name ^ ": signature program is not statically fused") else Ok ()) checked.rows)
    |> Result.map (fun _checks -> ()) in
  Ok checked
