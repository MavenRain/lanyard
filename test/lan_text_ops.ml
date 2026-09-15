open Kanon_kernel
module E = Kanon_surface.Elab
module L = Kanon_surface.Lower
module T = Lanyard_rust.Text_ops
module I = Lanyard_rust.Interp
module V = Lanyard_rust.Run_value
module S = Lanyard_rust.Run_store
module C = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let base = "mu Bytes : Type 0 := | nil : Bytes | cons (head : Nat) (tail : Bytes) : Bytes\n"
let bool = "sum ((prod () : Type 0), (prod () : Type 0))"
let fail message = Error (Error.Mismatch message)
let contains text needle = String.to_seq text |> List.of_seq |> List.to_seq
  |> Seq.mapi (fun index _character -> index) |> Seq.exists (fun index ->
    String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected text result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let literal text = String.to_seq text |> List.of_seq |> List.rev
  |> List.fold_left (fun tail byte -> "(cons " ^ string_of_int (Char.code byte) ^ " " ^ tail ^ ")") "nil"
let eval_source source =
  let* checked = E.check_lanyard source in
  let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [] |> Result.map fst
let evaluate ty expression = eval_source (base ^ "def main : " ^ ty ^ " := " ^ expression)
let trim input expected = equal (V.of_text "Bytes" expected)
  (evaluate "Bytes" ("Text.trim Bytes " ^ literal input))
let empty input expected =
  let* value = evaluate bool ("Text.is_empty Bytes " ^ literal input) in
  equal expected (V.boolean value)
let checked = E.check_lanyard (base ^ "def main : Bytes -> Bytes := Text.trim Bytes")
let operations =
  let* checked = checked in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  T.catalog specialized.specialized instances
let metadata ?(rewrite = Fun.id) change_row change_entry =
  let* operations = operations in
  let operations = List.map (fun (text : T.t) -> { text with row = rewrite text.row }) operations in
  let* text = List.find_opt (fun (text : T.t) -> text.row.schema = "Text.trim") operations
    |> Option.to_result ~none:(Error.Unbound "Text.trim") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Text.trim" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row text.row)
let whitespace = ["\009"; "\010"; "\011"; "\012"; "\013"; " "; "\194\133"; "\194\160";
  "\225\154\128"; "\226\128\128"; "\226\128\129"; "\226\128\130"; "\226\128\131";
  "\226\128\132"; "\226\128\133"; "\226\128\134"; "\226\128\135"; "\226\128\136";
  "\226\128\137"; "\226\128\138"; "\226\128\168"; "\226\128\169"; "\226\128\175";
  "\226\129\159"; "\227\128\128"]
let tests = [
  "ASCII trim", trim " \t hello  world \r\n" "hello  world";
  "empty trim", trim "" "";
  "whitespace-only trim", trim (String.concat "" whitespace) "";
  "Unicode trim", trim "\194\160\227\128\128caf\195\169\226\128\168" "caf\195\169";
  "Unicode neighbors preserved", trim " \225\160\142\226\128\139\239\187\191\226\129\160 " "\225\160\142\226\128\139\239\187\191\226\129\160";
  "four-byte scalar and NUL", trim " \240\159\166\128\000 " "\240\159\166\128\000";
  "already trimmed", trim "a\nb" "a\nb";
  "empty true", empty "" true;
  "nonempty false", empty "hello" false;
  "spaces are nonempty", empty " " false;
  "NUL is nonempty", empty "\000" false;
  "trim alias and closure", equal (V.of_text "Bytes" "hi") (eval_source (base ^
    "def trim : Bytes -> Bytes := Text.trim Bytes\n" ^
    "def main : Bytes := let original : Bytes := " ^ literal " hi " ^ " in " ^
    "let f : Nat -> Bytes := fun (n : Nat) => trim original in f 1"));
  "shared input remains intact", equal (V.of_text "Bytes" " hi ") (evaluate "Bytes"
    ("let original : Bytes := " ^ literal " hi " ^
     " in let trimmed : Bytes := Text.trim Bytes original in original"));
  "unused trim validates", refuses "invalid UTF-8" (evaluate "Nat"
    "let unused : Bytes := Text.trim Bytes (cons 255 nil) in 1");
  "unused empty validates", refuses "invalid UTF-8" (evaluate "Nat"
    ("let unused : " ^ bool ^ " := Text.is_empty Bytes (cons 255 nil) in 1"));
  "is_empty alias", (let* value = eval_source (base ^ "def empty : Bytes -> " ^ bool ^
    " := Text.is_empty Bytes\ndef main : " ^ bool ^ " := empty (Text.trim Bytes " ^ literal " " ^ ")") in
    equal true (V.boolean value));
  "distinct text families", equal (V.of_text "Other" "hi") (eval_source (base ^
    "mu Other : Type 0 := | stop : Other | more (head : Nat) (tail : Other) : Other\n" ^
    "def main : Other := let first : Bytes := Text.trim Bytes " ^ literal " x " ^
    " in Text.trim Other (more 32 (more 104 (more 105 (more 32 stop))))"));
  "Nat layout refused", refuses "byte list" (evaluate "Nat" "Text.trim Nat 1");
  "wrong list element refused", refuses "byte list" (eval_source (
    "mu Bad : Type 0 := | nil : Bad | cons (head : prod ()) (tail : Bad) : Bad\n" ^
    "def main : Bad := Text.trim Bad nil"));
  "open text type refused", refuses "text type arguments must be closed" (
    let* source = E.check_lanyard
      "def main : (0 T : Type 0) -> T -> T := fun (0 T : Type 0) (x : T) => Text.trim T x" in
    Lanyard_rust.Model.source source);
  "bad byte range", refuses "outside 0..255" (evaluate "Bytes" "Text.trim Bytes (cons 256 nil)");
  "invalid UTF-8 trim", refuses "invalid UTF-8" (evaluate "Bytes" "Text.trim Bytes (cons 255 nil)");
  "invalid UTF-8 empty", refuses "invalid UTF-8" (evaluate bool "Text.is_empty Bytes (cons 192 (cons 128 nil))");
  "truncated UTF-8", refuses "invalid UTF-8" (T.trim "\226\128");
  "checked text contract", (let* inputs, result, _render, effect = metadata Fun.id Fun.id in
    equal ([Rir.TyArc (Rir.TyUnion (Erase.mu_tid "Bytes"))], Rir.TyUnion (Erase.mu_tid "Bytes"),
      Lanyard_rust.Effects.Sync) (Ok (inputs, result, effect)));
  "emitted trim", (let* source = checked in let* rust = Lanyard_rust.Model.source source in
    if contains rust ".trim().to_owned()" && contains rust "String::from_utf8"
    then Ok () else fail "missing checked trim adapter");
  "emitted empty", (let* source = E.check_lanyard (base ^ "def main : Bytes -> " ^ bool ^ " := Text.is_empty Bytes") in
    let* rust = Lanyard_rust.Model.source source in
    if contains rust ".is_empty()" && contains rust "::V1(()) } else {"
    then Ok () else fail "missing Boolean conversion");
  "metadata type arguments", refuses "text metadata differs" (metadata (fun row -> {row with type_arguments = []}) Fun.id);
  "metadata name", refuses "text metadata differs" (metadata (fun row -> {row with name = "other"}) Fun.id);
  "metadata effects", refuses "text metadata differs" (metadata (fun row -> {row with effects = ["DbExec"]}) Fun.id);
  "schema type", refuses "text schema metadata" (metadata Fun.id (fun entry -> {entry with kernel_type = "(text : Nat) -> Nat"}));
  "schema quantity", refuses "text schema metadata" (metadata Fun.id (fun entry -> {entry with quantities = [C.Zero; C.One]}));
  "schema kind", refuses "text schema kind" (metadata Fun.id (fun entry -> {entry with kind = C.Constant}));
  "checked arity", refuses "text schema metadata" (metadata ~rewrite:(fun row -> {row with arity = 2}) Fun.id Fun.id);
  "schema placeholders", refuses "text schema placeholders" (metadata
    ~rewrite:(fun row -> {row with print_rule = "#{unknown}"}) Fun.id (fun entry -> {entry with print_rule = "#{unknown}"}));
  "render argument count", (let* _inputs, _result, render, _effects = metadata Fun.id Fun.id in
    refuses "text argument count" (render []));
  "runtime rejects foreign family", (let* operations = operations in
    let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Text.trim") operations
      |> Option.to_result ~none:(Error.Unbound "Text.trim") in
    refuses "expected a model byte list" (S.foreign
      { S.models = []; connections = []; texts = operations; constants = [] }
      operation.row [V.of_text "Other" "hi"] S.empty));
  "runtime rejects unregistered text", (let* operations = operations in
    let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Text.trim") operations
      |> Option.to_result ~none:(Error.Unbound "Text.trim") in
    refuses "text metadata differs" (S.foreign
      { S.models = []; connections = []; texts = []; constants = [operation.row] }
      operation.row [V.of_text "Bytes" "hi"] S.empty));
] @ List.mapi (fun index space -> "whitespace " ^ string_of_int index, trim (space ^ "x" ^ space) "x") whitespace
let () =
  let failures = List.filter_map (fun (name, result) -> Result.fold
    ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) tests in
  List.iter prerr_endline failures;
  Printf.printf "LAN-TEXT-OPS %s checks=%d failures=%d\n"
    (if List.is_empty failures then "OK" else "FAIL") (List.length tests) (List.length failures);
  if not (List.is_empty failures) then exit 1
