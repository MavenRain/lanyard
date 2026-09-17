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
  if actual = expected then Ok () else fail "unexpected decimal text"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked () = E.check_lanyard (base ^ "def main : Nat -> Bytes := Text.from_nat Bytes")
let prepared = let* checked = checked () in I.prepare checked
let call value =
  let* context = prepared in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value]
  |> Result.map fst
let decimal value =
  let* number = Bignum.of_decimal value |> Option.to_result ~none:(Error.Mismatch "invalid test natural") in
  let* value = call (V.Nat number) in V.text ~what:"decimal" "Bytes" value
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* value, _output = I.run checked in V.text ~what:"decimal" "Bytes" value
let metadata change_row change_entry =
  let* checked = checked () in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Text.from_nat") operations
    |> Option.to_result ~none:(Error.Unbound "Text.from_nat") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Text.from_nat" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let numbers = ["0"; "1"; "9"; "10"; "99"; "100"; "255"; "256"; "257";
  "65535"; "65536"; "65537"; "16777215"; "16777216"; "4294967295"; "4294967296";
  "9223372036854775807"; "9223372036854775808"; "18446744073709551615"; "18446744073709551616";
  "340282366920938463463374607431768211455"; "340282366920938463463374607431768211456";
  "123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890";
  String.make 100 '9']
let cases = List.map (fun number -> "decimal " ^ number, equal number (decimal number)) numbers @ [
  "leading zeroes", equal "42" (decimal "000042");
  "addition", equal "18446744073709551616" (evaluate
    "def main : Bytes := Text.from_nat Bytes (natAdd 18446744073709551615 1)");
  "multiplication", equal "1208925819614629174706176" (evaluate
    "def main : Bytes := Text.from_nat Bytes (natMul 1099511627776 1099511627776)");
  "subtraction", equal "0" (evaluate "def main : Bytes := Text.from_nat Bytes (natSub 1 2)");
  "alias", equal "256" (evaluate
    "def decimal : Nat -> Bytes := Text.from_nat Bytes\ndef main : Bytes := decimal 256");
  "captured natural", equal "4294967296" (evaluate
    "def main : Bytes := let number : Nat := 4294967296 in let render : prod () -> Bytes := fun (u : prod ()) => Text.from_nat Bytes number in render ()");
  "output alias", equal "42" (evaluate
    "def TextType : Type 0 := Bytes\ndef main : TextType := Text.from_nat TextType 42");
  "concat composition", equal "/todos/256" (evaluate
    "def main : Bytes := Text.concat Bytes b\"/todos/\" (Text.from_nat Bytes 256)");
  "negative runtime natural", refuses "natural number" (call (V.Nat (Bignum.of_int (-1))));
  "wrong runtime value", refuses "natural number" (call V.Unit);
  "text is not a natural", refuses "natural number" (call (V.of_text "Bytes" "42"));
  "unsupported output layout", refuses "byte list"
    (let* checked = E.check_lanyard "def main : Nat := Text.from_nat Nat 1" in I.run checked);
  "open output type", refuses "closed"
    (let* checked = E.check_lanyard "def main : (0 A : Type 0) -> Nat -> A := fun (0 A : Type 0) (value : Nat) => Text.from_nat A value" in I.prepare checked);
  "input representation", (let* arguments, result, _render, effect = metadata Fun.id Fun.id in
    if arguments = [Rir.TyArc (Rir.TyUnion (Rir.Tid "nat"))]
       && result = Rir.TyUnion (Erase.mu_tid "Bytes") && effect = Lanyard_rust.Effects.Sync
    then Ok () else fail "natural input or text result representation differs");
  "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = ["topcoat::Error"] }));
  "metadata arity", refuses "metadata" (metadata (fun row -> { row with arity = 2 }) Fun.id);
  "metadata quantities", refuses "metadata" (metadata Fun.id (fun row -> { row with quantities = [C.Zero; C.One] }));
  "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant }));
  "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = T.specification T.Trim }));
  "metadata type argument", refuses "metadata" (metadata (fun row -> { row with type_arguments = [] }) Fun.id);
  "metadata print rule", refuses "metadata" (metadata Fun.id (fun row -> { row with print_rule = "#{other}" }));
]
let () =
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-NAT-TEXT OK checks=%d\n" (List.length cases) else exit 1
