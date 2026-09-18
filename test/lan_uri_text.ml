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
let contains text needle = let limit = String.length text - String.length needle in
  List.init (max 0 (limit + 1)) Fun.id
  |> List.exists (fun index -> Seq.equal Char.equal (String.to_seq needle)
      (String.to_seq text |> Seq.drop index |> Seq.take (String.length needle)))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected URI text"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked = E.check_lanyard (base ^ "def main : Uri -> Bytes := Uri.to_text Bytes")
let context = let* checked = checked in I.prepare checked
let call value = let* context = context in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value] |> Result.map fst
let convert uri = let* value = call (V.Uri uri) in V.text ~what:"URI text" "Bytes" value
let evaluate source arguments =
  let* checked = E.check_lanyard (base ^ source) in
  let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments |> Result.map fst
let operations =
  let* checked = checked in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  T.catalog specialized.specialized instances
let metadata change_row change_entry =
  let* operations = operations in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Uri.to_text") operations
    |> Option.to_result ~none:(Error.Unbound "Uri.to_text") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Uri.to_text" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let paths = ["/"; "/todos"; "/todos?"; "/a/b?x=1&x=2"; "/a??b";
  "/%00%0d%0A"; "/%c3%a9"; "/%C3%A9"; "/-._~!$&'()*+,;=:@/?";
  "/a//b"; "/a/../b"; "/" ^ String.make 8191 'a']
let bad_paths = [""; "relative"; "https://example.com/"; "//example.com/";
  "/space here"; "/#fragment"; "/\\"; "/[x]"; "/\r\nLocation: /other";
  "/\000"; "/\127"; "/caf\195\169"; "/%"; "/%0"; "/%GG"; "/%0x";
  "/" ^ String.make 8192 'a']
let tests = List.mapi (fun index path -> "accepted path " ^ string_of_int index,
    equal path (convert path)) paths
  @ List.mapi (fun index path -> "refused path " ^ string_of_int index,
    refuses "request URI" (convert path)) bad_paths
  @ [
    "wrong value", refuses "expected a request URI" (call V.Unit);
    "round trip", equal (V.of_text "Bytes" "/a?x=%2f") (evaluate
      "def main : Bytes := Uri.to_text Bytes (Uri.from_text Bytes b\"/a?x=%2f\")" []);
    "captured URI", equal (V.of_text "Bytes" "/next") (evaluate
      "def main : Uri -> Bytes := fun (uri : Uri) => let render : Nat -> Bytes := fun (n : Nat) => Uri.to_text Bytes uri in render 0"
      [V.Uri "/next"]);
    "unused invalid URI", refuses "request URI" (evaluate
      "def main : Uri -> Nat := fun (uri : Uri) => let unused : Bytes := Uri.to_text Bytes uri in 1"
      [V.Uri "//host"]);
    "alternate family", equal (V.of_text "Other" "/next") (evaluate
      "mu Other : Type 0 := | nil : Other | cons (n : Nat) (tail : Other) : Other\ndef main : Uri -> Other := Uri.to_text Other"
      [V.Uri "/next"]);
    "bad output layout", refuses "byte list" (let* program = E.check_lanyard
      "def main : Uri -> Nat := Uri.to_text Nat" in I.prepare program);
    "open output type", refuses "type arguments must be closed" (let* program = E.check_lanyard
      "def main : (0 T : Type 0) -> Uri -> T := fun (0 T : Type 0) (uri : Uri) => Uri.to_text T uri" in I.prepare program);
    "metadata type arguments", refuses "metadata differs" (metadata
      (fun row -> { row with Rir.type_arguments = ["Text", "Nat"] }) Fun.id);
    "metadata effects", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.effects = ["topcoat::Error"] }));
    "metadata schema type", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.kernel_type = "(0 Text : Type 0) -> (uri : Uri) -> Nat" }));
    "metadata quantities", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.quantities = [C.Zero; C.One] }));
    "metadata kind", refuses "schema kind" (metadata Fun.id
      (fun entry -> { entry with C.kind = C.Constant }));
    "synchronous layout", (let* arguments, result, _render, effect = metadata Fun.id Fun.id in
      if arguments = [Rir.TyArc (Rir.TyForeign ("Uri", []))]
        && result = Rir.TyUnion (Erase.mu_tid "Bytes")
        && effect = Lanyard_rust.Effects.Sync
      then Ok () else fail "URI text layout or effect differs");
    "emitted validation", (let* checked = checked in let* code = Lanyard_rust.Model.source checked in
      if contains code "__lan_uri.to_string()" && contains code "lan_uri_validate(&__lan_uri_text)?;"
        && contains code "enum LanUriEscape" && contains code "InvalidUri" && not (contains code ".await")
      then Ok () else fail "URI text emission contract differs")
  ]
let () =
  let failures = List.filter_map (fun (name, result) -> Result.fold ~ok:(fun () -> None)
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) tests in
  if List.is_empty failures then Printf.printf "LAN-URI-TEXT OK checks=%d\n" (List.length tests)
  else (List.iter prerr_endline failures; exit 1)
