open Kanon_kernel
module E = Kanon_surface.Elab
module L = Kanon_surface.Lower
module T = Lanyard_rust.Text_ops
module I = Lanyard_rust.Interp
module V = Lanyard_rust.Run_value
module S = Lanyard_rust.Run_store
module C = Lanyard_target.Target_generated
let ( let* ) = Result.bind
type boundary = Prefix | Suffix
let schema = function Prefix -> "Text.starts_with" | Suffix -> "Text.ends_with"
let base = "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
  ^ "def Bool : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))\n"
let fail message = Error (Error.Mismatch message)
let equal expected result = let* actual = result in
  if Bool.equal actual expected then Ok () else fail "unexpected boundary result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if T.contains (Error.to_string error) needle then Ok () else Error error) result
let checked boundary = E.check_lanyard (base ^ "def main : Bytes -> Bytes -> Bool := " ^ schema boundary ^ " Bytes")
let metadata boundary change_row change_entry =
  let* checked = checked boundary in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let name = schema boundary in
  let* operation = List.find_opt (fun (text : T.t) -> String.equal text.row.schema name) operations
    |> Option.to_result ~none:(Error.Unbound name) in
  let entries = List.map (fun (entry : C.entry) ->
    if String.equal entry.name name then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let pairs = [
  "", "", true, true; "", "x", false, false; "x", "", true, true;
  "same", "same", true, true; "a", "A", false, false;
  "prefix-tail", "prefix", true, false; "prefix-tail", "tail", false, true;
  "prefix-tail", "fix-ta", false, false; "x", "xx", false, false;
  " a ", " a", true, false; " a ", "a ", false, true;
  "a\000b", "a\000", true, false; "a\000b", "\000b", false, true;
  "a\000b", "\000", false, false; "\000", "\000", true, true;
  "café", "é", false, true; "éclair", "é", true, false;
  "é", "e\204\129", false, false; "日本語", "本", false, false;
  "\240\159\166\128x", "\240\159\166\128", true, false;
  "x\240\159\166\128", "\240\159\166\128", false, true;
  "aaaaab", "aaab", false, true; "baaaaa", "baaa", true, false]
let invalid_text = ["\255"; "\192\175"; "\195"; "\237\160\128"; "\244\144\128\128"]
let cases boundary =
  let name = schema boundary in
  let prepared = let* checked = checked boundary in I.prepare checked in
  let call arguments = let* context = prepared in
    I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments |> Result.map fst in
  let compare left right = let* value = call [V.of_text "Bytes" left; V.of_text "Bytes" right] in V.boolean value in
  let evaluate source = let* checked = E.check_lanyard (base ^ source) in
    let* value, _store = I.run checked in V.boolean value in
  let main expression = "def main : Bool := " ^ name ^ " Bytes " ^ expression in
  List.map (fun (left, right, prefix, suffix) ->
    let expected = match boundary with Prefix -> prefix | Suffix -> suffix in
    "pair " ^ String.escaped left ^ "/" ^ String.escaped right, equal expected (compare left right)) pairs
  @ List.concat_map (fun bad -> [
      "invalid text", refuses "UTF-8" (compare bad "x");
      "invalid needle", refuses "UTF-8" (compare "x" bad);
      "empty needle validates text", refuses "UTF-8" (compare bad "");
      "empty text validates needle", refuses "UTF-8" (compare "" bad);
      "matching boundary validates remainder", refuses "UTF-8" (compare ("x" ^ bad ^ "x") "x")]) invalid_text
  @ [
    "alias", equal true (evaluate ("def same : Bytes -> Bytes -> Bool := " ^ name ^ " Bytes\ndef main : Bool := same b\"x\" b\"x\""));
    "capture", equal false (evaluate ("def main : Bool := let text : Bytes := b\"left\" in let f : Bytes -> Bool := fun (needle : Bytes) => " ^ name ^ " Bytes text needle in f b\"right\""));
    "type alias", equal true (evaluate ("def TextType : Type 0 := Bytes\ndef main : Bool := " ^ name ^ " TextType b\"x\" b\"x\""));
    "composed", equal true (evaluate (main "(Text.trim Bytes b\" xy \") (Text.concat Bytes b\"x\" b\"y\")"));
    "shared", equal true (evaluate ("def main : Bool := let text : Bytes := b\"same\" in " ^ name ^ " Bytes text text"));
    "text byte range", refuses "255" (evaluate (main "(bytesCons 256 bytesNil) b\"\""));
    "needle byte range", refuses "255" (evaluate (main "b\"\" (bytesCons 256 bytesNil)"));
    "validation order byte first", refuses "255" (evaluate (main "(bytesCons 256 bytesNil) (bytesCons 255 bytesNil)"));
    "validation order UTF-8 first", refuses "UTF-8" (evaluate (main "(bytesCons 255 bytesNil) (bytesCons 256 bytesNil)"));
    "unused result", refuses "UTF-8" (evaluate ("def main : Bool := let ignored : Bool := " ^ name ^ " Bytes b\"x\" (bytesCons 255 bytesNil) in Text.is_empty Bytes b\"\""));
    "wrong text value", refuses "byte list" (call [V.Unit; V.of_text "Bytes" ""]);
    "wrong needle value", refuses "byte list" (call [V.of_text "Bytes" ""; V.Unit]);
    "unsupported layout", refuses "byte list" (evaluate ("def main : Bool := " ^ name ^ " Nat 1 1"));
    "open input", refuses "closed" (let* checked = E.check_lanyard (base ^ "def main : (0 A : Type 0) -> A -> A -> Bool := fun (0 A : Type 0) (text : A) (needle : A) => " ^ name ^ " A text needle") in I.prepare checked);
    "representations", (let* arguments, result, _render, effect = metadata boundary Fun.id Fun.id in
      let input = Rir.TyArc (Rir.TyUnion (Erase.mu_tid "Bytes")) in
      match () with
      | () when arguments = [input; input] && result = T.bool_repr && effect = Lanyard_rust.Effects.Sync -> Ok ()
      | () -> fail "representation differs");
    "effects", refuses "metadata" (metadata boundary Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
    "arity", refuses "metadata" (metadata boundary (fun row -> { row with arity = 1 }) Fun.id);
    "quantities", refuses "metadata" (metadata boundary Fun.id (fun row -> { row with quantities = [C.Zero; C.Many; C.One] }));
    "kind", refuses "kind" (metadata boundary Fun.id (fun row -> { row with kind = C.Constant }));
    "type", refuses "metadata" (metadata boundary Fun.id (fun row -> { row with kernel_type = T.specification T.Concat }));
    "type arguments", refuses "metadata" (metadata boundary (fun row -> { row with type_arguments = [] }) Fun.id);
    "print rule", refuses "metadata" (metadata boundary Fun.id (fun row -> { row with print_rule = "#{other}" }));
    "render arity", (let* _arguments, _result, render, _effect = metadata boundary Fun.id Fun.id in refuses "argument count" (render ["text"]));
  ] |> List.map (fun (label, result) -> name ^ " " ^ label, result)
let () =
  let cases = List.concat_map cases [Prefix; Suffix] in
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-TEXT-BOUNDARIES OK checks=%d\n" (List.length cases) else exit 1
