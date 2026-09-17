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
  List.init (max 0 (String.length text - String.length needle + 1)) Fun.id
  |> List.exists (fun index -> String.equal needle (String.sub text index (String.length needle))) (* @total-accessor *)
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected concatenation result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked () = E.check_lanyard (base ^ "def main : Bytes -> Bytes -> Bytes := Text.concat Bytes")
let call arguments =
  let* checked = checked () in
  let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments
  |> Result.map fst
let concat left right =
  let* value = call [V.of_text "Bytes" left; V.of_text "Bytes" right] in
  V.text ~what:"concat" "Bytes" value
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* value, _text = I.run checked in V.text ~what:"concat" "Bytes" value
let metadata change_row change_entry =
  let* checked = checked () in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Text.concat") operations
    |> Option.to_result ~none:(Error.Unbound "Text.concat") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Text.concat" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let malformed = V.Tag (Erase.mu_tid "Bytes", 1, [V.Nat (Bignum.of_int 256); V.of_text "Bytes" ""])
let cases = [
  "left before right", equal "leftright" (concat "left" "right");
  "empty left", equal "right" (concat "" "right");
  "empty right", equal "left" (concat "left" "");
  "both empty", equal "" (concat "" "");
  "Unicode", equal "caf\195\169\230\151\165\240\159\152\128" (concat "caf\195\169" "\230\151\165\240\159\152\128");
  "controls", equal "a\000\r\nb" (concat "a\000" "\r\nb");
  "markup stays literal", equal "<b>&lt;\"'" (concat "<b>" "&lt;\"'");
  "UTF-8 fragments refused separately", refuses "UTF-8" (concat "\195" "\169");
  "nested", equal "abc" (evaluate "def main : Bytes := Text.concat Bytes b\"a\" (Text.concat Bytes b\"b\" b\"c\")");
  "alias", equal "ab" (evaluate
    "def join : Bytes -> Bytes -> Bytes := Text.concat Bytes\ndef main : Bytes := join b\"a\" b\"b\"");
  "partial application refused", refuses "arity" (evaluate
    "def main : Bytes := let append : Bytes -> Bytes := Text.concat Bytes b\"prefix:\" in append b\"value\"");
  "captured helper", equal "<title>" (evaluate
    "def main : Bytes := let prefix : Bytes := b\"<\" in let wrap : Bytes -> Bytes := fun (value : Bytes) => Text.concat Bytes prefix (Text.concat Bytes value b\">\") in wrap b\"title\"");
  "escaped composition", equal "<h1>&lt;script&gt;&amp;</h1>" (evaluate
    "def main : Bytes := Text.concat Bytes b\"<h1>\" (Text.concat Bytes (Html.text Bytes b\"<script>&\") b\"</h1>\")");
  "unused left fails", refuses "UTF-8" (evaluate
    "def main : Bytes := let ignored : Bytes := Text.concat Bytes (bytesCons 255 bytesNil) b\"ok\" in b\"done\"");
  "unused right fails", refuses "UTF-8" (evaluate
    "def main : Bytes := let ignored : Bytes := Text.concat Bytes b\"ok\" (bytesCons 255 bytesNil) in b\"done\"");
  "unsupported layout", refuses "byte list"
    (let* checked = E.check_lanyard "def main : Nat := Text.concat Nat 1 2" in I.run checked);
  "open type", refuses "closed"
    (let* checked = E.check_lanyard "def main : (0 A : Type 0) -> A -> A -> A := fun (0 A : Type 0) (left : A) (right : A) => Text.concat A left right" in I.prepare checked);
  "metadata valid", Result.map (fun _contract -> ()) (metadata Fun.id Fun.id);
  "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
  "metadata arity", refuses "metadata" (metadata (fun row -> { row with arity = 1 }) Fun.id);
  "metadata quantities", refuses "metadata" (metadata Fun.id (fun row -> { row with quantities = [C.Zero; C.Many; C.One] }));
  "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant }));
  "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = T.specification T.Trim }));
  "metadata type argument", refuses "metadata" (metadata (fun row -> { row with type_arguments = [] }) Fun.id);
  "metadata print rule", refuses "metadata" (metadata Fun.id (fun row -> { row with print_rule = "#{right}" }));
] @ List.concat_map (fun (side, arguments) -> [
  side ^ " byte range", refuses "0..255" (call (arguments malformed));
  side ^ " malformed UTF-8", refuses "UTF-8" (call (arguments (V.of_text "Bytes" "\255")));
  side ^ " truncated UTF-8", refuses "UTF-8" (call (arguments (V.of_text "Bytes" "\226\130")));
  side ^ " wrong family", refuses "byte list" (call (arguments (V.of_text "Other" "text")));
]) ["left", (fun value -> [value; V.of_text "Bytes" ""]);
    "right", (fun value -> [V.of_text "Bytes" ""; value])]
let () =
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-CONCAT OK checks=%d\n" (List.length cases) else exit 1
