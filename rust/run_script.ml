(** One URI per line, with an optional tab and URL-encoded form body. *)
open Kanon_kernel
let ( let* ) = Result.bind
type request = { uri : string; form : string option }
type t = request list
let max_bytes = 1048576
let max_requests = 128
let requests script = script
let invalid message = Error (Error.Mismatch ("request script: " ^ message))

let parse_line line =
  let line = if String.ends_with ~suffix:"\r" line then
      String.to_seq line |> Seq.take (String.length line - 1) |> String.of_seq else line in
  let* uri, form = match String.split_on_char '\t' line with
    | [uri] -> Ok (uri, None)
    | [uri; body] -> Ok (uri, Some body)
    | [] | _ :: _ -> Error (Error.Mismatch "expected URI or URI<TAB>FORM") in
  let* uri = Run_http.uri uri in
  let* _fields = Option.fold ~none:(Ok []) ~some:Form_data.parse form in
  Ok { uri; form }

let parse text =
  let lines = match List.rev (String.split_on_char '\n' text) with
    | "" :: rest -> List.rev rest
    | [] | _ :: _ as reversed -> List.rev reversed in
  match () with
  | () when String.length text > max_bytes -> invalid (Printf.sprintf "exceeds %d bytes" max_bytes)
  | () when List.is_empty lines -> invalid "requires at least one request"
  | () when List.length lines > max_requests -> invalid (Printf.sprintf "exceeds %d requests" max_requests)
  | () ->
    let rec read number reversed = function
      | [] -> Ok (List.rev reversed)
      | line :: rest ->
          let* request = parse_line line |> Result.map_error (fun error ->
            Error.Mismatch (Printf.sprintf "request script line %d: %s" number (Error.to_string error))) in
          read (number + 1) (request :: reversed) rest in
    read 1 [] lines
