open Kanon_kernel
module E = Kanon_surface.Elab
module L = Kanon_surface.Lower
module T = Lanyard_rust.Text_ops
module I = Lanyard_rust.Interp
module V = Lanyard_rust.Run_value
module S = Lanyard_rust.Run_store
module C = Lanyard_target.Target_generated
let ( let* ) = Result.bind
type edge = Leading | Trailing
let schema = function Leading -> "Text.trim_start" | Trailing -> "Text.trim_end"
let base = "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
let fail message = Error (Error.Mismatch message)
let equal expected result = let* actual = result in
  if String.equal actual expected then Ok () else fail ("unexpected text: " ^ String.escaped actual)
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if T.contains (Error.to_string error) needle then Ok () else Error error) result
let checked edge = E.check_lanyard (base ^ "def main : Bytes -> Bytes := " ^ schema edge ^ " Bytes")
let metadata ?(catalog_row = Fun.id) edge change_row change_entry =
  let* checked = checked edge in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let name = schema edge in
  let* operation = List.find_opt (fun (text : T.t) -> String.equal text.row.schema name) operations
    |> Option.to_result ~none:(Error.Unbound name) in
  let entries = List.map (fun (entry : C.entry) ->
    if String.equal entry.name name then change_entry entry else entry) C.entries in
  let drift (text : T.t) = if String.equal text.row.schema name then { text with T.row = catalog_row text.row } else text in
  T.foreign_call entries (List.map drift operations) (change_row operation.row)
let pairs = ["", "", ""; " \r\n\t", "", ""; "x", "x", "x";
  " x ", "x ", " x"; "  a b  ", "a b  ", "  a b";
  "\194\160é\227\128\128", "é\227\128\128", "\194\160é";
  " \000 ", "\000 ", " \000"; " e\204\129 ", "e\204\129 ", " e\204\129";
  " \240\159\166\128 ", "\240\159\166\128 ", " \240\159\166\128";
  "\226\128\139 x \239\187\191", "\226\128\139 x \239\187\191", "\226\128\139 x \239\187\191"]
let invalid_text = ["\255"; "\192\175"; "\195"; "\237\160\128"; "\244\144\128\128"]
let cases edge =
  let name = schema edge in
  let prepared = let* checked = checked edge in I.prepare checked in
  let call arguments = let* context = prepared in
    let* value, _store = I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments in
    V.text "Bytes" value in
  let evaluate source = let* checked = E.check_lanyard (base ^ source) in
    let* value, _store = I.run checked in V.text "Bytes" value in
  let main expression = "def main : Bytes := " ^ name ^ " Bytes " ^ expression in
  let expected = match edge with Leading -> "x " | Trailing -> " x" in
  List.map (fun (text, leading, trailing) ->
    let expected = match edge with Leading -> leading | Trailing -> trailing in
    "text " ^ String.escaped text, equal expected (call [V.of_text "Bytes" text])) pairs
  @ List.concat_map (fun bad -> List.map (fun text ->
      "invalid UTF-8 " ^ String.escaped text, refuses "UTF-8" (call [V.of_text "Bytes" text]))
      [bad; " x" ^ bad; bad ^ "x "; " " ^ bad ^ " "]) invalid_text
  @ [
    "alias", equal expected (evaluate ("def trim : Bytes -> Bytes := " ^ name ^ " Bytes\ndef main : Bytes := trim b\" x \""));
    "type alias", equal expected (evaluate ("def TextType : Type 0 := Bytes\ndef main : Bytes := " ^ name ^ " TextType b\" x \""));
    "capture", equal expected (evaluate ("def main : Bytes := let text : Bytes := b\" x \" in let f : Nat -> Bytes := fun (n : Nat) => " ^ name ^ " Bytes text in f 0"));
    "shared", equal (expected ^ " x ") (evaluate ("def main : Bytes := let text : Bytes := b\" x \" in Text.concat Bytes (" ^ name ^ " Bytes text) text"));
    "compose", equal "x" (evaluate (main ("(" ^ schema (match edge with Leading -> Trailing | Trailing -> Leading) ^ " Bytes b\" x \")")));
    "unused", equal "ok" (evaluate ("def main : Bytes := let ignored : Bytes := " ^ name ^ " Bytes b\" x \" in b\"ok\""));
    "byte range", refuses "255" (evaluate (main "(bytesCons 256 bytesNil)"));
    "unused error", refuses "UTF-8" (evaluate ("def main : Bytes := let ignored : Bytes := " ^ name ^ " Bytes (bytesCons 255 bytesNil) in b\"ok\""));
    "wrong value", refuses "byte list" (call [V.Unit]);
    "unsupported layout", refuses "byte list" (evaluate ("def main : Nat := " ^ name ^ " Nat 1"));
    "open input", refuses "closed" (let* checked = E.check_lanyard (base ^ "def main : (0 A : Type 0) -> A -> A := fun (0 A : Type 0) (text : A) => " ^ name ^ " A text") in I.prepare checked);
    "valid metadata", (let* _call = metadata edge Fun.id Fun.id in Ok ());
    "effects", refuses "metadata" (metadata edge Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
    "arity", refuses "schema metadata" (metadata ~catalog_row:(fun row -> { row with arity = 2 }) edge (fun row -> { row with arity = 2 }) Fun.id);
    "quantities", refuses "metadata" (metadata edge Fun.id (fun row -> { row with quantities = [C.Zero; C.One] }));
    "kind", refuses "kind" (metadata edge Fun.id (fun row -> { row with kind = C.Constant }));
    "type", refuses "metadata" (metadata edge Fun.id (fun row -> { row with kernel_type = T.specification T.Concat }));
    "type arguments", refuses "metadata" (metadata edge (fun row -> { row with type_arguments = [] }) Fun.id);
    "print rule", refuses "metadata" (metadata edge Fun.id (fun row -> { row with print_rule = "#{other}" }));
    "render arity", (let* _arguments, _result, render, _effect = metadata edge Fun.id Fun.id in refuses "argument count" (render []));
  ] |> List.map (fun (label, result) -> name ^ " " ^ label, result)
let () =
  let cases = List.concat_map cases [Leading; Trailing] in
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-TEXT-TRIM OK checks=%d\n" (List.length cases) else exit 1
