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
  if String.equal expected actual then Ok () else fail "unexpected repetition result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if T.contains (Error.to_string error) needle then Ok () else Error error) result
let checked () = E.check_lanyard (base ^ "def main : Bytes -> Nat -> Bytes := Text.repeat Bytes")
let metadata change_row change_entry =
  let* checked = checked () in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Text.repeat") operations
    |> Option.to_result ~none:(Error.Unbound "Text.repeat") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Text.repeat" then change_entry entry else entry) C.entries in
  let drift (text : T.t) = if text.row.schema = "Text.repeat" then { text with T.row = change_row text.row } else text in
  T.foreign_call entries (List.map drift operations) (change_row operation.row)
let tests () =
  let* checked = checked () in
  let* context = I.prepare checked in
  let call arguments = I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments
    |> Result.map fst in
  let repeat text count =
    let* value = call [V.of_text "Bytes" text; V.Nat count] in
    V.text ~what:"repeat" "Bytes" value in
  let texts = [""; "a"; "abc"; " \r\n"; "a\000b"; "\195\169"; "e\204\129";
    "\230\151\165\230\156\172"; "\240\159\166\128"] in
  let checks = List.concat_map (fun text -> List.map (fun count ->
    "oracle", equal (String.concat "" (List.init count (fun _index -> text)))
      (repeat text (Bignum.of_int count))) [0; 1; 2; 3; 7; 32; 256]) texts in
  let* huge = Bignum.of_decimal "340282366920938463463374607431768211456"
    |> Option.to_result ~none:(Error.Mismatch "test natural") in
  let malformed = V.Tag (Erase.mu_tid "Bytes", 1,
    [V.Nat (Bignum.of_int 256); V.of_text "Bytes" ""]) in
  let invalid = List.concat_map (fun (name, value, message) ->
    List.map (fun count -> name, refuses message (call [value; V.Nat (Bignum.of_int count)])) [0; 1; 3])
    ["range", malformed, "0..255"; "UTF-8", V.of_text "Bytes" "\255", "UTF-8";
     "continuation", V.of_text "Bytes" "\128", "UTF-8";
     "incomplete", V.of_text "Bytes" "\195", "UTF-8";
     "surrogate", V.of_text "Bytes" "\237\160\128", "UTF-8";
     "text type", V.Nat Bignum.zero, "byte list"] in
  let checks = checks @ invalid @ [
    "empty huge", equal "" (repeat "" huge);
    "huge", refuses "overflow" (repeat "x" huge);
    "size overflow", refuses "overflow" (repeat "xx" (Bignum.of_int Sys.max_string_length));
    "negative", refuses "natural number" (repeat "" (Bignum.of_int (-1)));
    "count type", refuses "natural number" (call [V.of_text "Bytes" ""; V.Unit]);
    "helper negative", refuses "negative" (T.repeat "" (Bignum.of_int (-1)));
    "helper UTF-8", refuses "UTF-8" (T.repeat "\255" Bignum.zero);
    "metadata valid", Result.map (fun _contract -> ()) (metadata Fun.id Fun.id);
    "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = [] }));
    "metadata arity", refuses "schema metadata" (metadata (fun row -> { row with arity = 1 }) Fun.id);
    "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant }));
    "metadata quantity", refuses "metadata" (metadata Fun.id (fun row -> { row with quantities = [C.Zero; C.Many; C.Zero] }));
    "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = "(0 Text : Type 0) -> (text : Text) -> (count : Text) -> Text" }));
    "metadata print", refuses "schema metadata" (metadata (fun row -> { row with print_rule = "wrong" }) Fun.id);
    "argument types", (let* arguments, _result, _render, _effect = metadata Fun.id Fun.id in
      if arguments = [Rir.TyArc (Rir.TyUnion (Erase.mu_tid "Bytes")); Rir.TyArc (Rir.TyUnion (Rir.Tid "nat"))]
      then Ok () else fail "mixed argument types")
  ] in
  let* _results = Rules.all_ok (List.map (fun (name, result) ->
    Result.map_error (fun error -> Error.Mismatch (name ^ ": " ^ Error.to_string error)) result) checks) in
  Ok (List.length checks)
let () = tests () |> Result.fold
  ~ok:(fun count -> Printf.printf "LAN-TEXT-REPEAT OK checks=%d\n" count)
  ~error:(fun error -> prerr_endline (Error.to_string error); exit 1)
