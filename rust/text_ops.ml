(** Checked byte-list adapters for the string operations used by Todo forms. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Lower = Kanon_surface.Lower
module Catalog = Lanyard_target.Target_generated
module Printer = Foreign.Printer
let ( let* ) = Result.bind
let invalid text = Error (Error.Mismatch ("Rust emission: " ^ text))
type operation = Trim | Is_empty | Equal | Contains | Starts_with | Ends_with | Replace | Length | Concat | From_nat | To_nat | Uri_from_text | Uri_to_text | Uri_path | Uri_query | Form_field | Form_has | Response_text | Html_text | Response_html
let operation name = match () with
  | () when String.equal name "Text.trim" -> Ok Trim
  | () when String.equal name "Text.is_empty" -> Ok Is_empty
  | () when String.equal name "Text.equal" -> Ok Equal
  | () when String.equal name "Text.contains" -> Ok Contains
  | () when String.equal name "Text.starts_with" -> Ok Starts_with
  | () when String.equal name "Text.ends_with" -> Ok Ends_with
  | () when String.equal name "Text.replace" -> Ok Replace
  | () when String.equal name "Text.length" -> Ok Length
  | () when String.equal name "Text.concat" -> Ok Concat
  | () when String.equal name "Text.from_nat" -> Ok From_nat
  | () when String.equal name "Text.to_nat" -> Ok To_nat
  | () when String.equal name "Uri.from_text" -> Ok Uri_from_text
  | () when String.equal name "Uri.to_text" -> Ok Uri_to_text
  | () when String.equal name "Uri.path" -> Ok Uri_path
  | () when String.equal name "Uri.query" -> Ok Uri_query
  | () when String.equal name "Form.field" -> Ok Form_field
  | () when String.equal name "Form.has" -> Ok Form_has
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
  | Replace -> "(0 Text : Type 0) -> (text : Text) -> (needle : Text) -> (replacement : Text) -> Text"
  | From_nat -> "(0 Text : Type 0) -> (value : Nat) -> Text"
  | Length | To_nat -> "(0 Text : Type 0) -> (text : Text) -> Nat"
  | Is_empty -> "(0 Text : Type 0) -> (text : Text) -> sum ((prod () : Type 0), (prod () : Type 0))"
  | Equal -> "(0 Text : Type 0) -> (left : Text) -> (right : Text) -> sum ((prod () : Type 0), (prod () : Type 0))"
  | Contains | Starts_with | Ends_with -> "(0 Text : Type 0) -> (text : Text) -> (needle : Text) -> sum ((prod () : Type 0), (prod () : Type 0))"
  | Uri_from_text -> "(0 Text : Type 0) -> (text : Text) -> Uri"
  | Uri_to_text | Uri_path | Uri_query -> "(0 Text : Type 0) -> (uri : Uri) -> Text"
  | Form_field -> "(0 Text : Type 0) -> (text : Text) -> (field : Text) -> Text"
  | Form_has -> "(0 Text : Type 0) -> (text : Text) -> (field : Text) -> sum ((prod () : Type 0), (prod () : Type 0))"
  | Response_text | Response_html -> "(0 Text : Type 0) -> (text : Text) -> Response"
let effects = function Trim | Is_empty | Equal | Contains | Starts_with | Ends_with | Replace | Length | Concat | From_nat | Uri_to_text | Uri_path | Uri_query | Response_text | Html_text | Response_html -> []
  | To_nat | Uri_from_text | Form_field | Form_has -> ["topcoat::Error"]
let parameters = function Trim | Is_empty | Length | To_nat | Uri_from_text | Response_text | Html_text | Response_html -> ["text"]
  | Equal | Concat -> ["left"; "right"]
  | Contains | Starts_with | Ends_with -> ["text"; "needle"]
  | Replace -> ["text"; "needle"; "replacement"]
  | From_nat -> ["value"]
  | Uri_to_text | Uri_path | Uri_query -> ["uri"]
  | Form_field | Form_has -> ["text"; "field"]
type input = Byte_list | Natural | Request_uri
let input = function
  | From_nat -> Natural
  | Uri_to_text | Uri_path | Uri_query -> Request_uri
  | Trim | Is_empty | Equal | Contains | Starts_with | Ends_with | Replace | Length | Concat | To_nat | Uri_from_text | Form_field | Form_has | Response_text | Html_text | Response_html -> Byte_list
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
          | Trim | Concat | Replace | From_nat | Form_field | Html_text -> Printer.identifier "lan_model_text_from_" text.family ^ "(" ^ call ^ ")"
          | Is_empty | Equal | Contains | Starts_with | Ends_with | Form_has ->
              let ty = Printer.rust_type (Printer.Sum [Printer.Unit; Printer.Unit]) in
              "if " ^ call ^ " { " ^ ty ^ "::V1(()) } else { " ^ ty ^ "::V0(()) }"
          | Uri_from_text -> "lan_uri_validate(&__lan_text)?; " ^ call
          | Uri_to_text | Uri_path | Uri_query ->
              let full = if operation = Uri_to_text then call else "__lan_uri.to_string()" in
              let part = if operation = Uri_to_text then "__lan_uri_text" else call in
              "let __lan_uri_text = " ^ full ^ "; lan_uri_validate(&__lan_uri_text)?; "
              ^ Printer.identifier "lan_model_text_from_" text.family ^ "(" ^ part ^ ")"
          | Length | To_nat | Response_text | Response_html -> call in
        let evaluated = Seq.zip (List.to_seq bindings) (List.to_seq arguments)
          |> Seq.map (fun ((_name, local), value) -> "let " ^ local ^ "_arg = " ^ value ^ "; ")
          |> List.of_seq |> String.concat "" in
        let conversions = List.map (fun (_name, local) -> "let " ^ local ^ " = "
          ^ (match input operation with
             | Byte_list -> Printer.identifier "lan_model_text_to_" text.family ^ "(&" ^ local ^ "_arg)?"
             | Natural | Request_uri -> local ^ "_arg") ^ "; ") bindings
          |> String.concat "" in
        Ok ("{ " ^ evaluated ^ conversions ^ converted ^ " }") in
  let uri_foreign () = let* _uri_type = Foreign.foreign_type entries "Uri" [] in
    Ok (Rir.TyForeign ("Uri", [])) in
  let* result = match operation with
    | Trim | Concat | Replace | From_nat | Uri_to_text | Uri_path | Uri_query | Form_field | Html_text -> Ok text.repr | Is_empty | Equal | Contains | Starts_with | Ends_with | Form_has -> Ok bool_repr
    | Length | To_nat -> Ok (Rir.TyUnion (Rir.Tid "nat"))
    | Uri_from_text -> uri_foreign ()
    | Response_text | Response_html ->
        let* _response_type = Foreign.foreign_type entries "Response" [] in
        Ok (Rir.TyForeign ("Response", [])) in
  let* argument = match input operation with
    | Byte_list -> Ok text.repr | Natural -> Ok (Rir.TyUnion (Rir.Tid "nat"))
    | Request_uri -> uri_foreign () in
  Ok (List.map (fun _name -> Rir.TyArc argument) parameters, result, render, Effects.Sync)

(** Project a validated origin-form URI without decoding or normalizing bytes. *)
let uri_text operation uri =
  let before_query character = not (Char.equal character '?') in
  match operation with
  | Uri_to_text -> Ok uri
  | Uri_path -> Ok (String.to_seq uri |> Seq.take_while before_query |> String.of_seq)
  | Uri_query -> Ok (String.to_seq uri |> Seq.drop_while before_query |> Seq.drop 1 |> String.of_seq)
  | Trim | Is_empty | Equal | Contains | Starts_with | Ends_with | Replace | Length | Concat | From_nat | To_nat | Uri_from_text
  | Form_field | Form_has | Response_text | Html_text | Response_html -> invalid "expected a URI text operation"

module Text_positions = Map.Make (Int)

(** Prefix fallback avoids rescanning repetitive text. Total map lookups keep
    the table immutable, with logarithmic lookup cost per search transition. *)
let rec advance table matched character =
      Text_positions.find_opt matched table |> Option.fold ~none:0
        ~some:(fun (expected, fallback) ->
          match () with
          | () when Char.equal expected character -> matched + 1
          | () when matched = 0 -> 0
          | () -> advance table fallback character)
let search_table needle =
    let table, _, _ = String.fold_left (fun (table, index, matched) character ->
      let next = if index = 0 then 0 else advance table matched character in
      Text_positions.add index (character, matched) table, index + 1, next)
      (Text_positions.empty, 0, 0) needle in table
let contains text needle =
  let size = String.length needle in
  match () with
  | () when size = 0 -> true
  | () when size > String.length text -> false
  | () ->
    let table = search_table needle in
    let rec search matched remaining = match remaining () with
      | Seq.Nil -> false
      | Seq.Cons (character, rest) ->
          let matched = advance table matched character in
          matched = size || search matched rest in
    search 0 (String.to_seq text)

(** Inputs are validated UTF-8. Empty needles match scalar boundaries;
    nonempty matches consume their full span before the next search. *)
let replace text needle replacement =
  let size = String.length needle in
  if size = 0 then
    let bytes = String.to_seq text |> Seq.flat_map (fun character ->
      if Char.code character land 0xc0 = 0x80 then Seq.return character
      else Seq.append (String.to_seq replacement) (Seq.return character)) in
    Seq.append bytes (String.to_seq replacement) |> String.of_seq
  else
    let table = search_table needle in
    let rec search index start matched pieces segment remaining = match remaining () with
      | Seq.Nil -> String.of_seq segment :: pieces |> List.rev |> String.concat ""
      | Seq.Cons (character, rest) ->
          let matched = advance table matched character in
          let next = index + 1 in
          if matched = size then
            let prefix = segment |> Seq.take (next - size - start) |> String.of_seq in
            search next next 0 (replacement :: prefix :: pieces) rest rest
          else search next start matched pieces segment rest in
    let bytes = String.to_seq text in search 0 0 0 [] bytes bytes

(** Decimal parsing shares the kernel's checked arbitrary-precision boundary. *)
let to_nat text = Bignum.of_decimal text
  |> Option.to_result ~none:(Error.Mismatch "invalid decimal natural text")

(** Nat.decimal already checks ASCII digits and accumulates arbitrary-size limbs.
    Its literal decoder accepts empty input, which text parsing must reject. *)
let parse_nat_runtime = {|
fn lan_text_to_nat(text: &str) -> Result<Nat, Error> {
    if text.is_empty() { Err(Error::Digit) } else { Nat::decimal(text) }
}
|}

(** Convert the Nat runtime's little-endian base-256 limbs without narrowing.
    Decimal digits stay in 0..9, so each multiply-and-carry fits in u16. *)
let nat_runtime = {|
struct LanDecimalDigits(Vec<u16>);
impl LanDecimalDigits {
    fn include_byte(self, byte: u8) -> Self {
        let (mut digits, carry) = self.0.into_iter().fold(
            (Vec::new(), u16::from(byte)), |(mut digits, carry), digit| {
                let next = digit * 256 + carry;
                digits.push(next % 10);
                (digits, next / 10)
            });
        digits.extend(std::iter::successors(Some(carry), |rest| Some(rest / 10))
            .take_while(|rest| *rest != 0)
            .map(|rest| rest % 10));
        Self(digits)
    }
    fn into_text(self) -> String {
        self.0.into_iter().rev().map(|digit| digit.to_string()).collect()
    }
}
fn lan_text_from_nat(value: &Nat) -> String {
    value.0.iter().rev().fold(LanDecimalDigits(vec![0]), |digits, byte| digits.include_byte(*byte))
        .into_text()
}
|}

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
