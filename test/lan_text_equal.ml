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
  ^ "def Bool : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))\n"
let fail message = Error (Error.Mismatch message)
let contains text needle =
  List.init (max 0 (String.length text - String.length needle + 1)) Fun.id
  |> List.exists (fun index -> String.equal needle (String.sub text index (String.length needle))) (* @total-accessor *)
let equal expected result = let* actual = result in
  if Bool.equal actual expected then Ok () else fail "unexpected text equality"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked () = E.check_lanyard (base ^ "def main : Bytes -> Bytes -> Bool := Text.equal Bytes")
let prepared = let* checked = checked () in I.prepare checked
let call arguments =
  let* context = prepared in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments
  |> Result.map fst
let compare left right = let* value = call [V.of_text "Bytes" left; V.of_text "Bytes" right] in
  V.boolean value
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* value, _store = I.run checked in V.boolean value
let metadata change_row change_entry =
  let* checked = checked () in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> String.equal text.row.schema "Text.equal") operations
    |> Option.to_result ~none:(Error.Unbound "Text.equal") in
  let entries = List.map (fun (entry : C.entry) ->
    if String.equal entry.name "Text.equal" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let pairs = ["", "", true; "", "x", false; "x", "", false;
  "same", "same", true; "same", "sane", false; "a", "A", false;
  "a", "a ", false; "prefix", "prefix-tail", false;
  "café", "café", true; "é", "e\204\129", false;
  "\000", "\000", true; "a\000b", "a\000c", false;
  "\240\159\166\128", "\240\159\166\128", true]
let invalid_text = ["\255"; "\192\175"; "\195"; "\237\160\128"; "\244\144\128\128"]
let cases = List.map (fun (left, right, expected) ->
    "pair " ^ String.escaped left ^ "/" ^ String.escaped right, equal expected (compare left right)) pairs
  @ List.concat_map (fun bad -> [
      "invalid left " ^ String.escaped bad, refuses "UTF-8" (compare bad "x");
      "invalid right " ^ String.escaped bad, refuses "UTF-8" (compare "x" bad);
      "identical invalid " ^ String.escaped bad, refuses "UTF-8" (compare bad bad)]) invalid_text
  @ [
  "alias", equal true (evaluate
    "def same : Bytes -> Bytes -> Bool := Text.equal Bytes\ndef main : Bool := same b\"x\" b\"x\"");
  "captured input", equal false (evaluate
    "def main : Bool := let left : Bytes := b\"left\" in let f : Bytes -> Bool := fun (right : Bytes) => Text.equal Bytes left right in f b\"right\"");
  "input type alias", equal true (evaluate
    "def TextType : Type 0 := Bytes\ndef main : Bool := Text.equal TextType b\"x\" b\"x\"");
  "composed inputs", equal true (evaluate
    "def main : Bool := Text.equal Bytes (Text.trim Bytes b\" xy \" ) (Text.concat Bytes b\"x\" b\"y\")");
  "shared inputs", equal true (evaluate
    "def main : Bool := let text : Bytes := b\"shared\" in Text.equal Bytes text text");
  "invalid left byte", refuses "255" (evaluate
    "def main : Bool := Text.equal Bytes (bytesCons 256 bytesNil) b\"x\"");
  "invalid right byte", refuses "255" (evaluate
    "def main : Bool := Text.equal Bytes b\"x\" (bytesCons 256 bytesNil)");
  "unused result validates", refuses "UTF-8" (evaluate
    "def main : Bool := let ignored : Bool := Text.equal Bytes b\"x\" (bytesCons 255 bytesNil) in Text.is_empty Bytes b\"\"");
  "wrong left runtime value", refuses "byte list" (call [V.Unit; V.of_text "Bytes" ""]);
  "wrong right runtime value", refuses "byte list" (call [V.of_text "Bytes" ""; V.Unit]);
  "unsupported input layout", refuses "byte list" (evaluate "def main : Bool := Text.equal Nat 1 1");
  "open input type", refuses "closed"
    (let* checked = E.check_lanyard (base ^ "def main : (0 A : Type 0) -> A -> A -> Bool := fun (0 A : Type 0) (left : A) (right : A) => Text.equal A left right") in I.prepare checked);
  "representations", (let* arguments, result, _render, effect = metadata Fun.id Fun.id in
    let input = Rir.TyArc (Rir.TyUnion (Erase.mu_tid "Bytes")) in
    if arguments = [input; input] && result = T.bool_repr && effect = Lanyard_rust.Effects.Sync
    then Ok () else fail "text inputs or Boolean result representation differs");
  "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
  "metadata arity", refuses "metadata" (metadata (fun row -> { row with arity = 1 }) Fun.id);
  "metadata quantities", refuses "metadata" (metadata Fun.id (fun row -> { row with quantities = [C.Zero; C.Many; C.One] }));
  "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant }));
  "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = T.specification T.Concat }));
  "metadata type argument", refuses "metadata" (metadata (fun row -> { row with type_arguments = [] }) Fun.id);
  "metadata print rule", refuses "metadata" (metadata Fun.id (fun row -> { row with print_rule = "#{other}" }));
  "render arity", (let* _arguments, _result, render, _effect = metadata Fun.id Fun.id in
    refuses "argument count" (render ["left"]));
]
let () =
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-TEXT-EQUAL OK checks=%d\n" (List.length cases) else exit 1
