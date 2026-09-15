(** A scripted origin-form request and an empty redirect response. *)
open Run_value

let max_uri_bytes = 8192
let hex character =
  (character >= '0' && character <= '9') || (character >= 'a' && character <= 'f')
  || (character >= 'A' && character <= 'F')
let uri_character character =
  (character >= 'a' && character <= 'z') || (character >= 'A' && character <= 'Z')
  || (character >= '0' && character <= '9') || String.contains "-._~!$&'()*+,;=:@/?" character

let uri text =
  if String.length text > max_uri_bytes then invalid "request URI exceeds 8192 bytes"
  else if not (String.starts_with ~prefix:"/" text)
    || String.starts_with ~prefix:"//" text then
    invalid "request URI requires an origin-form path beginning with one slash"
  else
    let rec scan = function
      | [] -> Ok text
      | '%' :: high :: low :: rest when hex high && hex low -> scan rest
      | '%' :: _rest -> invalid "request URI has an invalid percent escape"
      | character :: rest when uri_character character -> scan rest
      | _character :: _rest -> invalid "request URI has an invalid character" in
    scan (List.of_seq (String.to_seq text))

let response = function
  | See_other location ->
      let* location = uri location in
      Ok ("HTTP/1.1 303 See Other\r\nLocation: " ^ location ^
          "\r\nContent-Length: 0\r\n\r\n")
  | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ | Database _
  | Context _ | Uri _ -> invalid "request handler did not return SeeOther"
