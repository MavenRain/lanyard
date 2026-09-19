(** Adapt a checked handler to the pinned Topcoat HTTP transport. *)
open Kanon_kernel
let ( let* ) = Result.bind

let runtime = {|
#[derive(Debug)]
enum LanHttpError {
    BadRequest, Body, Timeout, MediaType, Handler(Error), Conversion(topcoat::Error),
}
impl std::fmt::Display for LanHttpError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::BadRequest => f.write_str("invalid request URI, form or body"),
            Self::Body => f.write_str("request body exceeds its limit or cannot be read"),
            Self::Timeout => f.write_str("request body timed out"),
            Self::MediaType => f.write_str("expected application/x-www-form-urlencoded"),
            Self::Handler(error) => std::fmt::Display::fmt(error, f),
            Self::Conversion(error) => std::fmt::Display::fmt(error, f),
        }
    }
}
impl std::error::Error for LanHttpError {}
impl LanHttpError {
    fn status(&self) -> topcoat::router::StatusCode {
        use topcoat::router::StatusCode;
        match self {
            Self::BadRequest => StatusCode::BAD_REQUEST,
            Self::Body => StatusCode::PAYLOAD_TOO_LARGE,
            Self::Timeout => StatusCode::REQUEST_TIMEOUT,
            Self::MediaType => StatusCode::UNSUPPORTED_MEDIA_TYPE,
            Self::Handler(_) | Self::Conversion(_) => StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}

#[derive(Debug)]
enum LanServerError { Database(toasty::Error), Io(std::io::Error) }
impl std::fmt::Display for LanServerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Database(error) => write!(f, "server database: {error}"),
            Self::Io(error) => write!(f, "server I/O: {error}"),
        }
    }
}
impl std::error::Error for LanServerError {}

static LAN_HANDLER_LOCK: tokio::sync::Mutex<()> = tokio::sync::Mutex::const_new(());

fn lan_http_route(cx: &topcoat::context::Cx, body: topcoat::router::Body) -> topcoat::router::RouteFuture<'_> {
    use topcoat::router::response::IntoResponse;
    Box::pin(async move {
        lan_http_handle(cx, body).await.map_or_else(|error| {
            eprintln!("request: {error}");
            error.status().into_response(cx)
        }, Ok)
    })
}
|}

let entry checked address =
  let* context = Interp.prepare checked in
  let* main = Interp.find context "main" in
  let form = match main.params with [_cx; _uri; _body] -> Some "" | [] | _ :: _ -> None in
  let* _body = Interp.request_body context main form in
  let* cx, uri, body = match main.params with
    | [cx; uri] -> Ok (cx, uri, None)
    | [cx; uri; body] ->
        let* family = Text_ops.byte_family body context.families in
        Ok (cx, uri, Some (body, family.family_name))
    | [] | _ :: _ -> Error (Error.Mismatch "HTTP entry point arity") in
  let input_text = Option.fold ~none:[] ~some:(fun (_repr, family) -> [family]) body in
  let models = List.map Model.rust_name context.foreign.models in
  let render effect name =
    let args = [Session_emit.owned cx "cx.clone()"; Session_emit.owned uri "uri"]
      @ Option.fold ~none:[] ~some:(fun (repr, family) ->
          [Session_emit.owned repr (Model.text_from family ^ "(form.to_owned())")]) body in
    runtime ^ {|
async fn lan_http_handle(cx: &topcoat::context::Cx, body: topcoat::router::Body)
    -> Result<topcoat::router::response::Response, LanHttpError> {
    use topcoat::router::{request, response::IntoResponse};
    let uri = request::uri(cx).clone();
    lan_uri_validate(&uri.to_string()).map_err(|_error| LanHttpError::BadRequest)?;
    let bytes = tokio::time::timeout(std::time::Duration::from_secs(5),
        topcoat::router::to_bytes(body, |} ^ string_of_int Form_data.max_bytes ^ {|)).await
        .map_err(|_error| LanHttpError::Timeout)?.map_err(|_error| LanHttpError::Body)?;
    let form = std::str::from_utf8(&bytes).map_err(|_error| LanHttpError::BadRequest)?;
|}
    ^ Option.fold ~none:"    if !form.is_empty() { return Err(LanHttpError::BadRequest); }\n"
       ~some:(fun _body -> {|
    if !form.is_empty() {
        if request::method(cx) != topcoat::router::Method::POST {
            return Err(LanHttpError::BadRequest);
        }
        let content_type = request::headers(cx).get(topcoat::router::header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok())
            .and_then(|value| value.split(';').next().map(|media| media.trim().to_ascii_lowercase()));
        if content_type.as_deref() != Some("application/x-www-form-urlencoded") {
            return Err(LanHttpError::MediaType);
        }
    }
    lan_form_fields(form).map_err(|_error| LanHttpError::BadRequest)?;
|}) body
    ^ "    let _guard = LAN_HANDLER_LOCK.lock().await;\n"
    ^ "    let value = " ^ name ^ "(" ^ String.concat ", " args ^ ")" ^ Effects.await effect
    ^ ".map_err(LanHttpError::Handler)?;\n"
    ^ "    value.into_response(cx).map_err(LanHttpError::Conversion)\n}\n"
    ^ "\nasync fn lan_server() -> Result<(), LanServerError> {\n"
    ^ "    use topcoat::router::{Method, RouteFn, Router};\n"
    ^ "    let db = toasty::Db::builder()"
    ^ (if List.is_empty models then "" else ".models(toasty::models!(" ^ String.concat ", " models ^ "))")
    ^ ".connect(\"sqlite::memory:\").await.map_err(LanServerError::Database)?;\n"
    ^ "    let router = Router::builder().app_context(db)\n"
    ^ "        .route(RouteFn::new(vec![Method::GET, Method::POST], \"/\", lan_http_route))\n"
    ^ "        .route(RouteFn::new(vec![Method::GET, Method::POST], \"/{*path}\", lan_http_route)).build();\n"
    ^ "    let address = std::net::SocketAddrV4::new(std::net::Ipv4Addr::LOCALHOST, "
    ^ string_of_int (Listen_address.port address) ^ ");\n"
    ^ "    let listener = tokio::net::TcpListener::bind(address).await.map_err(LanServerError::Io)?;\n"
    ^ "    eprintln!(\"LANYARD-LISTEN http://{}\", listener.local_addr().map_err(LanServerError::Io)?);\n"
    ^ "    topcoat::serve(listener, router).await.map_err(LanServerError::Io)\n}\n"
    ^ "\n#[tokio::main(flavor = \"current_thread\")]\nasync fn main() {\n"
    ^ "    if let Err(error) = lan_server().await {\n        eprintln!(\"{error}\");\n        std::process::exit(1);\n    }\n}\n" in
  Ok (Emit.Http_listener { parameters = main.params; response = main.result; render }, input_text)
