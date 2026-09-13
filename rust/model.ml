(** Model fields store Nat, two-unit sums and checked byte lists as database scalars.
    Checked model instances select schemas; only the key field id keeps its source name. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Lower = Kanon_surface.Lower
module Catalog = Lanyard_target.Target_generated
module Printer = Foreign.Printer
let ( let* ) = Result.bind
let invalid text = Error (Error.Mismatch ("Rust emission: " ^ text))
let refuse text = Error (Error.Not_yet ("Rust emission: " ^ text))
type scalar = Nat_field | Bool_field | Text_field of string
type t = { name : string; fields : (string * scalar) list; repr : Rir.repr;
  data : Rir.tid list; instances : Rir.foreign list }
let bool_repr = Rir.TyUnion (Rir.Tid "sum<struct tuple<>|struct tuple<>>")
let bool_type = Printer.rust_type (Printer.Sum [Printer.Unit; Printer.Unit])
let storage_type = function Nat_field -> "i64" | Bool_field -> "bool" | Text_field _ -> "String"
let text_to name = Printer.identifier "lan_model_text_to_" name
let text_from name = Printer.identifier "lan_model_text_from_" name
let to_storage scalar value = match scalar with
  | Nat_field -> "lan_model_to_i64(&" ^ value ^ ")?"
  | Bool_field -> "match &" ^ value ^ " { " ^ bool_type ^ "::V0(()) => false, "
      ^ bool_type ^ "::V1(()) => true }"
  | Text_field name -> text_to name ^ "(&" ^ value ^ ")?"
let from_storage scalar value = match scalar with
  | Nat_field -> "lan_model_from_i64(" ^ value ^ ")?"
  | Bool_field -> "if " ^ value ^ " { " ^ bool_type ^ "::V1(()) } else { " ^ bool_type ^ "::V0(()) }"
  | Text_field name -> text_from name ^ "(" ^ value ^ ")"
let rust_name model = Printer.identifier "LanModel" model.name
let field_name name = if String.equal name "id" then "id" else Printer.identifier "f_" name
let catalog (checked : Elab.lan_program) =
  if List.is_empty checked.models then Ok [] else
  let* instances = Lower.catalog checked in
  Rules.all_ok (List.map (fun (model : Elab.model_info) ->
    let ec : Erase.ectx = { c = Check.make checked.globals Budget.unlimited;
      slots = []; self = model.model_name } in
    let evaluate syntax =
      let* term = Elab.elab ec.c ~expected:None syntax in
      Eval.eval checked.globals [] term in
    let* ty = evaluate (Kanon_surface.Syntax.SVar model.model_name) in
    let* repr = Erase.repr_of ec ty in
    let* tid = Erase.tid_of ec ty in
    let* data = Erase.complete_groups ec [tid] in
    let* families = Printer.family_catalog [model.model_name, Erase.Code [Rir.RData data]] in
    let* fields = Rules.all_ok (List.map (fun (field, syntax) ->
      let* ty = evaluate syntax in
      let* repr = Erase.repr_of ec ty in
      let is_key = String.equal field "id" in
      let text_family = List.find_opt (fun (family : Printer.family) ->
        repr = Rir.TyUnion (Erase.mu_tid family.family_name)
        && family.variants = [[]; [Printer.Nat; Printer.Nominal family.family_name]]) families in
      match () with
      | () when repr = Rir.TyUnion (Rir.Tid "nat") -> Ok (field, Nat_field)
      | () when is_key -> refuse ("model field " ^ model.model_name ^ "." ^ field ^ " requires Nat")
      | () when repr = bool_repr -> Ok (field, Bool_field)
      | () -> Option.fold
          ~none:(refuse ("model field " ^ model.model_name ^ "." ^ field
            ^ " requires Nat or Bool (a two-unit sum) or a byte list"))
          ~some:(fun (family : Printer.family) -> Ok (field, Text_field family.family_name))
          text_family) model.fields) in
    let* () = if List.mem_assoc "id" model.fields then Ok () else invalid "model requires id" in
    let instances = List.filter (fun (row : Rir.foreign) ->
      List.assoc_opt "M" row.type_arguments = Some model.model_name) instances in
    Ok { name = model.model_name; fields; repr; data; instances }) checked.models)

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
let text_conversions name =
  let ty = Printer.rust_type (Printer.Nominal name) in
  Printf.sprintf {|
fn %s(value: &%s) -> Result<String, Error> {
    std::iter::successors(Some(value), |node| match node {
        %s::V0 => None,
        %s::V1(fields) => Some(&fields.1),
    }).filter_map(|node| match node {
        %s::V0 => None,
        %s::V1(fields) => Some(match fields.0.0.as_slice() {
            [] => Ok(0),
            [byte] => Ok(*byte),
            [_, _, ..] => Err(Error::ModelByteRange),
        }),
    }).collect::<Result<Vec<u8>, Error>>()
        .and_then(|bytes| String::from_utf8(bytes).map_err(|_error| Error::ModelUtf8))
}
fn %s(value: String) -> %s {
    value.bytes().rev().fold(%s::V0, |tail, byte| {
        %s::V1(Box::new((Nat::canonical(vec![byte]), tail)))
    })
}
|} (text_to name) ty ty ty ty ty (text_from name) ty ty ty
type output = Discard | Print_model of string
let output_errors = {|
#[derive(Debug)]
enum LanMainError { Program(Error), Output(std::io::Error) }
impl std::fmt::Display for LanMainError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Program(error) => std::fmt::Display::fmt(error, f),
            Self::Output(error) => std::fmt::Display::fmt(error, f),
        }
    }
}
impl std::error::Error for LanMainError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Program(error) => Some(error),
            Self::Output(error) => Some(error),
        }
    }
}
impl From<Error> for LanMainError {
    fn from(error: Error) -> Self { Self::Program(error) }
}
|}
let output_source model =
  let* native = Printer.repr model.repr in
  let format = model.name ^ " {{ " ^ String.concat ", " (List.map (fun (field, scalar) ->
    field ^ ": " ^ (match scalar with Nat_field | Bool_field -> "{}" | Text_field _ -> "{:?}")) model.fields) ^ " }}\\n" in
  let arguments = List.mapi (fun index (_field, scalar) ->
    to_storage scalar ("value.f" ^ string_of_int index)) model.fields in
  let name = Printer.identifier "lan_print_model_" model.name in
  Ok (Emit.Print_model (model.repr, name), output_errors ^ "\nfn " ^ name
    ^ "(value: &" ^ Printer.rust_type native ^ ") -> Result<(), LanMainError> {\n"
    ^ "    let line = format!(\"" ^ format ^ "\", " ^ String.concat ", " arguments ^ ");\n"
    ^ "    std::io::Write::write_all(&mut std::io::stdout().lock(), line.as_bytes()).map_err(LanMainError::Output)\n}\n")
let source ?entrypoint ?(output = Discard) (checked : Elab.lan_program) =
  let* specialized = Lower.specialize checked in
  let checked = specialized.Lower.specialized in
  let* models = catalog checked in
  let* entry_output, output_code = match output with
    | Discard -> Ok (Emit.Discard, "")
    | Print_model name ->
        let* () = if Option.is_some entrypoint then Ok () else invalid "model output requires a crate entry point" in
        let* model = List.find_opt (fun model -> String.equal name model.name) models
          |> Option.to_result ~none:(Error.Mismatch ("Rust emission: printed model is unknown or not reachable: " ^ name)) in
        output_source model in
  let* instances = Lower.connections specialized in
  let* connections = Connection.catalog checked (List.map (fun model -> model.name, rust_name model) models) instances in
  let* rows = Lower.program_with instances specialized in
  if List.is_empty models && List.is_empty connections then Foreign.source ?entrypoint rows else
  let module Target = Emit.Make (struct
    let foreign_type = Foreign.foreign_type Catalog.entries
    let foreign_layout = foreign_type
    let foreign_call row =
      if String.starts_with ~prefix:"Model." row.Rir.schema then foreign_call Catalog.entries models row
      else if String.equal row.Rir.schema "Db.connect" then Connection.foreign_call Catalog.entries connections row
      else Foreign.foreign_call Catalog.entries row
  end) in
  let data = List.concat_map (fun model -> model.data) models
    @ List.concat_map (fun (connection : Connection.t) -> connection.data) connections in
  let text = List.concat_map (fun model -> List.filter_map (fun (_field, scalar) ->
    match scalar with Nat_field | Bool_field -> None | Text_field name -> Some name) model.fields) models
    @ List.map (fun (connection : Connection.t) -> connection.family) connections
    |> List.sort_uniq String.compare in
  let* source = Target.native ?entrypoint ~entry_output ~model_errors:true ~text_errors:(text <> [])
    (("", Erase.Code [Rir.RData data]) :: rows) in
  Ok (source ^ "\n" ^ String.concat "\n" (List.map declaration models) ^ conversions
    ^ (List.map text_conversions text |> String.concat "") ^ output_code)
