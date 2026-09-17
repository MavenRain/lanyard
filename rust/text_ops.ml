(** Checked byte-list adapters for the string operations used by Todo forms. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Lower = Kanon_surface.Lower
module Catalog = Lanyard_target.Target_generated
module Printer = Foreign.Printer
let ( let* ) = Result.bind
let invalid text = Error (Error.Mismatch ("Rust emission: " ^ text))
type operation = Trim | Is_empty | Concat | Uri_from_text | Form_field | Response_text | Html_text | Response_html
let operation name = match () with
  | () when String.equal name "Text.trim" -> Ok Trim
  | () when String.equal name "Text.is_empty" -> Ok Is_empty
  | () when String.equal name "Text.concat" -> Ok Concat
  | () when String.equal name "Uri.from_text" -> Ok Uri_from_text
  | () when String.equal name "Form.field" -> Ok Form_field
  | () when String.equal name "Response.text" -> Ok Response_text
  | () when String.equal name "Html.text" -> Ok Html_text
  | () when String.equal name "Response.html" -> Ok Response_html
  | () -> Error (Error.Not_yet ("Rust emission: text schema " ^ name))
let bool_tid = Rir.Tid "sum<struct tuple<>|struct tuple<>>"
let bool_repr = Rir.TyUnion bool_tid
type t = { row : Rir.foreign; operation : operation; family : string;
  repr : Rir.repr; data : Rir.tid list }
let byte_family repr families =
  List.find_opt (fun (family : Printer.family) ->
    (repr = Rir.TyUnion (Erase.mu_tid family.family_name)
     || repr = Rir.TyArc (Rir.TyUnion (Erase.mu_tid family.family_name)))
    && family.variants = [[]; [Printer.Nat; Printer.Nominal family.family_name]]) families
  |> Option.to_result ~none:(Error.Not_yet "Rust emission: text operation requires a byte list")
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
    let* family = byte_family repr families in
    Ok { row = instance.row; operation; family = family.family_name; repr; data }) instances)

let specification = function
  | Trim | Html_text -> "(0 Text : Type 0) -> (text : Text) -> Text"
  | Concat -> "(0 Text : Type 0) -> (left : Text) -> (right : Text) -> Text"
  | Is_empty -> "(0 Text : Type 0) -> (text : Text) -> sum ((prod () : Type 0), (prod () : Type 0))"
  | Uri_from_text -> "(0 Text : Type 0) -> (text : Text) -> Uri"
  | Form_field -> "(0 Text : Type 0) -> (text : Text) -> (field : Text) -> Text"
  | Response_text | Response_html -> "(0 Text : Type 0) -> (text : Text) -> Response"
let effects = function Trim | Is_empty | Concat | Response_text | Html_text | Response_html -> []
  | Uri_from_text | Form_field -> ["topcoat::Error"]
let parameters = function Trim | Is_empty | Uri_from_text | Response_text | Html_text | Response_html -> ["text"]
  | Concat -> ["left"; "right"]
  | Form_field -> ["text"; "field"]
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
  let parameters = parameters operation in
  let* () = if actual = expected && entry.quantities = Catalog.Zero :: List.map (fun _name -> Catalog.Many) parameters
      && entry.effects = effects operation && row.effects = entry.effects && row.arity = List.length parameters
      && row.name = Elab.target_name entry.name && row.print_rule = entry.print_rule
    then Ok () else invalid "text schema metadata" in
  let* template = Template.parse entry.print_rule in
  let* () = if List.sort_uniq String.compare (Template.slots template) = List.sort String.compare parameters
    then Ok () else invalid "text schema placeholders" in
  let render arguments =
    if List.length arguments <> List.length parameters then invalid "text argument count" else
        let bindings = List.map (fun name -> name, "__lan_" ^ name) parameters in
        let* call = Template.render template bindings in
        let converted = match operation with
          | Trim | Concat | Form_field | Html_text -> Printer.identifier "lan_model_text_from_" text.family ^ "(" ^ call ^ ")"
          | Is_empty ->
              let ty = Printer.rust_type (Printer.Sum [Printer.Unit; Printer.Unit]) in
              "if " ^ call ^ " { " ^ ty ^ "::V1(()) } else { " ^ ty ^ "::V0(()) }"
          | Uri_from_text -> "lan_uri_validate(&__lan_text)?; " ^ call
          | Response_text | Response_html -> call in
        let evaluated = Seq.zip (List.to_seq bindings) (List.to_seq arguments)
          |> Seq.map (fun ((_name, local), value) -> "let " ^ local ^ "_arg = " ^ value ^ "; ")
          |> List.of_seq |> String.concat "" in
        let conversions = List.map (fun (_name, local) -> "let " ^ local ^ " = "
          ^ Printer.identifier "lan_model_text_to_" text.family ^ "(&" ^ local ^ "_arg)?; ") bindings
          |> String.concat "" in
        Ok ("{ " ^ evaluated ^ conversions ^ converted ^ " }") in
  let* result = match operation with
    | Trim | Concat | Form_field | Html_text -> Ok text.repr | Is_empty -> Ok bool_repr
    | Uri_from_text ->
        let* _uri_type = Foreign.foreign_type entries "Uri" [] in
        Ok (Rir.TyForeign ("Uri", []))
    | Response_text | Response_html ->
        let* _response_type = Foreign.foreign_type entries "Response" [] in
        Ok (Rir.TyForeign ("Response", [])) in
  Ok (List.map (fun _name -> Rir.TyArc text.repr) parameters, result, render, Effects.Sync)

(** Topcoat's TEXT_ESCAPES table applies only to HTML text nodes. *)
let html_text text =
  if not (String.is_valid_utf_8 text) then Error (Error.Mismatch "invalid UTF-8 in HTML text") else
  Ok (String.to_seq text |> Seq.map (fun character -> match () with
    | () when Char.equal character '&' -> "&amp;"
    | () when Char.equal character '<' -> "&lt;"
    | () when Char.equal character '>' -> "&gt;"
    | () -> String.make 1 character) |> List.of_seq |> String.concat "")

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
