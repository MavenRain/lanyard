(** A checked script becomes a finite native entry point. Each request uses
    the same private database, and only a complete transcript is published. *)
open Kanon_kernel
let ( let* ) = Result.bind
let invalid message = Error (Error.Mismatch ("Rust request session: " ^ message))

let literal text =
  let character c = match () with
    | () when Char.equal c '"' -> "\\\""
    | () when Char.equal c '\\' -> "\\\\"
    | () when Char.code c < 32 || Char.code c = 127 -> Printf.sprintf "\\u{%x}" (Char.code c)
    | () -> String.make 1 c in
  "\"" ^ (String.to_seq text |> Seq.map character |> List.of_seq |> String.concat "") ^ "\""

let owned repr code = match repr with
  | Rir.TyArc _ -> "Arc::new(" ^ code ^ ")"
  | Rir.TyI31 | Rir.TyStruct _ | Rir.TyUnion _ | Rir.TyFunc _ | Rir.TyThunk _ | Rir.TyForeign _ -> code

let runtime = {|
#[derive(Debug)]
struct LanRequestNumber(usize);

#[derive(Debug)]
enum LanRequestError {
    Handler(Error), Conversion(topcoat::Error), Task(tokio::task::JoinError),
    Uri, Body, Response, Utf8(std::str::Utf8Error),
}
impl std::fmt::Display for LanRequestError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Handler(error) => std::fmt::Display::fmt(error, f),
            Self::Conversion(error) => std::fmt::Display::fmt(error, f),
            Self::Task(error) => std::fmt::Display::fmt(error, f),
            Self::Uri => f.write_str("invalid request URI"),
            Self::Body => f.write_str("cannot read response body"),
            Self::Response => f.write_str("unsupported response status or headers"),
            Self::Utf8(error) => std::fmt::Display::fmt(error, f),
        }
    }
}
impl std::error::Error for LanRequestError {}

#[derive(Debug)]
enum LanSessionError {
    Database(toasty::Error), Request(LanRequestNumber, LanRequestError), Output(std::io::Error),
}
impl std::fmt::Display for LanSessionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Database(error) => write!(f, "session database: {error}"),
            Self::Request(number, error) => write!(f, "request {}: {error}", number.0),
            Self::Output(error) => write!(f, "session output: {error}"),
        }
    }
}
impl std::error::Error for LanSessionError {}

async fn lan_session_response<T: topcoat::router::response::IntoResponse>(value: T, cx: &topcoat::context::Cx) -> Result<String, LanRequestError> {
    let (parts, body) = value.into_response(cx).map_err(LanRequestError::Conversion)?.into_parts();
    if parts.status == topcoat::router::StatusCode::SEE_OTHER {
        let location = parts.headers.get(topcoat::router::header::LOCATION)
            .and_then(|value| value.to_str().ok()).ok_or(LanRequestError::Response)?;
        Ok(format!("HTTP/1.1 303 See Other\r\nLocation: {location}\r\nContent-Length: 0\r\n\r\n"))
    } else if parts.status == topcoat::router::StatusCode::OK {
        let content_type = parts.headers.get(topcoat::router::header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok()).ok_or(LanRequestError::Response)?;
        let bytes = topcoat::router::to_bytes(body, usize::MAX).await.map_err(|_error| LanRequestError::Body)?;
        let text = std::str::from_utf8(&bytes).map_err(LanRequestError::Utf8)?;
        Ok(format!("HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {}\r\n\r\n{text}", bytes.len()))
    } else {
        Err(LanRequestError::Response)
    }
}
|}

let entry checked script =
  let* context = Interp.prepare checked in
  let* main = Interp.find context "main" in
  let* arguments = Rules.all_ok (List.mapi (fun index (request : Run_script.request) ->
    let* _body = Interp.request_body context main request.form |> Result.map_error (fun error ->
      Error.Mismatch (Printf.sprintf "request %d: %s" (index + 1) (Error.to_string error))) in
    let* () = Option.fold ~none:(Ok ()) ~some:(fun text ->
      if String.is_valid_utf_8 text then Ok ()
      else invalid (Printf.sprintf "request %d: form body is not valid UTF-8" (index + 1)))
      request.Run_script.form in
    match main.params with
    | [cx; uri] -> Ok (cx, uri, None, request)
    | [cx; uri; body] ->
        let* family = Text_ops.byte_family body context.families in
        Ok (cx, uri, Some (body, family.family_name), request)
    | [] | _ :: _ -> invalid "entry point arity") (Run_script.requests script)) in
  let input_text = List.filter_map (fun (_cx, _uri, body, _request) -> Option.map snd body) arguments
    |> List.sort_uniq String.compare in
  let models = List.map Model.rust_name context.foreign.models in
  let render effect name =
    let request index (cx, uri, body, request) =
      let form = Option.fold ~none:[] ~some:(fun (repr, family) ->
        let text = Option.value ~default:"" request.Run_script.form in
        [owned repr (Model.text_from family ^ "(" ^ literal text ^ ".to_owned())")]) body in
      let args = [owned cx "request_cx.clone()"; owned uri "uri"] @ form in
      "    let request_cx = cx.clone();\n"
      ^ "    let response_" ^ string_of_int index ^ " = tokio::spawn(async move {\n"
      ^ "        let uri = " ^ literal request.uri ^ ".parse::<topcoat::router::Uri>().map_err(|_error| LanRequestError::Uri)?;\n"
      ^ "        let value = " ^ name ^ "(" ^ String.concat ", " args ^ ")" ^ Effects.await effect
      ^ ".map_err(LanRequestError::Handler)?;\n"
      ^ "        lan_session_response(value, &request_cx).await\n"
      ^ "    }).await.map_err(LanRequestError::Task).and_then(std::convert::identity)\n"
      ^ "        .map_err(|error| LanSessionError::Request(LanRequestNumber(" ^ string_of_int (index + 1) ^ "), error))?;\n" in
    runtime ^ "\nasync fn lan_session() -> Result<(), LanSessionError> {\n"
    ^ "    let db = toasty::Db::builder()"
    ^ (if List.is_empty models then "" else ".models(toasty::models!(" ^ String.concat ", " models ^ "))")
    ^ ".connect(\"sqlite::memory:\").await.map_err(LanSessionError::Database)?;\n"
    ^ "    let cx = topcoat::context::CxTestBuilder::new().app_context(db).build();\n"
    ^ String.concat "" (List.mapi request arguments)
    ^ "    let transcript = [" ^ String.concat ", " (List.mapi (fun index _request -> "response_" ^ string_of_int index) arguments) ^ "].concat();\n"
    ^ "    std::io::Write::write_all(&mut std::io::stdout().lock(), transcript.as_bytes()).map_err(LanSessionError::Output)\n}\n"
    ^ "\n#[tokio::main(flavor = \"current_thread\")]\nasync fn main() {\n"
    ^ "    if let Err(error) = lan_session().await {\n        eprintln!(\"{error}\");\n        std::process::exit(1);\n    }\n}\n" in
  Ok (Emit.Scripted_requests { parameters = main.params; response = main.result; render }, input_text)
