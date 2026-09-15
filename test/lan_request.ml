open Kanon_kernel
module I = Lanyard_rust.Interp
module V = Lanyard_rust.Run_value
module H = Lanyard_rust.Run_http
module S = Lanyard_rust.Run_store
let ( let* ) = Result.bind
let check = Kanon_surface.Elab.check_lanyard
let redirect = "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => topcoat.see_other uri"
let run ?steps ?(uri = "/next") source =
  let* checked = check source in I.request ?steps ~uri checked
let equal expected result () =
  let* actual = result in
  if actual = expected then Ok () else Error (Error.Mismatch "unexpected request result")
let contains text needle =
  List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
    String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let refuses needle result () = Result.fold
  ~ok:(fun _value -> Error (Error.Mismatch "expected request refusal"))
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let row name =
  let* checked = check redirect in
  let* constants = Kanon_surface.Lower.catalog checked in
  let* row = List.find_opt (fun (row : Rir.foreign) -> row.schema = name) constants
    |> Option.to_result ~none:(Error.Mismatch "missing request target row") in
  Ok (row, { S.models = []; connections = []; constants })
let invoke name arguments store =
  let* row, catalog = row name in S.foreign catalog row arguments store
let expected = "HTTP/1.1 303 See Other\r\nLocation: /next\r\nContent-Length: 0\r\n\r\n"

let tests = [
  "redirect bytes", equal (V.See_other "/next", expected) (run redirect);
  "closure captures", equal (V.See_other "/next", expected) (run
    "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => let f : Nat -> SeeOther := fun (n : Nat) => topcoat.see_other uri in f 3");
  "linear URI remains checked", refuses "linear binder uri" (run
    "def main : (1 cx : Cx) -> (1 uri : Uri) -> SeeOther := fun (1 cx : Cx) (1 uri : Uri) => let db : Db := topcoat.db cx in topcoat.see_other uri");
  "URI bytes preserved", equal "/a%2Fb?q=x%20y&z=%E2%98%83" (H.uri "/a%2Fb?q=x%20y&z=%E2%98%83");
  "URI boundary", equal ("/" ^ String.make 8191 'a') (H.uri ("/" ^ String.make 8191 'a'));
  "URI size limit", refuses "8192" (H.uri ("/" ^ String.make 8192 'a'));
  "header injection refused", refuses "invalid character" (H.response (V.See_other "/next\r\nInjected:yes"));
  "response type", refuses "did not return SeeOther" (H.response (V.Text "/next"));
  "step bound", refuses "step limit exhausted" (run ~steps:1 redirect);
  "invalid API step bound", refuses "steps must" (run ~steps:0 redirect);
  "excessive API step bound", refuses "steps must" (run ~steps:(I.max_steps + 1) redirect);
  "invalid API URI", refuses "origin-form" (run ~uri:"https://example.test/" redirect);
  "entry parameter order", refuses "Cx -> Uri -> SeeOther" (run
    "def main : Uri -> Cx -> SeeOther := fun (uri : Uri) (cx : Cx) => topcoat.see_other uri");
  "entry result type", refuses "Cx -> Uri -> SeeOther" (run
    "def main : Cx -> Uri -> Uri := fun (cx : Cx) (uri : Uri) => uri");
  "entry arity", refuses "Cx -> Uri -> SeeOther" (run "def main : Nat := 3");
  "context type", refuses "expected a request context" (invoke "topcoat.db" [V.Unit] S.empty);
  "context handle", refuses "unknown database handle" (invoke "topcoat.db" [V.Context 0] S.empty);
  "URI type", refuses "expected a request URI" (invoke "topcoat.see_other" [V.Text "/next"] S.empty);
  "foreign metadata", (fun () ->
    let* row, catalog = row "topcoat.see_other" in
    refuses "foreign metadata differs"
      (S.foreign { catalog with constants = [] } row [V.Uri "/next"] S.empty) ());
  "foreign arity", refuses "foreign argument count" (invoke "topcoat.see_other" [] S.empty);
  "context aliases", (fun () ->
    let cx, store = S.context [] S.empty in
    let* first, store = invoke "topcoat.db" [cx] store in
    let* second, _store = invoke "topcoat.db" [cx] store in equal first (Ok second) ());
  "context allocation", (fun () ->
    let first, store = S.context [] S.empty in
    let second, _store = S.context [] store in
    if first <> second then Ok () else Error (Error.Mismatch "contexts share an identity"));
  "same-process isolation", (fun () ->
    let* checked = check ("model Row with | id : Nat end\n" ^
      "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => " ^
      "let db : Db := topcoat.db cx in let ready : prod () := Db.push_schema db in " ^
      "let row : Row := Row.create (tuple (1)) db in topcoat.see_other uri") in
    let* first = I.request ~uri:"/next" checked in
    let* second = I.request ~uri:"/next" checked in equal first (Ok second) ());
]

let () =
  let failures = List.filter_map (fun (name, test) -> Result.fold ~ok:(fun () -> None)
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) (test ())) tests in
  List.iter prerr_endline failures;
  if List.is_empty failures then Printf.printf "LAN-REQUEST OK observations=%d\n" (List.length tests)
  else exit 1
