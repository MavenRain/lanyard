(** Values of the erased IR. Sharing has no observable identity here. *)
open Kanon_kernel
let ( let* ) = Result.bind
let invalid text = Error (Error.Mismatch ("run: " ^ text))
let refuse text = Error (Error.Not_yet ("run: " ^ text))
type t =
  | Nat of Bignum.t
  | Text of string
  | Unit
  | Product of Rir.tid * t list
  | Tag of Rir.tid * int * t list
  | Closure of Rir.fid * int * t list
  | Database of int
  | Context of int
  | Uri of string
  | See_other of string

let rec at index = function
  | [] -> invalid "value index out of bounds"
  | value :: _rest when index = 0 -> Ok value
  | _value :: rest when index > 0 -> at (index - 1) rest
  | _value :: _rest -> invalid "negative value index"

let rec zip left right = match left, right with
  | [], [] -> Ok []
  | left :: lefts, right :: rights ->
      let* rest = zip lefts rights in Ok ((left, right) :: rest)
  | [], _ :: _ | _ :: _, [] -> invalid "model field count"

let natural = function
  | Nat number when Bignum.sign number >= 0 -> Ok number
  | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ | Database _
  | Context _ | Uri _ | See_other _ ->
      invalid "expected a natural number"

let scalar_nat value =
  let* number = natural value in
  (* Compare decimal lengths without narrowing to a machine integer. *)
  let text = Bignum.to_string number in
  if String.length text < 19 ||
     (String.length text = 19 && String.compare text "9223372036854775807" <= 0)
  then Ok number else invalid "model integer outside i64 range"

let boolean = function
  | Tag (tid, tag, [Unit]) when Rir.TyUnion tid = Model.bool_repr && (tag = 0 || tag = 1) ->
      Ok (tag = 1)
  | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ | Database _
  | Context _ | Uri _ | See_other _ ->
      invalid "expected a two-unit Boolean"

(* A total byte lookup avoids a partial integer-to-character conversion. *)
let byte_characters = (
  "\000\001\002\003\004\005\006\007\008\009\010\011\012\013\014\015\016\017\018\019\020\021\022\023\024\025\026\027\028\029\030\031" ^
  "\032\033\034\035\036\037\038\039\040\041\042\043\044\045\046\047\048\049\050\051\052\053\054\055\056\057\058\059\060\061\062\063" ^
  "\064\065\066\067\068\069\070\071\072\073\074\075\076\077\078\079\080\081\082\083\084\085\086\087\088\089\090\091\092\093\094\095" ^
  "\096\097\098\099\100\101\102\103\104\105\106\107\108\109\110\111\112\113\114\115\116\117\118\119\120\121\122\123\124\125\126\127" ^
  "\128\129\130\131\132\133\134\135\136\137\138\139\140\141\142\143\144\145\146\147\148\149\150\151\152\153\154\155\156\157\158\159" ^
  "\160\161\162\163\164\165\166\167\168\169\170\171\172\173\174\175\176\177\178\179\180\181\182\183\184\185\186\187\188\189\190\191" ^
  "\192\193\194\195\196\197\198\199\200\201\202\203\204\205\206\207\208\209\210\211\212\213\214\215\216\217\218\219\220\221\222\223" ^
  "\224\225\226\227\228\229\230\231\232\233\234\235\236\237\238\239\240\241\242\243\244\245\246\247\248\249\250\251\252\253\254\255"
  ) |> String.to_seq |> List.of_seq

let text ?(what = "model text") family value =
  let expected = Erase.mu_tid family in
  let rec bytes reversed = function
    | Tag (tid, 0, []) when tid = expected ->
        let text = String.of_seq (List.to_seq (List.rev reversed)) in
        if String.is_valid_utf_8 text then Ok text else invalid ("invalid UTF-8 in " ^ what)
    | Tag (tid, 1, [head; tail]) when tid = expected ->
        let* number = natural head in
        let* byte = Bignum.to_int number
          |> Option.to_result ~none:(Error.Mismatch "run: model byte outside 0..255") in
        if byte > 255 then invalid "model byte outside 0..255"
        else
          let* character = at byte byte_characters in
          bytes (character :: reversed) tail
    | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ | Database _
    | Context _ | Uri _ | See_other _ ->
        invalid "expected a model byte list" in
  bytes [] value

let of_text family text =
  let tid = Erase.mu_tid family in
  String.to_seq text |> List.of_seq |> List.rev
  |> List.fold_left (fun tail character ->
    Tag (tid, 1, [Nat (Bignum.of_int (Char.code character)); tail])) (Tag (tid, 0, []))

let fields (model : Model.t) = function
  | Product (tid, fields) when model.repr = Rir.TyStruct tid &&
      List.length fields = List.length model.fields -> Ok fields
  | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ | Database _
  | Context _ | Uri _ | See_other _ ->
      invalid ("model result layout differs: " ^ model.name)

let scalar kind value = match kind with
  | Model.Nat_field -> scalar_nat value |> Result.map Bignum.to_string
  | Model.Bool_field -> boolean value |> Result.map string_of_bool
  | Model.Text_field family -> text family value |> Result.map (Printf.sprintf "%S")

(* One pass validates and prints every field. Both readers take what they
   need from that result. *)
let model_fields (model : Model.t) value =
  let* values = fields model value in
  let* pairs = zip model.fields values in
  List.fold_left (fun result ((name, kind), value) ->
    let* fields = result in
    let* printed = scalar kind value in
    Ok ((name, value, printed) :: fields)) (Ok []) pairs
  |> Result.map List.rev

let print_model model value =
  let* fields = model_fields model value in
  Ok (model.Model.name ^ " { " ^ String.concat ", "
    (List.map (fun (name, _value, text) -> name ^ ": " ^ text) fields) ^ " }\n")

let key (model : Model.t) value =
  let* fields = model_fields model value in
  let* _name, key, _printed = List.find_opt (fun (name, _value, _printed) ->
      String.equal name "id") fields
    |> Option.to_result ~none:(Error.Mismatch "run: model requires id") in
  scalar_nat key
