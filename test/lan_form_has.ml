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
  Seq.init (max 0 (String.length text - String.length needle + 1)) Fun.id
  |> Seq.exists (fun index -> String.equal needle
    (String.to_seq text |> Seq.drop index |> Seq.take (String.length needle) |> String.of_seq))
let equal expected result = let* actual = result in
  if actual = V.Tag (T.bool_tid, (if expected then 1 else 0), [V.Unit]) then Ok () else fail "unexpected presence"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked = E.check_lanyard (base ^ "def main : Bytes -> Bytes -> Bool := Form.has Bytes")
let call body name =
  let* checked = checked in let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [body; name]
  |> Result.map fst
let has body name = call (V.of_text "Bytes" body) (V.of_text "Bytes" name)
let evaluate source = let* checked = E.check_lanyard (base ^ source) in I.run checked |> Result.map fst
let metadata change_row change_entry =
  let* checked = checked in let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  let* operations = T.catalog specialized.specialized instances in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Form.has") operations
    |> Option.to_result ~none:(Error.Unbound "Form.has") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Form.has" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let good = [
  "", "title", false; "title=", "title", true; "title=x", "other", false;
  "title=other", "other", false; "Title=x", "title", false; "title=x", "", false;
  "%74itle=caf%C3%A9", "title", true; "a+b=x", "a b", true;
  "a%2Bb=x", "a+b", true; "a%252Bb=x", "a%2Bb", true;
  "%E6%97%A5=x", "\230\151\165", true; "a%00b=x", "a\000b", true;
  "first=1&last=", "last", true; "a%26b%3Dc=x", "a&b=c", true ]
let bad = [
  "title", "name=value"; "=value", "empty";
  "title=one&title=two", "duplicate"; "title=one&%74itle=two", "duplicate";
  "title=x&a=1&a=2", "duplicate"; "title=x&", "name=value";
  "title=x&&a=1", "name=value"; "title=x&other=%", "escape";
  "title=%0", "escape"; "title=%GG", "escape";
  "title=x&other=%ff", "UTF-8"; "title=%c0%af", "UTF-8";
  "title=%ed%a0%80", "UTF-8"; "title=%f4%90%80%80", "UTF-8";
  "title=%e2%82", "UTF-8"; "%ff=x&title=ok", "UTF-8" ]
let cases =
  List.mapi (fun index (body, name, expected) -> "presence " ^ string_of_int index, equal expected (has body name)) good
  @ List.concat_map (fun name -> List.mapi (fun index (body, message) ->
      "refused " ^ name ^ " " ^ string_of_int index, refuses message (has body name)) bad) ["title"; "absent"]
  @ [
    "body limit", equal true (has ("title=" ^ String.make 8186 'x') "title");
    "oversize body", refuses "8192" (has ("title=" ^ String.make 8187 'x') "title");
    "field limit", equal true (has (String.concat "&" (List.init 128 (fun i -> "k" ^ string_of_int i ^ "="))) "k127");
    "too many fields", refuses "128" (has (String.concat "&" (List.init 129 (fun i -> "k" ^ string_of_int i ^ "="))) "k0");
    "raw UTF-8", refuses "UTF-8" (has "title=\255" "title");
    "name UTF-8", refuses "UTF-8" (has "title=x" "\255");
    "byte range", refuses "0..255" (call (V.Tag (Erase.mu_tid "Bytes", 1,
      [V.Nat (Bignum.of_int 256); V.of_text "Bytes" ""])) (V.of_text "Bytes" "title"));
    "direct", equal true (evaluate "def main : Bool := Form.has Bytes b\"title=\" b\"title\"");
    "captured", equal false (evaluate ("def main : Bool := let body : Bytes := b\"other=x\" in "
      ^ "let present : Bytes -> Bool := fun (name : Bytes) => Form.has Bytes body name in present b\"title\""));
    "alternate family", equal true (evaluate ("mu Other : Type 0 := | otherNil : Other | otherCons (head : Nat) (tail : Other) : Other\n"
      ^ "def main : Bool := Form.has Other (otherCons 97 (otherCons 61 otherNil)) (otherCons 97 otherNil)"));
    "unused invalid", refuses "escape" (evaluate "def main : Nat := let ignored : Bool := Form.has Bytes b\"title=%\" b\"title\" in 1");
    "evaluation order", refuses "origin-form" (evaluate "def main : Bool := Form.has Bytes (bytesCons 255 bytesNil) (let invalid : Uri := Uri.from_text Bytes b\"//host\" in b\"title\")");
    "unsupported layout", refuses "byte list" (evaluate "def main : Bool := Form.has Nat 0 0");
    "open type", refuses "closed" (let* program = E.check_lanyard (base ^ "def main : (0 A : Type 0) -> A -> A -> Bool := fun (0 A : Type 0) (body : A) (name : A) => Form.has A body name") in I.prepare program);
    "metadata effects", refuses "metadata" (metadata Fun.id (fun row -> { row with effects = [] }));
    "metadata arity", refuses "metadata" (metadata (fun row -> { row with arity = 1 }) Fun.id);
    "metadata type", refuses "metadata" (metadata Fun.id (fun row -> { row with kernel_type = "Nat" }));
    "metadata print", refuses "metadata" (metadata (fun row -> { row with print_rule = "false" }) Fun.id);
    "metadata kind", refuses "kind" (metadata Fun.id (fun row -> { row with kind = C.Constant })) ]
let () =
  let failed = List.filter_map (fun (name, result) ->
    Result.fold ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) cases in
  List.iter prerr_endline failed;
  if List.is_empty failed then Printf.printf "LAN-FORM-HAS OK checks=%d\n" (List.length cases) else exit 1
