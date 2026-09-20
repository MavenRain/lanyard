type t = Path of string

let parse ~directory text =
  match () with
  | () when text = "" || String.contains text '\000' || not (String.is_valid_utf_8 text)
      || Filename.is_relative directory || not (String.is_valid_utf_8 directory)
      || String.contains directory '\000' ->
      Error (Kanon_kernel.Error.Mismatch "database needs a nonempty UTF-8 file path")
  | () -> Ok (Path (if Filename.is_relative text then Filename.concat directory text else text))

let rust_string (Path text) =
  let escape character = match () with
    | () when character = '"' -> "\\\""
    | () when character = '\\' -> "\\\\"
    | () when Char.code character < 32 || Char.code character = 127 ->
        Printf.sprintf "\\x%02x" (Char.code character)
    | () -> String.make 1 character in
  "\"" ^ (String.to_seq text |> Seq.map escape |> List.of_seq |> String.concat "") ^ "\""
