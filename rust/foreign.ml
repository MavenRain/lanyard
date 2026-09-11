(** Target constants consume checked, pinned metadata. The async slice supports
    database effects; schema instantiation needs the later crate printer. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Syntax = Kanon_surface.Syntax
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let refuse text = Error (Error.Not_yet ("Rust emission: " ^ text))
let invalid text = Error (Error.Mismatch ("Rust emission: " ^ text))
let lookup entries name = List.find_opt (fun (entry : Catalog.entry) -> String.equal entry.name name) entries
  |> Option.to_result ~none:(Error.Mismatch ("Rust emission: missing print rule " ^ name))
let rec telescope ty = Elab.arrow_split ty |> Option.fold
  ~none:([], ty) ~some:(fun (binder, rest) -> let binders, result = telescope rest in binder :: binders, result)
let foreign_type entries name arguments =
  let* entry = List.find_opt (fun (entry : Catalog.entry) ->
    String.equal (Elab.target_name entry.name) name && match entry.kind with
      | Catalog.Type_constant -> true | Catalog.Constant | Catalog.Schema -> false) entries
    |> Option.to_result ~none:(Error.Not_yet ("Rust emission: foreign type " ^ name)) in
  let* syntax = Elab.target_type entry.kernel_type in
  let binders, result = telescope syntax in
  let* () = if result = Syntax.SType 0 && List.for_all (fun binder ->
    Quantity.equal binder.Syntax.b_q Quantity.Zero && binder.Syntax.b_ty = Syntax.SType 0) binders
    && List.map (fun _binder -> Catalog.Zero) binders = entry.quantities
    && List.is_empty entry.effects then Ok () else invalid ("foreign type metadata: " ^ name) in
  let* () = if List.length binders = List.length arguments then Ok ()
    else invalid ("foreign type argument count: " ^ name) in
  let* template = Template.parse entry.print_rule in
  let bindings = Seq.zip (List.to_seq binders) (List.to_seq arguments)
    |> Seq.map (fun (binder, argument) -> binder.Syntax.b_name, argument) |> List.of_seq in
  Template.render template bindings
let foreign_call entries (row : Rir.foreign) =
  let* entry = lookup entries row.schema in
  let* () = match entry.kind with
    | Catalog.Constant -> Ok ()
    | Catalog.Schema -> refuse ("foreign schema " ^ row.schema)
    | Catalog.Type_constant -> invalid ("type used as a call: " ^ row.schema) in
  let* () = if String.equal row.print_rule entry.print_rule && row.effects = entry.effects
    && String.equal row.name (Elab.target_name entry.name) && List.is_empty row.type_arguments
    then Ok () else invalid ("foreign metadata differs: " ^ row.name) in
  let* effect = match row.effects with
    | [] -> Ok Effects.Sync
    | ["DbExec"; "toasty::Error"] -> Ok Effects.Async_db
    | _ :: _ -> refuse ("effectful foreign call " ^ row.name) in
  let* syntax = Elab.target_type entry.kernel_type in
  let binders, result = telescope syntax in
  let* () = if row.arity = List.length binders then Ok () else invalid "foreign arity" in
  let quantity = function Catalog.Zero -> Quantity.Zero | Catalog.One -> Quantity.One | Catalog.Many -> Quantity.Many in
  let* () = if List.map (fun b -> b.Syntax.b_q) binders = List.map quantity entry.quantities
    then Ok () else invalid "foreign quantities" in
  let repr syntax =
    if syntax = Syntax.SProd [] then Ok (Rir.TyStruct (Rir.Tid "tuple<>")) else
    let* name = Elab.var_name syntax |> Option.to_result
      ~none:(Error.Not_yet "Rust emission: non-atomic foreign call type") in
    let* _path = foreign_type entries name [] in Ok (Rir.TyForeign (name, [])) in
  let* params = Rules.all_ok (List.map (fun b ->
    let* ty = repr b.Syntax.b_ty in Ok (Rir.owned b.Syntax.b_q ty)) binders) in
  let* result = repr result in
  let parameters = List.map (fun b -> b.Syntax.b_name, b.Syntax.b_q) binders in
  Ok (params, result, (fun arguments -> Template.call ~parameters ~types:[] ~arguments entry.print_rule), effect)
module Printer = Emit.Make (struct
  let foreign_type = foreign_type Catalog.entries
  let foreign_layout = foreign_type
  let foreign_call = foreign_call Catalog.entries
end)
let source = Printer.native
