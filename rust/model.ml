(** Model fields store Nat through checked i64 conversions and two-unit sums as bool.
    Checked model instances select schemas; only the key field id keeps its source name. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Lower = Kanon_surface.Lower
module Catalog = Lanyard_target.Target_generated
module Printer = Foreign.Printer
let ( let* ) = Result.bind
let invalid text = Error (Error.Mismatch ("Rust emission: " ^ text))
let refuse text = Error (Error.Not_yet ("Rust emission: " ^ text))
type scalar = Nat_field | Bool_field
type t = { name : string; fields : (string * scalar) list; repr : Rir.repr; instances : Rir.foreign list }
let bool_repr = Rir.TyUnion (Rir.Tid "sum<struct tuple<>|struct tuple<>>")
let bool_type = Printer.rust_type (Printer.Sum [Printer.Unit; Printer.Unit])
let storage_type = function Nat_field -> "i64" | Bool_field -> "bool"
let to_storage scalar value = match scalar with
  | Nat_field -> "lan_model_to_i64(&" ^ value ^ ")?"
  | Bool_field -> "match &" ^ value ^ " { " ^ bool_type ^ "::V0(()) => false, "
      ^ bool_type ^ "::V1(()) => true }"
let from_storage scalar value = match scalar with
  | Nat_field -> "lan_model_from_i64(" ^ value ^ ")?"
  | Bool_field -> "if " ^ value ^ " { " ^ bool_type ^ "::V1(()) } else { " ^ bool_type ^ "::V0(()) }"
let rust_name model = Printer.identifier "LanModel" model.name
let field_name name = if String.equal name "id" then "id" else Printer.identifier "f_" name
let catalog (checked : Elab.lan_program) =
  if List.is_empty checked.models then Ok [] else
  let* instances = Lower.catalog checked in
  Rules.all_ok (List.map (fun (model : Elab.model_info) ->
    let ec : Erase.ectx = { c = Check.make checked.globals Budget.unlimited;
      slots = []; self = model.model_name } in
    let representation syntax =
      let* term = Elab.elab ec.c ~expected:None syntax in
      let* ty = Eval.eval checked.globals [] term in Erase.repr_of ec ty in
    let* fields = Rules.all_ok (List.map (fun (field, syntax) ->
      let* repr = representation syntax in
      let is_key = String.equal field "id" in
      match () with
      | () when repr = Rir.TyUnion (Rir.Tid "nat") -> Ok (field, Nat_field)
      | () when repr = bool_repr && not is_key -> Ok (field, Bool_field)
      | () -> refuse ("model field " ^ model.model_name ^ "." ^ field ^ " requires "
        ^ (if is_key then "Nat" else "Nat or Bool (a two-unit sum)"))) model.fields) in
    let* () = if List.mem_assoc "id" model.fields then Ok () else invalid "model requires id" in
    let* repr = representation (Kanon_surface.Syntax.SVar model.model_name) in
    let instances = List.filter (fun (row : Rir.foreign) ->
      List.assoc_opt "M" row.type_arguments = Some model.model_name) instances in
    Ok { name = model.model_name; fields; repr; instances }) checked.models)

type operation = Create | Get
let operation name =
  if String.equal name "Model.create" then Ok Create
  else if String.equal name "Model.get_by_id" then Ok Get
  else refuse ("foreign schema " ^ name)
let specification = function
  | Create -> "(0 M : Type 0) -> (fields : M) -> (db : Db) -> M", [Catalog.Zero; Catalog.Many; Catalog.Many]
  | Get -> "(0 M : Type 0) -> (0 Key : Type 0) -> (key : Key) -> (db : Db) -> M",
      [Catalog.Zero; Catalog.Zero; Catalog.Many; Catalog.Many]
let foreign_call entries models (row : Rir.foreign) =
  let* op = operation row.schema in
  let* model = List.find_opt (fun model -> List.exists (fun (instance : Rir.foreign) ->
    String.equal instance.name row.name) model.instances) models
    |> Option.to_result ~none:(Error.Mismatch ("Rust emission: unknown model instance " ^ row.name)) in
  let* () = if List.mem row model.instances then Ok () else invalid ("model metadata differs: " ^ row.name) in
  let* entry = Foreign.lookup entries row.schema in
  let* () = match entry.kind with
    | Catalog.Schema -> Ok ()
    | Catalog.Constant | Catalog.Type_constant -> invalid "model schema kind" in
  let expected_type, quantities = specification op in
  let* expected = Elab.target_type expected_type in
  let* actual = Elab.target_type entry.kernel_type in
  let* () = if expected = actual && entry.quantities = quantities
      && entry.effects = ["DbExec"; "toasty::Error"] && row.effects = entry.effects
      && String.equal row.print_rule entry.print_rule && row.arity = 2
    then Ok () else invalid "model schema metadata" in
  let* native = Printer.repr model.repr in
  let native = Printer.rust_type native in
  let* template = Template.parse entry.print_rule in
  let slots = match op with Create -> ["M"; "fields"; "db"] | Get -> ["M"; "key"; "db"] in
  let* () = if List.sort_uniq String.compare (Template.slots template) = List.sort String.compare slots
    then Ok () else invalid "model schema placeholders" in
  let render arguments = match arguments with
    | [value; db] ->
      let fields = List.mapi (fun index (field, scalar) -> field_name field ^ ": "
        ^ to_storage scalar ("__lan_value.f" ^ string_of_int index)) model.fields |> String.concat ", " in
      let value_slot, value_code = match op with
        | Create -> "fields", fields
        | Get -> "key", "lan_model_to_i64(&__lan_value)?" in
      let* call = Template.render template ["M", rust_name model; value_slot, value_code; "db", "__lan_db"] in
      let result = List.mapi (fun index (field, scalar) -> "f" ^ string_of_int index
        ^ ": " ^ from_storage scalar ("__lan_row." ^ field_name field)) model.fields |> String.concat ", " in
      Ok ("{ let __lan_value = " ^ value ^ "; let __lan_db_arg = " ^ db
        ^ "; let mut __lan_db = (*__lan_db_arg).clone(); let __lan_row = " ^ call
        ^ "; " ^ native ^ " { " ^ result ^ " } }")
    | [] | _ :: _ -> invalid "model argument count" in
  let input = match op with Create -> model.repr | Get -> Rir.TyUnion (Rir.Tid "nat") in
  Ok ([Rir.TyArc input; Rir.TyArc (Rir.TyForeign ("Db", []))], model.repr, render, Effects.Async_db)

let declaration model =
  "#[derive(Debug, toasty::Model)]\nstruct " ^ rust_name model ^ " {\n"
  ^ String.concat "" (List.map (fun (field, scalar) ->
    (if String.equal field "id" then "    #[key]\n" else "")
    ^ "    " ^ field_name field ^ ": " ^ storage_type scalar ^ ",\n") model.fields) ^ "}\n"
let conversions = {|
fn lan_model_to_i64(value: &Nat) -> Result<i64, Error> {
    value.0.iter().rev().try_fold(0_i64, |number, byte| {
        number.checked_mul(256).and_then(|number| number.checked_add(i64::from(*byte)))
            .ok_or(Error::ModelRange)
    })
}
fn lan_model_from_i64(value: i64) -> Result<Nat, Error> {
    if value < 0 { Err(Error::ModelRange) }
    else { Ok(Nat::canonical(value.to_le_bytes().to_vec())) }
}
|}
let source (checked : Elab.lan_program) =
  let* models = catalog checked in
  let* rows = Lower.program checked in
  if List.is_empty models then Foreign.source rows else
  let module Target = Emit.Make (struct
    let foreign_type = Foreign.foreign_type Catalog.entries
    let foreign_layout = foreign_type
    let foreign_call row =
      if String.starts_with ~prefix:"Model." row.Rir.schema then foreign_call Catalog.entries models row
      else Foreign.foreign_call Catalog.entries row
  end) in
  let* source = Target.native ~model_errors:true rows in
  Ok (source ^ "\n" ^ String.concat "\n" (List.map declaration models) ^ conversions)
