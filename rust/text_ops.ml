(** Checked byte-list adapters for the string operations used by Todo forms. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Lower = Kanon_surface.Lower
module Catalog = Lanyard_target.Target_generated
module Printer = Foreign.Printer
let ( let* ) = Result.bind
let invalid text = Error (Error.Mismatch ("Rust emission: " ^ text))
type operation = Trim | Is_empty | Uri_from_text
let operation name = match () with
  | () when String.equal name "Text.trim" -> Ok Trim
  | () when String.equal name "Text.is_empty" -> Ok Is_empty
  | () when String.equal name "Uri.from_text" -> Ok Uri_from_text
  | () -> Error (Error.Not_yet ("Rust emission: text schema " ^ name))
let bool_tid = Rir.Tid "sum<struct tuple<>|struct tuple<>>"
let bool_repr = Rir.TyUnion bool_tid
type t = { row : Rir.foreign; operation : operation; family : string;
  repr : Rir.repr; data : Rir.tid list }
let catalog (checked : Elab.lan_program) (instances : Lower.text_operation list) =
  Rules.all_ok (List.map (fun (instance : Lower.text_operation) ->
    let* operation = operation instance.row.schema in
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
      |> Option.to_result ~none:(Error.Not_yet "Rust emission: text operation requires a byte list") in
    Ok { row = instance.row; operation; family = family.family_name; repr; data }) instances)

let specification = function
  | Trim -> "(0 Text : Type 0) -> (text : Text) -> Text"
  | Is_empty -> "(0 Text : Type 0) -> (text : Text) -> sum ((prod () : Type 0), (prod () : Type 0))"
  | Uri_from_text -> "(0 Text : Type 0) -> (text : Text) -> Uri"
let effects = function Trim | Is_empty -> [] | Uri_from_text -> ["topcoat::Error"]
let foreign_call entries operations (row : Rir.foreign) =
  let* text = List.find_opt (fun text -> text.row = row) operations
    |> Option.to_result ~none:(Error.Mismatch "Rust emission: text metadata differs") in
  let* operation = operation row.schema in
  let* () = if operation = text.operation then Ok () else invalid "text operation differs" in
  let* entry = Foreign.lookup entries row.schema in
  let* () = match entry.kind with Catalog.Schema -> Ok ()
    | Catalog.Constant | Catalog.Type_constant -> invalid "text schema kind" in
  let* expected = Elab.target_type (specification operation) in
  let* actual = Elab.target_type entry.kernel_type in
  let* () = if actual = expected && entry.quantities = [Catalog.Zero; Catalog.Many]
      && entry.effects = effects operation && row.effects = entry.effects && row.arity = 1
      && row.name = Elab.target_name entry.name && row.print_rule = entry.print_rule
    then Ok () else invalid "text schema metadata" in
  let* template = Template.parse entry.print_rule in
  let* () = if List.sort_uniq String.compare (Template.slots template) = ["text"]
    then Ok () else invalid "text schema placeholders" in
  let render = function
    | [value] ->
        let* call = Template.render template ["text", "__lan_text"] in
        let converted = match operation with
          | Trim -> Printer.identifier "lan_model_text_from_" text.family ^ "(" ^ call ^ ")"
          | Is_empty ->
              let ty = Printer.rust_type (Printer.Sum [Printer.Unit; Printer.Unit]) in
              "if " ^ call ^ " { " ^ ty ^ "::V1(()) } else { " ^ ty ^ "::V0(()) }"
          | Uri_from_text -> "lan_uri_validate(&__lan_text)?; " ^ call in
        Ok ("{ let __lan_text_arg = " ^ value ^ "; let __lan_text = "
          ^ Printer.identifier "lan_model_text_to_" text.family ^ "(&__lan_text_arg)?; " ^ converted ^ " }")
    | [] | _ :: _ -> invalid "text argument count" in
  let* result = match operation with
    | Trim -> Ok text.repr | Is_empty -> Ok bool_repr
    | Uri_from_text ->
        let* _uri_type = Foreign.foreign_type entries "Uri" [] in
        Ok (Rir.TyForeign ("Uri", [])) in
  Ok ([Rir.TyArc text.repr], result, render, Effects.Sync)

(** Match Run_http.uri before the pinned HTTP parser can accept another URI form. *)
let uri_runtime = {|
enum LanUriEscape { Ready, FirstHex, SecondHex }
fn lan_uri_validate(value: &str) -> Result<(), Error> {
    let initial = if value.len() > 8192 || !value.starts_with('/') || value.starts_with("//") {
        Err(Error::InvalidUri)
    } else { Ok(LanUriEscape::Ready) };
    initial.and_then(|initial| value.bytes().try_fold(initial, |state, byte| {
        match state {
            LanUriEscape::Ready => {
                if byte == b'%' { Ok(LanUriEscape::FirstHex) }
                else if byte.is_ascii_alphanumeric() || b"-._~!$&'()*+,;=:@/?".contains(&byte) {
                    Ok(LanUriEscape::Ready)
                } else { Err(Error::InvalidUri) }
            }
            LanUriEscape::FirstHex => {
                if byte.is_ascii_hexdigit() { Ok(LanUriEscape::SecondHex) }
                else { Err(Error::InvalidUri) }
            }
            LanUriEscape::SecondHex => {
                if byte.is_ascii_hexdigit() { Ok(LanUriEscape::Ready) }
                else { Err(Error::InvalidUri) }
            }
        }
    })).and_then(|state| match state {
        LanUriEscape::Ready => Ok(()),
        LanUriEscape::FirstHex | LanUriEscape::SecondHex => Err(Error::InvalidUri),
    })
}
|}

(* Unicode White_Space, the property used by Rust's str::trim. The checked
   decoder supplies valid scalar boundaries, including four-byte scalars. *)
let whitespace scalar = (scalar >= 0x09 && scalar <= 0x0d)
  || (scalar >= 0x2000 && scalar <= 0x200a)
  || List.mem scalar [0x20; 0x85; 0xa0; 0x1680; 0x2028; 0x2029; 0x202f; 0x205f; 0x3000]
let trim text =
  if not (String.is_valid_utf_8 text) then Error (Error.Mismatch "invalid UTF-8 in text operation") else
  let rec scan offset bounds =
    if offset = String.length text then
      Ok (Option.fold ~none:"" ~some:(fun (first, last) ->
        String.to_seq text |> Seq.drop first |> Seq.take (last - first) |> String.of_seq) bounds)
    else
      let decoded = String.get_utf_8_uchar text offset in
      let next = offset + Uchar.utf_decode_length decoded in
      let bounds = if whitespace (Uchar.to_int (Uchar.utf_decode_uchar decoded)) then bounds
        else Some (Option.fold ~none:offset ~some:fst bounds, next) in
      scan next bounds in
  scan 0 None
