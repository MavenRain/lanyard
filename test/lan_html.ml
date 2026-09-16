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
let contains text needle = String.to_seq text |> Seq.mapi (fun index _character -> index)
  |> Seq.exists (fun index -> String.starts_with ~prefix:needle
       (String.to_seq text |> Seq.drop index |> String.of_seq))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected HTML result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let result_type schema = if String.equal schema "Html.text" then "Bytes" else "Response"
let checked schema = E.check_lanyard (base ^ "def main : Bytes -> " ^ result_type schema ^ " := " ^ schema ^ " Bytes")
let call schema value =
  let* checked = checked schema in let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value]
  |> Result.map fst
let escape value = let* value = call "Html.text" (V.of_text "Bytes" value) in
  V.text ~what:"HTML" "Bytes" value
let render value = let* value = call "Response.html" (V.of_text "Bytes" value) in H.response value
let wire body = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: "
  ^ string_of_int (String.length body) ^ "\r\n\r\n" ^ body
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* value, _text = I.run checked in H.response value
let metadata schema change_row change_entry =
  let* checked = checked schema in let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = schema) operations
    |> Option.to_result ~none:(Error.Unbound schema) in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = schema then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let malformed = V.Tag (Erase.mu_tid "Bytes", 1, [V.Nat (Bignum.of_int 256); V.of_text "Bytes" ""])
let cases = [
  "escape delimiters", equal "&lt;a&gt;&amp;&lt;/a&gt;" (escape "<a>&</a>");
  "escape existing entities", equal "&amp;lt;&amp;amp;" (escape "&lt;&amp;");
  "escape quotes retained", equal "\"'\096=/" (escape "\"'\096=/");
  "escape empty", equal "" (escape "");
  "escape Unicode", equal "caf\195\169 \230\151\165\240\159\152\128" (escape "caf\195\169 \230\151\165\240\159\152\128");
  "escape controls", equal "\000\r\n" (escape "\000\r\n");
  "escape public UTF-8 guard", refuses "UTF-8" (T.html_text "\255");
  "html raw markup", equal (wire "<h1>hello</h1>") (render "<h1>hello</h1>");
  "html empty body", equal (wire "") (render "");
  "html byte length", equal (wire "caf\195\169") (render "caf\195\169");
  "html body controls", equal (wire "\000\r\n\r\nX-Header:yes") (render "\000\r\n\r\nX-Header:yes");
  "html runtime UTF-8 guard", refuses "UTF-8" (H.response (V.Response_html "\255"));
  "composed escaping", equal (wire "&lt;script&gt;&amp;&lt;/script&gt;")
    (evaluate "def main : Response := Response.html Bytes (Html.text Bytes b\"<script>&</script>\")");
  "captured helper", equal (wire "&lt;title&gt;")
    (evaluate ("def main : Response := let title : Bytes := b\"<title>\" in "
     ^ "let escaped : prod () -> Bytes := fun (u : prod ()) => Html.text Bytes title in Response.html Bytes (escaped ())"));
  "text response retained", equal "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 3\r\n\r\n<b>"
    (evaluate "def main : Response := Response.text Bytes b\"<b>\"");
  "unused escape fails", refuses "UTF-8" (evaluate
    "def main : Response := let ignored : Bytes := Html.text Bytes (bytesCons 255 bytesNil) in Response.html Bytes b\"ok\"");
  "unused response fails", refuses "UTF-8" (evaluate
    "def main : Response := let ignored : Response := Response.html Bytes (bytesCons 255 bytesNil) in Response.html Bytes b\"ok\"");
] @ List.concat_map (fun schema -> [
  schema ^ " byte range", refuses "0..255" (call schema malformed);
  schema ^ " malformed UTF-8", refuses "UTF-8" (call schema (V.of_text "Bytes" "\255"));
  schema ^ " truncated UTF-8", refuses "UTF-8" (call schema (V.of_text "Bytes" "\226\130"));
  schema ^ " wrong family", refuses "byte list" (call schema (V.of_text "Other" "hello"));
  schema ^ " unsupported layout", refuses "byte list"
    (let* checked = E.check_lanyard ("def main : "
      ^ (if String.equal schema "Html.text" then "Nat" else "Response")
      ^ " := " ^ schema ^ " Nat 1") in I.run checked);
  schema ^ " open type", refuses "closed"
    (let* checked = E.check_lanyard ("def main : (0 A : Type 0) -> A -> "
      ^ (if String.equal schema "Html.text" then "A" else "Response")
      ^ " := fun (0 A : Type 0) (text : A) => " ^ schema ^ " A text") in I.prepare checked);
  schema ^ " metadata effects", refuses "metadata" (metadata schema Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
  schema ^ " metadata arity", refuses "metadata" (metadata schema (fun row -> { row with arity = 2 }) Fun.id);
  schema ^ " metadata quantities", refuses "metadata" (metadata schema Fun.id (fun row -> { row with quantities = [C.Zero; C.One] }));
  schema ^ " metadata kind", refuses "kind" (metadata schema Fun.id (fun row -> { row with kind = C.Constant }));
  schema ^ " metadata type", refuses "metadata" (metadata schema Fun.id (fun row -> { row with kernel_type = T.specification T.Is_empty }));
  schema ^ " metadata type argument", refuses "metadata" (metadata schema (fun row -> { row with type_arguments = [] }) Fun.id);
  schema ^ " metadata print rule", refuses "metadata" (metadata schema Fun.id (fun row -> { row with print_rule = "#{other}" }));
]) ["Html.text"; "Response.html"]
let () =
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-HTML OK checks=%d\n" (List.length cases) else exit 1
