(** Explicit URL-encoded fields. Bounds apply before decoding or allocation. *)
open Kanon_kernel
let ( let* ) = Result.bind
let invalid message = Error (Error.Mismatch ("form: " ^ message))
let max_bytes = 8192
let max_fields = 128
let byte_characters = "\000\001\002\003\004\005\006\007\008\009\010\011\012\013\014\015\016\017\018\019\020\021\022\023\024\025\026\027\028\029\030\031\032\033\034\035\036\037\038\039\040\041\042\043\044\045\046\047\048\049\050\051\052\053\054\055\056\057\058\059\060\061\062\063\064\065\066\067\068\069\070\071\072\073\074\075\076\077\078\079\080\081\082\083\084\085\086\087\088\089\090\091\092\093\094\095\096\097\098\099\100\101\102\103\104\105\106\107\108\109\110\111\112\113\114\115\116\117\118\119\120\121\122\123\124\125\126\127\128\129\130\131\132\133\134\135\136\137\138\139\140\141\142\143\144\145\146\147\148\149\150\151\152\153\154\155\156\157\158\159\160\161\162\163\164\165\166\167\168\169\170\171\172\173\174\175\176\177\178\179\180\181\182\183\184\185\186\187\188\189\190\191\192\193\194\195\196\197\198\199\200\201\202\203\204\205\206\207\208\209\210\211\212\213\214\215\216\217\218\219\220\221\222\223\224\225\226\227\228\229\230\231\232\233\234\235\236\237\238\239\240\241\242\243\244\245\246\247\248\249\250\251\252\253\254\255" |> String.to_seq |> List.of_seq
let hex character = match () with
  | () when character >= '0' && character <= '9' -> Ok (Char.code character - Char.code '0')
  | () when character >= 'a' && character <= 'f' -> Ok (Char.code character - Char.code 'a' + 10)
  | () when character >= 'A' && character <= 'F' -> Ok (Char.code character - Char.code 'A' + 10)
  | () -> invalid "invalid percent escape"
let decode text =
  let rec bytes reversed = function
    | [] ->
        let value = String.of_seq (List.to_seq (List.rev reversed)) in
        if String.is_valid_utf_8 value then Ok value else invalid "invalid UTF-8"
    | '+' :: rest -> bytes (' ' :: reversed) rest
    | '%' :: high :: low :: rest ->
        let* high = hex high in let* low = hex low in
        let* character = List.find_opt (fun byte -> Char.code byte = high * 16 + low) byte_characters
          |> Option.to_result ~none:(Error.Mismatch "form: byte out of range") in
        bytes (character :: reversed) rest
    | '%' :: _rest -> invalid "invalid percent escape"
    | character :: rest -> bytes (character :: reversed) rest in
  bytes [] (List.of_seq (String.to_seq text))
let parse body = match () with
  | () when String.length body > max_bytes -> invalid "body exceeds 8192 bytes"
  | () when String.equal body "" -> Ok []
  | () ->
      let segments = String.split_on_char '&' body in
      if List.length segments > max_fields then invalid "body exceeds 128 fields" else
      List.fold_left (fun result field ->
        let* fields = result in
        match String.split_on_char '=' field with
        | [] | [_] -> invalid "field requires name=value"
        | name :: values ->
            let* name = decode name in
            let* value = decode (String.concat "=" values) in
            match () with
            | () when String.equal name "" -> invalid "empty field name"
            | () when List.mem_assoc name fields -> invalid "duplicate field name"
            | () -> Ok ((name, value) :: fields)) (Ok []) segments
      |> Result.map List.rev
let field body name =
  let* fields = parse body in
  List.assoc_opt name fields |> Option.to_result ~none:(Error.Mismatch "form: missing field")

(** Validate strictly before using the pinned Topcoat form deserializer. *)
let runtime = {|
enum LanFormEscape { Ready, High, Low(u8) }
fn lan_form_hex(byte: u8) -> Result<u8, Error> {
    if byte.is_ascii_digit() { Ok(byte - b'0') }
    else if (b'a'..=b'f').contains(&byte) { Ok(byte - b'a' + 10) }
    else if (b'A'..=b'F').contains(&byte) { Ok(byte - b'A' + 10) }
    else { Err(Error::InvalidForm) }
}
fn lan_form_validate_component(text: &str) -> Result<(), Error> {
    text.bytes().try_fold((Vec::new(), LanFormEscape::Ready), |(mut bytes, state), byte| {
        let next = match state {
            LanFormEscape::Ready => {
                if byte == b'%' { LanFormEscape::High }
                else {
                    bytes.push(if byte == b'+' { b' ' } else { byte });
                    LanFormEscape::Ready
                }
            }
            LanFormEscape::High => LanFormEscape::Low(lan_form_hex(byte)?),
            LanFormEscape::Low(high) => {
                bytes.push(high * 16 + lan_form_hex(byte)?);
                LanFormEscape::Ready
            }
        };
        Ok((bytes, next))
    }).and_then(|(bytes, state)| match state {
        LanFormEscape::Ready => String::from_utf8(bytes).map(|_text| ()).map_err(|_error| Error::InvalidForm),
        LanFormEscape::High | LanFormEscape::Low(_) => Err(Error::InvalidForm),
    })
}
fn lan_form_fields(body: &str) -> Result<Vec<(String, String)>, Error> {
    let bounded = if body.len() > |} ^ string_of_int max_bytes ^ {| { Err(Error::InvalidForm) } else { Ok(()) };
    bounded?;
    if !body.is_empty() {
        body.split('&').try_fold(0usize, |count, field| {
            if count >= |} ^ string_of_int max_fields ^ {| { Err(Error::InvalidForm) }
            else {
                field.split_once('=').ok_or(Error::InvalidForm).and_then(|(key, value)| {
                    lan_form_validate_component(key)?;
                    lan_form_validate_component(value)?;
                    Ok(count + 1)
                })
            }
        })?;
    }
    let fields = topcoat::router::content::Form::<Vec<(String, String)>>::from_bytes(body.as_bytes())
        .map_err(|_error| Error::InvalidForm)?.0;
    fields.iter().try_fold(Vec::<&str>::new(), |mut seen, (key, _value)| {
        if key.is_empty() || seen.contains(&key.as_str()) { Err(Error::InvalidForm) }
        else { seen.push(key); Ok(seen) }
    })?;
    Ok(fields)
}
fn lan_form_field(body: &str, name: &str) -> Result<String, Error> {
    lan_form_fields(body)?.into_iter().find(|(key, _value)| key == name)
        .map(|(_key, value)| value).ok_or(Error::InvalidForm)
}
|}
