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
let contains text needle = String.to_seq text |> List.of_seq |> List.to_seq
  |> Seq.mapi (fun index _character -> index) |> Seq.exists (fun index ->
    String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let equal expected result = let* actual = result in
  if String.equal actual expected then Ok () else fail "unexpected parsed natural"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked () = E.check_lanyard (base ^ "def main : Bytes -> Nat := Text.to_nat Bytes")
let prepared = let* checked = checked () in I.prepare checked
let call value =
  let* context = prepared in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value]
  |> Result.map fst
let number value = let* value = value in
  V.natural value |> Result.map Bignum.to_string
let parse text = number (call (V.of_text "Bytes" text))
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  number (I.run checked |> Result.map fst)
let metadata change_row change_entry =
  let* checked = checked () in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> String.equal text.row.schema "Text.to_nat") operations
    |> Option.to_result ~none:(Error.Unbound "Text.to_nat") in
  let entries = List.map (fun (entry : C.entry) ->
    if String.equal entry.name "Text.to_nat" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let numbers = ["0"; "1"; "9"; "10"; "255"; "256"; "65535"; "65536";
  "4294967296"; "9223372036854775807"; "9223372036854775808";
  "18446744073709551615"; "18446744073709551616";
  "340282366920938463463374607431768211456"; String.make 100 '9']
let invalid_text = [""; " "; " 1"; "1 "; "\t1"; "1\n"; "+1"; "-1"; "1.0";
  "1e2"; "0x10"; "1_000"; "1,000"; "1a"; "a1"; "１２"; "١"; "1\0002"]
let cases = List.map (fun text -> "decimal " ^ text, equal text (parse text)) numbers
  @ List.map (fun text -> "invalid " ^ String.escaped text, refuses "decimal natural" (parse text)) invalid_text
  @ [
  "leading zeros", equal "42" (parse "000042");
  "all zeros", equal "0" (parse "0000");
  "alias", equal "256" (evaluate "def parse : Bytes -> Nat := Text.to_nat Bytes\ndef main : Nat := parse b\"256\"");
  "captured text", equal "4294967296" (evaluate
    "def main : Nat := let text : Bytes := b\"4294967296\" in let parse : prod () -> Nat := fun (u : prod ()) => Text.to_nat Bytes text in parse ()");
  "input alias", equal "42" (evaluate
    "def TextType : Type 0 := Bytes\ndef main : Nat := Text.to_nat TextType b\"42\"");
  "computed text", equal "1024" (evaluate
    "def main : Nat := Text.to_nat Bytes (Text.concat Bytes b\"10\" b\"24\")");
  "arithmetic", equal "18446744073709551617" (evaluate
    "def main : Nat := natAdd (Text.to_nat Bytes b\"18446744073709551616\") 1");
  "invalid UTF-8", refuses "UTF-8" (parse "\192\175");
  "byte range", refuses "255" (evaluate "def main : Nat := Text.to_nat Bytes (bytesCons 256 bytesNil)");
  "wrong runtime value", refuses "byte list" (call V.Unit);
  "unsupported input layout", refuses "byte list"
    (let* checked = E.check_lanyard "def main : Nat := Text.to_nat Nat 1" in I.run checked);
  "open input type", refuses "closed"
    (let* checked = E.check_lanyard "def main : (0 A : Type 0) -> A -> Nat := fun (0 A : Type 0) (value : A) => Text.to_nat A value" in I.prepare checked);
  "representations", (let* arguments, result, _render, effect = metadata Fun.id Fun.id in
    if arguments = [Rir.TyArc (Rir.TyUnion (Erase.mu_tid "Bytes"))]
       && result = Rir.TyUnion (Rir.Tid "nat") && effect = Lanyard_rust.Effects.Sync
    then Ok () else fail "text input or natural result representation differs");
  "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = [] }));
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
  if List.is_empty failed then Printf.printf "LAN-TEXT-NAT OK checks=%d\n" (List.length cases) else exit 1
