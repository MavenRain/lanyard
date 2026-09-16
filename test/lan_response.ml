open Kanon_kernel
module E = Kanon_surface.Elab
module L = Kanon_surface.Lower
module T = Lanyard_rust.Text_ops
module I = Lanyard_rust.Interp
module V = Lanyard_rust.Run_value
module H = Lanyard_rust.Run_http
module S = Lanyard_rust.Run_store
module C = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let base = "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
let fail message = Error (Error.Mismatch message)
let contains text needle = String.to_seq text |> List.of_seq |> List.to_seq
  |> Seq.mapi (fun index _character -> index) |> Seq.exists (fun index ->
    String.starts_with ~prefix:needle
      (String.to_seq text |> Seq.drop index |> String.of_seq))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected response"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked = E.check_lanyard (base ^ "def main : Bytes -> Response := Response.text Bytes")
let call value =
  let* checked = checked in let* context = I.prepare checked in
  let* value, _state = I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value] in
  H.response value
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* value, _text = I.run checked in H.response value
let request ?form ?steps source =
  let* checked = E.check_lanyard (base ^ source) in
  I.request ?form ?steps ~uri:"/message" checked |> Result.map snd
let handler = "def main : Cx -> Uri -> Response := fun (cx : Cx) (uri : Uri) => Response.text Bytes b\"hello\""
let form_handler = "def main : Cx -> Uri -> Bytes -> Response := fun (cx : Cx) (uri : Uri) (body : Bytes) => "
  ^ "Response.text Bytes (Text.trim Bytes (Form.field Bytes body b\"title\"))"
let hello = "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 5\r\n\r\nhello"
let metadata change_row change_entry =
  let* checked = checked in let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Response.text") operations
    |> Option.to_result ~none:(Error.Unbound "Response.text") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Response.text" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let cases = [
  "direct call", equal hello (evaluate "def main : Response := Response.text Bytes b\"hello\"");
  "alias", equal hello (call (V.of_text "Bytes" "hello"));
  "empty body", equal "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 0\r\n\r\n" (call (V.of_text "Bytes" ""));
  "UTF-8 byte length", equal "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 5\r\n\r\ncaf\195\169" (call (V.of_text "Bytes" "caf\195\169"));
  "body controls", equal "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 6\r\n\r\n\000\r\n\r\nX" (call (V.of_text "Bytes" "\000\r\n\r\nX"));
  "captured call", equal hello (evaluate ("def main : Response := let text : Bytes := b\"hello\" in "
    ^ "let render : prod () -> Response := fun (u : prod ()) => Response.text Bytes text in render ()"));
  "shared response", equal hello (evaluate ("def main : Response := let value : Response := Response.text Bytes b\"hello\" in "
    ^ "let ignored : Response := value in value"));
  "scripted request", equal hello (request handler);
  "form request", equal hello (request ~form:"title=++hello++" form_handler);
  "request budget", refuses "step limit" (request ~steps:1 handler);
  "form requires body", refuses "entry point" (request form_handler);
  "form missing field", refuses "missing" (request ~form:"other=x" form_handler);
  "form malformed unused field", refuses "escape" (request ~form:"title=hello&other=%" form_handler);
  "form extra body", refuses "entry point" (request ~form:"" handler);
  "request result type", refuses "entry point" (request "def main : Cx -> Uri -> Nat := fun (cx : Cx) (uri : Uri) => 1");
  "byte range", refuses "0..255" (call (V.Tag (Erase.mu_tid "Bytes", 1, [V.Nat (Bignum.of_int 256); V.of_text "Bytes" ""])));
  "UTF-8 refused", refuses "UTF-8" (call (V.of_text "Bytes" "\255"));
  "truncated UTF-8", refuses "UTF-8" (call (V.of_text "Bytes" "\226\130"));
  "wrong family", refuses "byte list" (call (V.of_text "Other" "hello"));
  "unused error", refuses "UTF-8" (evaluate "def main : Response := let ignored : Response := Response.text Bytes (bytesCons 255 bytesNil) in Response.text Bytes b\"hello\"");
  "unsupported layout", refuses "byte list" (let* checked = E.check_lanyard "def main : Response := Response.text Nat 1" in I.run checked);
  "open type", refuses "closed" (let* checked = E.check_lanyard "def main : (0 A : Type 0) -> A -> Response := fun (0 A : Type 0) (text : A) => Response.text A text" in I.prepare checked);
  "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
  "metadata arity", refuses "metadata" (metadata (fun row -> { row with arity = 2 }) Fun.id);
  "metadata quantities", refuses "metadata" (metadata Fun.id (fun row -> { row with quantities = [C.Zero; C.One] }));
  "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant }));
  "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = T.specification T.Trim }));
  "metadata type argument", refuses "metadata" (metadata (fun row -> { row with type_arguments = [] }) Fun.id);
  "metadata print rule", refuses "metadata" (metadata Fun.id (fun row -> { row with print_rule = "#{other}" }));
  "invalid runtime response", refuses "UTF-8" (H.response (V.Response_text "\255"));
  "wrong runtime response", refuses "SeeOther or Response" (H.response V.Unit);
  "redirect retained", equal "HTTP/1.1 303 See Other\r\nLocation: /next\r\nContent-Length: 0\r\n\r\n" (H.response (V.See_other "/next"));
]
let () =
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-RESPONSE OK checks=%d\n" (List.length cases) else exit 1
