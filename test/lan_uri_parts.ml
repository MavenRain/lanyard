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
  |> List.exists (fun index -> Seq.equal Char.equal (String.to_seq needle)
      (String.to_seq text |> Seq.drop index |> Seq.take (String.length needle)))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected URI component"
let refuses needle result = Result.fold ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let evaluate source arguments =
  let* checked = E.check_lanyard (base ^ source) in
  let* context = I.prepare checked in
  I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" arguments |> Result.map fst
let cases = [
  "/", "/", ""; "/todos", "/todos", ""; "/todos?", "/todos", "";
  "/todos?filter=done", "/todos", "filter=done";
  "/?", "/", ""; "/??x?y", "/", "?x?y";
  "/a%3fb?x=%3F%26+&y=%2f", "/a%3fb", "x=%3F%26+&y=%2f";
  "/a//b/../c?x=1&x=2", "/a//b/../c", "x=1&x=2";
  "/%C3%A9?name=%c3%a9", "/%C3%A9", "name=%c3%a9";
  "/%00?x=%FF", "/%00", "x=%FF";
  "/-._~!$&'()*+,;=:@/?/?:@", "/-._~!$&'()*+,;=:@/", "/?:@";
  "/" ^ String.make 8191 'a', "/" ^ String.make 8191 'a', "";
  "/?" ^ String.make 8190 'b', "/", String.make 8190 'b'
]
let invalid = [""; "relative"; "https://example.com/a?q=x"; "//host/a?x";
  "/bad%?q=ok"; "/ok?q=%"; "/ok?q=%0"; "/ok?q=%GG"; "/#fragment";
  "/ok?q=#fragment"; "/a\\b?q=ok"; "/ok?q=\\"; "/space here?q=ok";
  "/ok?q=space here"; "/ok?q=\r\n"; "/ok?q=\000"; "/ok?q=\127";
  "/caf\195\169?q=ok"; "/ok?q=caf\195\169"; "/?" ^ String.make 8191 'a']
let tests_for part =
  let schema = "Uri." ^ part in
  let main = "def main : Uri -> Bytes := " ^ schema ^ " Bytes" in
  let checked = E.check_lanyard (base ^ main) in
  let context = let* checked = checked in I.prepare checked in
  let call value = let* context = context in
    I.call context 0 { I.steps = I.default_steps; store = S.empty } "main" [value] |> Result.map fst in
  let convert uri = let* value = call (V.Uri uri) in V.text ~what:"URI component" "Bytes" value in
  let expected path query = if String.equal part "path" then path else query in
  let metadata change_row change_entry =
    let* checked = checked in
    let* specialized = L.specialize checked in
    let* instances = L.text_operations specialized in
    let* operations = T.catalog specialized.specialized instances in
    let* operation = List.find_opt (fun (text : T.t) -> text.row.schema = schema) operations
      |> Option.to_result ~none:(Error.Unbound schema) in
    let entries = List.map (fun (entry : C.entry) ->
      if entry.name = schema then change_entry entry else entry) C.entries in
    T.foreign_call entries operations (change_row operation.row) in
  List.mapi (fun index (uri, path, query) -> part ^ " accepted " ^ string_of_int index,
    equal (expected path query) (convert uri)) cases
  @ List.mapi (fun index uri -> part ^ " refused " ^ string_of_int index,
    refuses "request URI" (convert uri)) invalid
  @ [
    part ^ " wrong value", refuses "expected a request URI" (call V.Unit);
    part ^ " unused invalid", refuses "request URI" (evaluate
      ("def main : Uri -> Nat := fun (uri : Uri) => let unused : Bytes := " ^ schema ^ " Bytes uri in 1")
      [V.Uri "/ok?q=%GG"]);
    part ^ " roundtrip", equal (V.of_text "Bytes" (expected "/a" "x=%2f")) (evaluate
      ("def main : Bytes := " ^ schema ^ " Bytes (Uri.from_text Bytes b\"/a?x=%2f\")") []);
    part ^ " alias and capture", equal (V.of_text "Bytes" (expected "/a" "x=1")) (evaluate
      ("def alias : Uri -> Bytes := " ^ schema ^ " Bytes\n"
       ^ "def main : Uri -> Bytes := fun (uri : Uri) => let closure : Nat -> Bytes := fun (n : Nat) => alias uri in closure 0")
      [V.Uri "/a?x=1"]);
    part ^ " alternate family", equal (V.of_text "Other" (expected "/a" "x=1")) (evaluate
      ("mu Other : Type 0 := | nil : Other | cons (n : Nat) (tail : Other) : Other\n"
       ^ "def main : Uri -> Other := " ^ schema ^ " Other") [V.Uri "/a?x=1"]);
    part ^ " invalid layout", refuses "byte list" (let* program = E.check_lanyard
      ("def main : Uri -> Nat := " ^ schema ^ " Nat") in I.prepare program);
    part ^ " open output", refuses "type arguments must be closed" (let* program = E.check_lanyard
      ("def main : (0 T : Type 0) -> Uri -> T := fun (0 T : Type 0) (uri : Uri) => " ^ schema ^ " T uri") in I.prepare program);
    part ^ " metadata type argument", refuses "metadata differs" (metadata
      (fun row -> { row with Rir.type_arguments = ["Text", "Nat"] }) Fun.id);
    part ^ " metadata effects", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.effects = ["topcoat::Error"] }));
    part ^ " metadata type", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.kernel_type = "(0 Text : Type 0) -> (uri : Uri) -> Nat" }));
    part ^ " metadata quantity", refuses "schema metadata" (metadata Fun.id
      (fun entry -> { entry with C.quantities = [C.Zero; C.One] }));
    part ^ " metadata kind", refuses "schema kind" (metadata Fun.id
      (fun entry -> { entry with C.kind = C.Constant }));
    part ^ " layout", (let* arguments, result, _render, effect = metadata Fun.id Fun.id in
      if arguments = [Rir.TyArc (Rir.TyForeign ("Uri", []))]
        && result = Rir.TyUnion (Erase.mu_tid "Bytes") && effect = Lanyard_rust.Effects.Sync
      then Ok () else fail "URI component layout differs")
  ]
let tests = List.concat_map tests_for ["path"; "query"]
let () =
  let failures = List.filter_map (fun (name, result) -> Result.fold ~ok:(fun () -> None)
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) tests in
  if List.is_empty failures then Printf.printf "LAN-URI-PARTS OK checks=%d\n" (List.length tests)
  else (List.iter prerr_endline failures; exit 1)
