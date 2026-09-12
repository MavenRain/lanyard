(** The checked target metadata crosses into Rust IR at this boundary. *)
open Kanon_kernel
let ( let* ) = Result.bind

let runtime_arity globals name =
  let* entry = Global.find name globals
    |> Option.to_result ~none:(Error.Unbound name) in
  let ty = match entry with
    | Global.Axiom row -> row.Global.ax_ty
    | Global.Def row -> row.Global.ty
    | Global.Prim row -> row.Global.p_ty in
  let ec : Erase.ectx = { c = Check.make globals Budget.unlimited; slots = []; self = name } in
  let* ty = Eval.eval globals [] ty in
  let* count = match Erase.form_of ty with
    | Erase.FRan (shape, fibre) -> Erase.arity_of ec 0 shape fibre
    | Erase.FLan _ | Erase.FUniv | Erase.FNat | Erase.FOther -> Ok 0 in
  Ok count

let foreign_row globals name (schema : Elab.Target.entry) arguments =
  let* arity = runtime_arity globals name in
  Ok { Rir.name; schema = schema.name; print_rule = schema.print_rule;
       effects = schema.effects; type_arguments = arguments; arity }

let catalog (program : Elab.lan_program) =
  let* constants = Rules.all_ok (List.filter_map (fun (row : Elab.Target.entry) ->
    match row.kind with
    | Elab.Target.Type_constant | Elab.Target.Schema -> None
    | Elab.Target.Constant -> Some (foreign_row program.globals
        (Elab.target_name row.name) row [])) Elab.Target.entries) in
  let* instances = Rules.all_ok (List.map (fun (instance : Elab.foreign_instance) ->
    let* arguments = Rules.all_ok (List.map (fun (name, syntax) ->
      let c = Check.make program.globals Budget.unlimited in
      let* term = Elab.elab c ~expected:None syntax in
      Ok (name, Pp.term [] term)) instance.type_arguments) in
    foreign_row program.globals instance.instance_name instance.schema arguments)
    program.instances) in
  Ok (constants @ instances)

(** A closed connection alias retains its erased schema arguments. Its
    wrapper stays a native function; the generic call resolves only there. *)
type connection = { wrapper : string; models : Term.t; text : Term.t; row : Rir.foreign }
let connections (program : Elab.lan_program) =
  let arguments = function
    | Term.Out (_, Term.APt (Quantity.Zero, text),
        Term.Out (_, Term.APt (Quantity.Zero, models), Term.Global "Db_connect")) -> Some (models, text)
    | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
    | Term.Sec _ | Term.Out _ | Term.Let _ | Term.Ann _ | Term.Global _ | Term.Lit _ | Term.Auto -> None in
  Rules.all_ok (List.filter_map (fun (wrapper, entry) -> match entry with
    | Global.Axiom _ | Global.Prim _ -> None
    | Global.Def definition -> Option.map (fun (models, text) ->
        let* schema = List.find_opt (fun (entry : Elab.Target.entry) ->
          String.equal entry.name "Db.connect") Elab.Target.entries
          |> Option.to_result ~none:(Error.Unbound "Db.connect") in
        let* row = foreign_row program.globals wrapper schema
          ["Models", Pp.term [] models; "Text", Pp.term [] text] in
        Ok { wrapper; models; text; row = { row with name = "Db_connect" } })
        (arguments definition.Global.def)) program.rows)

(** The emitted parameter count of every function item, lifted ones included.
    A direct call to a native name is checked against this count. *)
let emitted_arities rows =
  List.concat_map (fun ((_name : string), (entry : Erase.entry)) ->
    match entry with
    | Erase.Dropped | Erase.Postulate _ -> []
    | Erase.Code decls -> List.filter_map (fun (decl : Rir.rdecl) ->
        match decl with
        | Rir.RData _ -> None
        | Rir.RFun (fid, params, _result, _body) ->
            Some (Rir.fid_text fid, Some (List.length params))) decls) rows

(** The caller supplies the lowered connections once. A second lowering
    repeats the whole program scan and builds equal but distinct rows. *)
let program_with (connections : connection list) (checked : Elab.lan_program) =
  let* foreign = catalog checked in
  let* rows = Erase.program checked.globals checked.rows in
  let emitted = emitted_arities rows in
  let* known = Global.StringMap.bindings checked.globals.Global.entries
    |> List.filter_map (fun (name, entry) -> match entry with
      | Global.Def _ -> Some (Ok (name, Option.join (List.assoc_opt name emitted)))
      | Global.Prim _ ->
          (* A prim emits no function item, so its parameter count comes
             from the runtime arity of its type, as a foreign row does. *)
          Some (runtime_arity checked.globals name
                |> Result.map (fun (count : int) -> (name, Some count)))
      | Global.Axiom _ -> None)
    |> Rules.all_ok in
  let table = emitted @ known in
  Rules.all_ok (List.map (fun (name, entry) ->
    match entry with
    | Erase.Dropped | Erase.Postulate _ -> Ok (name, entry)
    | Erase.Code decls ->
        let foreign = List.filter_map (fun connection ->
          if String.equal connection.wrapper name then Some connection.row else None) connections @ foreign in
        let* decls = Rules.all_ok (List.map (Rir.resolve_decl ~known:table foreign) decls) in
        Ok (name, Erase.Code decls)) rows)

let program (checked : Elab.lan_program) =
  let* connections = connections checked in
  program_with connections checked
