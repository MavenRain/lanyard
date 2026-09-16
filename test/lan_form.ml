open Kanon_kernel
module E = Kanon_surface.Elab
module L = Kanon_surface.Lower
module T = Lanyard_rust.Text_ops
module I = Lanyard_rust.Interp
module V = Lanyard_rust.Run_value
module S = Lanyard_rust.Run_store
module C = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let base = "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
let fail message = Error (Error.Mismatch message)
let contains text needle =
  Seq.init (max 0 (String.length text - String.length needle + 1)) Fun.id
  |> Seq.exists (fun index -> String.equal needle
    (String.to_seq text |> Seq.drop index |> Seq.take (String.length needle) |> String.of_seq))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected form result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked = E.check_lanyard (base ^ "def main : Bytes -> Bytes -> Bytes := Form.field Bytes")
let call body name =
  let* checked = checked in let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [body; name]
  |> Fun.flip Result.bind (fun (value, _state) -> V.text "Bytes" value)
let field body name = call (V.of_text "Bytes" body) (V.of_text "Bytes" name)
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* value, _text = I.run checked in V.text "Bytes" value
let metadata change_row change_entry =
  let* checked = checked in let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Form.field") operations
    |> Option.to_result ~none:(Error.Unbound "Form.field") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Form.field" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let request source form =
  let* checked = E.check_lanyard (base ^ source) in I.request ~form ~uri:"/todos" checked
let handler = "def main : Cx -> Uri -> Bytes -> SeeOther := fun (cx : Cx) (uri : Uri) (body : Bytes) => "
  ^ "topcoat.see_other (Uri.from_text Bytes (Form.field Bytes body b\"next\"))"
let good = [
  "title=write+tests", "title", "write tests"; "title=", "title", "";
  "%74itle=caf%C3%A9", "title", "caf\195\169"; "title=caf\195\169", "title", "caf\195\169";
  "title=%26%3D%2B%25%00", "title", "&=+%\000"; "title=%2526", "title", "%26";
  "other=x&title=a=b=c", "title", "a=b=c";
  "%E6%97%A5=%F0%9F%98%80", "\230\151\165", "\240\159\152\128";
  "a+b=space&a%2Bb=plus", "a+b", "plus" ]
let bad = [
  "", "missing"; "other=value", "missing"; "title", "name=value";
  "=value", "empty"; "title=one&title=two", "duplicate";
  "title=one&%74itle=two", "duplicate"; "title=x&a=1&a=2", "duplicate";
  "title=x&", "name=value"; "&title=x", "name=value"; "title=x&&a=1", "name=value";
  "title=%", "escape"; "title=%0", "escape"; "title=%GG", "escape";
  "title=x&other=%ff", "UTF-8"; "title=%c0%af", "UTF-8";
  "title=%ed%a0%80", "UTF-8"; "title=%f4%90%80%80", "UTF-8";
  "title=%e2%82", "UTF-8"; "%ff=x&title=ok", "UTF-8" ]
let cases =
  List.mapi (fun index (body, name, expected) -> "decode " ^ string_of_int index, equal expected (field body name)) good
  @ List.mapi (fun index (body, message) -> "refused form " ^ string_of_int index, refuses message (field body "title")) bad
  @ [
    "body limit accepted", equal (String.make 8186 'x') (field ("title=" ^ String.make 8186 'x') "title");
    "body limit refused", refuses "8192" (field ("title=" ^ String.make 8187 'x') "title");
    "field limit accepted", equal "127" (field (String.concat "&" (List.init 128 (fun i -> "k" ^ string_of_int i ^ "=" ^ string_of_int i))) "k127");
    "field limit refused", refuses "128" (field (String.concat "&" (List.init 129 (fun i -> "k" ^ string_of_int i ^ "=x"))) "k0");
    "byte range", refuses "0..255" (call (V.Tag (Erase.mu_tid "Bytes", 1, [V.Nat (Bignum.of_int 256); V.of_text "Bytes" ""])) (V.of_text "Bytes" "title"));
    "raw UTF-8", refuses "UTF-8" (field "title=\255" "title");
    "field UTF-8", refuses "UTF-8" (field "title=x" "\255");
    "direct call", equal "direct" (evaluate "def main : Bytes := Form.field Bytes b\"title=direct\" b\"title\"");
    "captured call", equal "captured" (evaluate ("def main : Bytes := let body : Bytes := b\"title=captured\" in "
      ^ "let read : Bytes -> Bytes := fun (name : Bytes) => Form.field Bytes body name in read b\"title\""));
    "unused invalid input", refuses "escape" (evaluate "def main : Bytes := let ignored : Bytes := Form.field Bytes b\"title=%\" b\"title\" in b\"ok\"");
    "argument evaluation order", refuses "origin-form" (evaluate "def main : Bytes := Form.field Bytes (bytesCons 255 bytesNil) (let invalid : Uri := Uri.from_text Bytes b\"//host\" in b\"title\")");
    "unsupported layout", refuses "byte list" (let* checked = E.check_lanyard "def main : Nat := Form.field Nat 0 0" in I.run checked);
    "open type", refuses "closed" (let* checked = E.check_lanyard "def main : (0 A : Type 0) -> A -> A -> A := fun (0 A : Type 0) (body : A) (key : A) => Form.field A body key" in I.prepare checked);
    "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = [] }));
    "metadata arity", refuses "metadata" (metadata (fun row -> { row with arity = 1 }) Fun.id);
    "metadata quantities", refuses "metadata" (metadata Fun.id (fun row -> { row with quantities = [C.Zero; C.Many] }));
    "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant }));
    "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = T.specification T.Trim }));
    "metadata type argument", refuses "metadata" (metadata (fun row -> { row with type_arguments = [] }) Fun.id);
    "request body", equal "HTTP/1.1 303 See Other\r\nLocation: /done\r\nContent-Length: 0\r\n\r\n" (request handler "next=%2Fdone" |> Result.map snd);
    "request unused invalid body", refuses "escape" (request "def main : Cx -> Uri -> Bytes -> SeeOther := fun (cx : Cx) (uri : Uri) (body : Bytes) => topcoat.see_other uri" "title=%");
    "request body layout", refuses "byte list" (request "def main : Cx -> Uri -> Nat -> SeeOther := fun (cx : Cx) (uri : Uri) (body : Nat) => topcoat.see_other uri" "title=x");
    "request body required", refuses "entry point" (let* checked = E.check_lanyard (base ^ handler) in I.request ~uri:"/" checked);
    "request body extra", refuses "entry point" (request "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => topcoat.see_other uri" "title=x");
    "emitted parser", (let* checked = checked in let* code = Lanyard_rust.Model.source checked in
      if contains code "Form::<Vec<(String, String)>>::from_bytes" && contains code "lan_form_validate_component(key)?"
        && contains code "InvalidForm" then Ok () else fail "missing emitted parser") ]
let () =
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-FORM OK checks=%d\n" (List.length cases) else exit 1
