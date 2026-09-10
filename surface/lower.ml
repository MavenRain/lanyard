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

let program (checked : Elab.lan_program) =
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
        let* decls = Rules.all_ok (List.map (Rir.resolve_decl ~known:table foreign) decls) in
        Ok (name, Erase.Code decls)) rows)
