(** Closed Db.connect aliases select nominal models before erasure. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Lower = Kanon_surface.Lower
module Catalog = Lanyard_target.Target_generated
module Printer = Foreign.Printer
let ( let* ) = Result.bind
let invalid text = Error (Error.Mismatch ("Rust emission: " ^ text))
let refuse text = Error (Error.Not_yet ("Rust emission: " ^ text))
type t = { row : Rir.foreign; models : string list; family : string; repr : Rir.repr; data : Rir.tid list }
let catalog (checked : Elab.lan_program) models (instances : Lower.connection list) =
  let rec select seen = function
    | Term.Global name -> Option.fold ~some:(fun rust () -> Ok [rust])
        ~none:(fun () -> if List.mem name seen then invalid "connection model alias cycle" else
          (Global.find_def name checked.globals |> Option.fold
            ~none:(fun () -> refuse ("connection requires a declared model: " ^ name))
            ~some:(fun definition () -> select (name :: seen) definition.Global.def)) ())
        (List.assoc_opt name models) ()
    | Term.Ran (Shape.SColl count, Term.Sec (Shape.SColl arity, legs))
        when count = arity && count = List.length legs
          && List.for_all (fun leg -> List.is_empty leg.Term.l_binders) legs ->
        let* groups = Rules.all_ok (List.map (fun leg -> select seen leg.Term.l_body) legs) in
        Ok (List.concat groups)
    | Term.Ann (term, _ty) -> select seen term
    | Term.Var _ | Term.Univ _ | Term.Lan _ | Term.Ran _ | Term.In _ | Term.Elim _
    | Term.Sec _ | Term.Out _ | Term.Let _ | Term.Lit _ | Term.Auto ->
        refuse "connection requires declared models or a product of models" in
  Rules.all_ok (List.map (fun (instance : Lower.connection) ->
    let* selected = select [] instance.models in
    let* () = if List.is_empty selected then refuse "connection requires at least one model"
      else if List.length selected <> List.length (List.sort_uniq String.compare selected)
      then invalid "connection has duplicate models" else Ok () in
    let ec : Erase.ectx = { c = Check.make checked.globals Budget.unlimited;
      slots = []; self = instance.wrapper } in
    let* ty = Eval.eval checked.globals [] instance.text in
    let* repr = Erase.repr_of ec ty in
    let* tid = Erase.tid_of ec ty in
    let* data = Erase.complete_groups ec [tid] in
    let* families = Printer.family_catalog [instance.wrapper, Erase.Code [Rir.RData data]] in
    let* family = List.find_opt (fun (family : Printer.family) ->
      repr = Rir.TyUnion (Erase.mu_tid family.family_name)
      && family.variants = [[]; [Printer.Nat; Printer.Nominal family.family_name]]) families
      |> Option.to_result ~none:(Error.Not_yet "Rust emission: connection URL requires a byte list") in
    Ok { row = instance.row; models = selected; family = family.family_name; repr; data }) instances)
let foreign_call entries connections (row : Rir.foreign) =
  let* connection = List.find_opt (fun connection -> connection.row = row) connections
    |> Option.to_result ~none:(Error.Mismatch "Rust emission: connection metadata differs") in
  let* entry = Foreign.lookup entries "Db.connect" in
  let* () = match entry.kind with Catalog.Schema -> Ok ()
    | Catalog.Constant | Catalog.Type_constant -> invalid "connection schema kind" in
  let* expected = Elab.target_type "(0 Models : Type 0) -> (0 Text : Type 0) -> (url : Text) -> Db" in
  let* actual = Elab.target_type entry.kernel_type in
  let* () = if actual = expected && entry.quantities = [Catalog.Zero; Catalog.Zero; Catalog.Many]
      && entry.effects = ["DbExec"; "toasty::Error"] && row.effects = entry.effects
      && row.schema = entry.name && row.print_rule = entry.print_rule && row.arity = 1
    then Ok () else invalid "connection schema metadata" in
  let* template = Template.parse entry.print_rule in
  let* () = if List.sort_uniq String.compare (Template.slots template) = ["Models"; "url"]
    then Ok () else invalid "connection schema placeholders" in
  let render = function
    | [url] ->
        let* call = Template.render template ["Models", String.concat ", " connection.models; "url", "&__lan_url"] in
        Ok ("{ let __lan_url_arg = " ^ url ^ "; let __lan_url = "
          ^ Printer.identifier "lan_model_text_to_" connection.family ^ "(&__lan_url_arg)?; " ^ call ^ " }")
    | [] | _ :: _ -> invalid "connection argument count" in
  Ok ([Rir.TyArc connection.repr], Rir.TyForeign ("Db", []), render, Effects.Async_db)
