open Kanon_kernel
module I = Lanyard_rust.Interp
module S = Lanyard_rust.Run_script
module H = Lanyard_rust.Run_http
let ( let* ) = Result.bind
let redirect = "def main : Cx -> Uri -> SeeOther := fun (cx : Cx) (uri : Uri) => topcoat.see_other uri"
let run ?steps text source =
  let* script = S.parse text in
  let* checked = Kanon_surface.Elab.check_lanyard source in
  I.session ?steps script checked
let equal expected result () =
  let* actual = result in
  if actual = expected then Ok () else Error (Error.Mismatch "unexpected session result")
let contains text needle =
  let width = String.length needle in
  let rec walk sequence = match sequence () with
    | Seq.Nil -> width = 0
    | Seq.Cons (_head, tail) as node ->
        String.of_seq (Seq.take width (fun () -> node)) = needle || walk tail in
  walk (String.to_seq text)
let refuses needle result () = Result.fold
  ~ok:(fun _value -> Error (Error.Mismatch "expected session refusal"))
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let parsed text = S.parse text |> Result.map S.requests
let request uri form : S.request = { uri; form }
let responses paths = paths |> List.fold_left (fun result path ->
  let* reversed = result in
  let* text = H.response (Lanyard_rust.Run_value.See_other path) in
  Ok (text :: reversed)) (Ok []) |> Result.map (fun reversed -> String.concat "" (List.rev reversed))
let maximum_script = String.concat "\n"
  (("/" ^ String.make 8191 'a') :: List.init 127 (fun _index -> "/" ^ String.make 8190 'b'))

let tests = [
  "single without newline", equal [request "/" None] (parsed "/");
  "final newline", equal [request "/" None] (parsed "/\n");
  "CRLF", equal [request "/a" None; request "/b" (Some "x=y")] (parsed "/a\r\n/b\tx=y\r\n");
  "explicit empty body", equal [request "/" (Some "")] (parsed "/\t\n");
  "percent spelling", equal [request "/a%2fb??x=y" (Some "x=%09%0A%0D")] (parsed "/a%2fb??x=y\tx=%09%0A%0D");
  "empty script", refuses "at least one" (parsed "");
  "blank line", refuses "line 2" (parsed "/a\n\n/b");
  "second final newline", refuses "line 2" (parsed "/a\n\n");
  "extra tab", refuses "URI<TAB>FORM" (parsed "/\tx=y\tz=w");
  "missing URI", refuses "origin-form" (parsed "\tx=y");
  "absolute URI", refuses "origin-form" (parsed "https://example.test/");
  "invalid URI escape", refuses "percent escape" (parsed "/%xx");
  "invalid URI character", refuses "invalid character" (parsed "/a b");
  "raw CR in URI", refuses "invalid character" (parsed "/a\rb");
  "invalid form escape", refuses "percent escape" (parsed "/\tx=%xy");
  "duplicate form field", refuses "duplicate" (parsed "/\tx=1&x=2");
  "invalid form UTF8", refuses "UTF-8" (parsed "/\tx=%FF");
  "URI byte bound", refuses "8192" (parsed ("/" ^ String.make 8192 'a'));
  "body byte bound", refuses "8192" (parsed ("/\tx=" ^ String.make 8191 'a'));
  "request count boundary", equal 128 (parsed (String.concat "\n" (List.init 128 (fun _index -> "/"))) |> Result.map List.length);
  "request count bound", refuses "128 requests" (parsed (String.concat "\n" (List.init 129 (fun _index -> "/"))));
  "script byte boundary", equal 128 (parsed maximum_script |> Result.map List.length);
  "script byte bound", refuses "1048576 bytes" (parsed (maximum_script ^ "x"));
  "ordered transcript", (fun () -> let* expected = responses ["/first"; "/second"; "/last"] in
    equal expected (run "/first\n/second\n/last" redirect) ());
  "single request budget", (fun () -> let* expected = responses ["/"] in
    equal expected (run ~steps:32 "/" redirect) ());
  "aggregate step budget", refuses "step limit exhausted" (run ~steps:32
    (String.concat "\n" (List.init 128 (fun _index -> "/"))) redirect);
  "invalid step budget", refuses "steps must" (run ~steps:0 "/" redirect);
  "excessive step budget", refuses "steps must" (run ~steps:(I.max_steps + 1) "/" redirect);
  "later shape mismatch", refuses "request 2:" (run "/first\n/second\t" redirect);
  "entry result type", refuses "Cx -> Uri" (run "/" "def main : Cx -> Uri -> Uri := fun (cx : Cx) (uri : Uri) => uri");
]

let () =
  let failures = List.filter_map (fun (name, test) ->
    Result.fold ~ok:(fun () -> None)
      ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) (test ())) tests in
  if List.is_empty failures then Printf.printf "LAN-SESSION OK checks=%d\n" (List.length tests)
  else (List.iter prerr_endline failures; exit 1)
