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
let contains text needle = String.to_seq text |> Seq.mapi (fun index _character -> index)
  |> Seq.exists (fun index -> String.starts_with ~prefix:needle
    (String.to_seq text |> Seq.drop index |> String.of_seq))
let equal expected result = let* actual = result in
  if String.equal actual expected then Ok () else fail ("unexpected length: " ^ actual)
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked () = E.check_lanyard (base ^ "def main : Bytes -> Nat := Text.length Bytes")
let prepared = let* checked = checked () in I.prepare checked
let number result = let* value = result in V.natural value |> Result.map Bignum.to_string
let call value = let* context = prepared in
  number (I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value]
    |> Result.map fst)
let measure text = call (V.of_text "Bytes" text)
let evaluate source = let* checked = E.check_lanyard (base ^ source) in
  number (I.run checked |> Result.map fst)
let metadata change_row change_entry =
  let* checked = checked () in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> String.equal text.row.schema "Text.length") operations
    |> Option.to_result ~none:(Error.Unbound "Text.length") in
  let entries = List.map (fun (entry : C.entry) ->
    if String.equal entry.name "Text.length" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let cases =
  List.map (fun (text, expected) -> "text " ^ String.escaped text, equal expected (measure text))
    ["", "0"; "abc", "3"; " \t\n", "3"; "\000", "1"; "é", "2";
     "é", "3"; "😀", "4"; "日本", "6"; "a\000é😀", "8"]
  @ List.map (fun size -> "length " ^ string_of_int size,
      equal (string_of_int size) (measure (String.make size 'x')))
      [127; 128; 255; 256; 257; 8191; 8192; 8193]
  @ List.map (fun text -> "UTF-8 " ^ String.escaped text, refuses "UTF-8" (measure text))
      ["\128"; "\192\175"; "\226\130"; "\237\160\128"; "\244\144\128\128"; "a\255"]
  @ [
  "alias", equal "2" (evaluate "def size : Bytes -> Nat := Text.length Bytes\ndef main : Nat := size b\"é\"");
  "capture", equal "4" (evaluate "def main : Nat := let text : Bytes := b\"😀\" in let size : prod () -> Nat := fun (u : prod ()) => Text.length Bytes text in size ()");
  "type alias", equal "3" (evaluate "def TextType : Type 0 := Bytes\ndef main : Nat := Text.length TextType b\"abc\"");
  "alternate family", equal "2" (evaluate "mu Octets : Type 0 := | nil : Octets | cons (head : Nat) (tail : Octets) : Octets\ndef main : Nat := Text.length Octets (cons 195 (cons 169 nil))");
  "computed", equal "6" (evaluate "def main : Nat := Text.length Bytes (Text.concat Bytes b\"é\" b\"😀\")");
  "arithmetic", equal "257" (evaluate "def main : Nat := natAdd (Text.length Bytes b\"a\") 256");
  "byte range", refuses "255" (evaluate "def main : Nat := Text.length Bytes (bytesCons 256 bytesNil)");
  "unused byte error", refuses "255" (evaluate "def main : Nat := let unused : Nat := Text.length Bytes (bytesCons 256 bytesNil) in 7");
  "unused UTF-8 error", refuses "UTF-8" (evaluate "def main : Nat := let unused : Nat := Text.length Bytes (bytesCons 128 bytesNil) in 7");
  "wrong runtime value", refuses "byte list" (call V.Unit);
  "wrong family", refuses "byte list" (call (V.of_text "Other" "a"));
  "unsupported layout", refuses "byte list"
    (let* checked = E.check_lanyard "def main : Nat := Text.length Nat 1" in I.run checked);
  "open input type", refuses "closed"
    (let* checked = E.check_lanyard "def main : (0 A : Type 0) -> A -> Nat := fun (0 A : Type 0) (value : A) => Text.length A value" in I.prepare checked);
  "representations", (let* arguments, result, _render, effect = metadata Fun.id Fun.id in
    if arguments = [Rir.TyArc (Rir.TyUnion (Erase.mu_tid "Bytes"))]
       && result = Rir.TyUnion (Rir.Tid "nat") && effect = Lanyard_rust.Effects.Sync
    then Ok () else fail "text input or natural result representation differs");
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
  if List.is_empty failed then Printf.printf "LAN-TEXT-LENGTH OK checks=%d\n" (List.length cases) else exit 1
