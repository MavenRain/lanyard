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
let equal expected actual = let* actual = actual in
  if String.equal expected actual then Ok () else fail "unexpected replacement result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if T.contains (Error.to_string error) needle then Ok () else Error error) result
let checked () = E.check_lanyard (base ^ "def main : Bytes -> Bytes -> Bytes -> Bytes := Text.replace Bytes")
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* value, _text = I.run checked in V.text ~what:"replace" "Bytes" value
let metadata change_row change_entry =
  let* checked = checked () in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Text.replace") operations
    |> Option.to_result ~none:(Error.Unbound "Text.replace") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Text.replace" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let cases = [
  "all matches", "one one one", "one", "two", "two two two";
  "no match", "abc", "z", "x", "abc";
  "overlap", "aaaaa", "aa", "b", "bba";
  "fallback", "ababababac", "ababac", "X", "ababX";
  "replacement not searched", "aa", "a", "aa", "aaaa";
  "delete", "banana", "na", "", "ba";
  "empty text", "", "x", "y", "";
  "all empty", "", "", "", "";
  "empty input insertion", "", "", "x", "x";
  "empty needle", "abc", "", "-", "-a-b-c-";
  "Unicode scalars", "\195\169\230\151\165\240\159\152\128", "", "|", "|\195\169|\230\151\165|\240\159\152\128|";
  "combining scalar", "e\204\129", "", "|", "|e|\204\129|";
  "Unicode match", "caf\195\169\195\169", "\195\169", "\230\151\165", "caf\230\151\165\230\151\165";
  "no normalization", "e\204\129", "\195\169", "x", "e\204\129";
  "NUL", "a\000b\000", "\000", "\000x", "a\000xb\000x";
  "case sensitive", "aAa", "a", "X", "XAX";
  "long needle", "a", "aa", "x", "a";
  "whitespace", " a\r\n", "a", "", " \r\n";
]
let malformed = V.Tag (Erase.mu_tid "Bytes", 1, [V.Nat (Bignum.of_int 256); V.of_text "Bytes" ""])
let tests () =
  let* checked = checked () in
  let* context = I.prepare checked in
  let call arguments = I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments
    |> Result.map fst in
  let replace text needle replacement =
    let* value = call (List.map (V.of_text "Bytes") [text; needle; replacement]) in
    V.text ~what:"replace" "Bytes" value in
  let checks = List.map (fun (name, text, needle, replacement, expected) ->
    name, equal expected (replace text needle replacement)) cases in
  let invalid = List.concat_map (fun (name, value, message) ->
    List.init 3 (fun position -> name ^ string_of_int position,
      refuses message (call (List.mapi (fun index text ->
        if position = index then value else V.of_text "Bytes" text) ["abc"; ""; ""]))))
    ["byte range", malformed, "0..255";
     "UTF-8", V.of_text "Bytes" "\255", "UTF-8";
     "continuation", V.of_text "Bytes" "\128", "UTF-8";
     "incomplete", V.of_text "Bytes" "\195", "UTF-8";
     "surrogate", V.of_text "Bytes" "\237\160\128", "UTF-8";
     "wrong type", V.Nat Bignum.zero, "byte list"] in
  let checks = checks @ invalid @ [
    "alias", equal "b" (evaluate "def change : Bytes -> Bytes -> Bytes -> Bytes := Text.replace Bytes\ndef main : Bytes := change b\"a\" b\"a\" b\"b\"");
    "capture", equal "b" (evaluate "def main : Bytes := let r : Bytes := b\"b\" in let f : Bytes -> Bytes := fun (t : Bytes) => Text.replace Bytes t b\"a\" r in f b\"a\"");
    "shared", equal "same" (evaluate "def main : Bytes := let t : Bytes := b\"same\" in Text.replace Bytes t t t");
    "discarded invalid replacement", refuses "UTF-8" (evaluate "def main : Bytes := let unused : Bytes := Text.replace Bytes b\"abc\" b\"z\" (bytesCons 255 bytesNil) in b\"done\"");
    "partial application", refuses "arity" (evaluate "def main : Bytes := let f : Bytes -> Bytes := Text.replace Bytes b\"a\" b\"a\" in f b\"b\"");
    "unsupported family", refuses "byte list" (let* p = E.check_lanyard "def main : Nat := Text.replace Nat 1 2 3" in I.run p);
    "open family", refuses "closed" (let* p = E.check_lanyard "def main : (0 A : Type 0) -> A -> A -> A -> A := fun (0 A : Type 0) (t : A) (n : A) (r : A) => Text.replace A t n r" in I.prepare p);
    "metadata valid", Result.map (fun _contract -> ()) (metadata Fun.id Fun.id);
    "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
    "metadata arity", refuses "metadata" (metadata (fun row -> { row with arity = 2 }) Fun.id);
    "metadata quantities", refuses "metadata" (metadata Fun.id (fun row -> { row with quantities = [C.Zero; C.Many; C.Many; C.One] }));
    "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant }));
    "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = T.specification T.Concat }));
    "metadata type argument", refuses "metadata" (metadata (fun row -> { row with type_arguments = [] }) Fun.id);
    "metadata print", refuses "metadata" (metadata Fun.id (fun row -> { row with print_rule = "#{text}" }));
    "many matches", equal (String.make 50000 'b') (Ok (T.replace (String.make 100000 'a') "aa" "b"));
    "long fallback", equal (String.make 99744 'a' ^ "X") (Ok (T.replace (String.make 100000 'a' ^ "b") (String.make 256 'a' ^ "b") "X"));
    "long miss", equal (String.make 100000 'a') (Ok (T.replace (String.make 100000 'a') (String.make 256 'a' ^ "b") "X"));
  ] in
  let* () = List.fold_left (fun result (name, check) ->
    let* () = result in Result.map_error (fun error ->
      Error.Mismatch (name ^ ": " ^ Error.to_string error)) check) (Ok ()) checks in
  Ok (List.length checks)

(** Simple oracle for small ASCII inputs, independent of fallback search. *)
let oracle text needle replacement =
  let size = String.length needle in
  let rec walk remaining = match remaining () with
    | Seq.Nil -> if size = 0 then replacement else ""
    | Seq.Cons (character, rest) ->
        match () with
        | () when size = 0 -> replacement ^ String.make 1 character ^ walk rest
        | () when String.equal needle (remaining |> Seq.take size |> String.of_seq) ->
            replacement ^ walk (Seq.drop size remaining)
        | () -> String.make 1 character ^ walk rest in
  walk (String.to_seq text)
let rec words size = if size = 0 then [""] else
  "" :: List.concat_map (fun word -> ["a" ^ word; "b" ^ word]) (words (size - 1))
let exhaustive () = List.fold_left (fun result text ->
  let* count = result in List.fold_left (fun result needle ->
    let* count = result in List.fold_left (fun result replacement ->
      let* count = result in
      let* () = equal (oracle text needle replacement) (Ok (T.replace text needle replacement)) in
      Ok (count + 1)) (Ok count) [""; "-"; "ab"]) (Ok count) (words 3)) (Ok 0) (words 5)
let () = (let* checks = tests () in let* oracle = exhaustive () in Ok (checks, oracle))
  |> Result.fold
    ~ok:(fun (checks, oracle) -> Printf.printf "LAN-TEXT-REPLACE OK checks=%d oracle=%d\n" checks oracle)
    ~error:(fun error -> prerr_endline (Error.to_string error); exit 1)
