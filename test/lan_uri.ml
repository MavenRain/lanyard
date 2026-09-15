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
  Seq.init (if limit >= 0 then limit + 1 else 0) (fun index -> index)
  |> Seq.exists (fun index -> String.equal needle (String.sub text index (String.length needle)))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected URI result"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let checked = E.check_lanyard (base ^ "def main : Bytes -> Uri := Uri.from_text Bytes")
let context = let* checked = checked in I.prepare checked
let call value = let* context = context in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value] |> Result.map fst
let convert text = call (V.of_text "Bytes" text)
let evaluate source =
  let* checked = E.check_lanyard (base ^ source) in
  let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [] |> Result.map fst
let operations =
  let* checked = checked in
  let* specialized = L.specialize checked in
  let* instances = L.text_operations specialized in
  T.catalog specialized.specialized instances
let metadata change_row change_entry =
  let* operations = operations in
  let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = "Uri.from_text") operations
    |> Option.to_result ~none:(Error.Unbound "Uri.from_text") in
  let entries = List.map (fun (entry : C.entry) ->
    if entry.name = "Uri.from_text" then change_entry entry else entry) C.entries in
  T.foreign_call entries operations (change_row operation.row)
let paths = ["/"; "/todos"; "/a/b?x=1&x=2"; "/a??b"; "/%00%0d%0A";
  "/%c3%a9"; "/-._~!$&'()*+,;=:@/?"; "/a//b"; "/" ^ String.make 8191 'a']
let bad_paths = [""; "relative"; "https://example.com/"; "//example.com/";
  "/space here"; "/#fragment"; "/\\"; "/[x]"; "/\r\nLocation: /other";
  "/\000"; "/\127"; "/caf\195\169"; "/%"; "/%0"; "/%GG"; "/%0x";
  "/" ^ String.make 8192 'a']
let tests = List.mapi (fun index path -> "accepted path " ^ string_of_int index,
    equal (V.Uri path) (convert path)) paths
  @ List.mapi (fun index path -> "refused path " ^ string_of_int index,
    refuses "request URI" (convert path)) bad_paths
  @ [
    "direct call", equal (V.Uri "/") (evaluate "def main : Uri := Uri.from_text Bytes b\"/\"");
    "alias call", equal (V.Uri "/next") (evaluate
      "def parse : Bytes -> Uri := Uri.from_text Bytes\ndef main : Uri := parse b\"/next\"");
    "captured call", equal (V.Uri "/next") (evaluate
      "def main : Uri := let path : Bytes := b\"/next\" in let go : Nat -> Uri := fun (n : Nat) => Uri.from_text Bytes path in go 0");
    "unused invalid URI", refuses "request URI" (evaluate
      "def main : Nat := let unused : Uri := Uri.from_text Bytes b\"//host\" in 1");
    "invalid UTF-8", refuses "invalid UTF-8" (convert "/\255");
    "byte range", refuses "outside 0..255" (evaluate
      "def main : Uri := Uri.from_text Bytes (bytesCons 256 bytesNil)");
    "bad layout", refuses "byte list" (let* program = E.check_lanyard
      "def main : Uri := Uri.from_text Nat 1" in I.prepare program);
    "open text type", refuses "type arguments must be closed" (let* program = E.check_lanyard
      "def main : (0 T : Type 0) -> T -> Uri := fun (0 T : Type 0) (x : T) => Uri.from_text T x" in I.prepare program);
    "metadata type arguments", refuses "metadata differs" (metadata
      (fun row -> { row with Rir.type_arguments = ["Text", "Nat"] }) Fun.id);
    "metadata effects", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.effects = [] }));
    "metadata schema type", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.kernel_type = "(0 Text : Type 0) -> (text : Text) -> Nat" }));
    "metadata quantities", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.quantities = [C.Zero; C.One] }));
    "metadata kind", refuses "schema kind" (metadata Fun.id
      (fun entry -> { entry with C.kind = C.Constant }));
    "synchronous result", (let* arguments, result, _render, effect = metadata Fun.id Fun.id in
      if List.length arguments = 1 && result = Rir.TyForeign ("Uri", []) && effect = Lanyard_rust.Effects.Sync
      then Ok () else fail "URI layout or effect differs");
    "emitted validation", (let* checked = checked in let* code = Lanyard_rust.Model.source checked in
      if contains code "lan_uri_validate(&__lan_text)?;" && contains code "parse::<topcoat::router::Uri>()"
        && contains code "enum LanUriEscape" && contains code "InvalidUri"
        && contains code ("value.len() > " ^ string_of_int Lanyard_rust.Run_http.max_uri_bytes)
        && not (contains code ".await")
      then Ok () else fail "URI emission contract differs")
  ]
let () =
  let failures = List.filter_map (fun (name, result) -> Result.fold ~ok:(fun () -> None)
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) tests in
  if List.is_empty failures then Printf.printf "LAN-URI OK checks=%d\n" (List.length tests)
  else (List.iter prerr_endline failures; exit 1)
