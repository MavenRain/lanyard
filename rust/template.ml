(** Print rules are tokenized before substitution. Bound text is never parsed
    again, so a placeholder in an argument stays literal argument text. *)
open Kanon_kernel
let ( let* ) = Result.bind
type part = Text of string | Slot of string
type t = part list
let invalid text = Error (Error.Mismatch ("Rust print rule: " ^ text))
let name_start c = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
let name_tail c = name_start c || (c >= '0' && c <= '9') || Char.equal c '_'
let valid_name name = String.to_seq name |> Seq.uncons |> Option.fold
  ~none:false ~some:(fun (first, rest) -> name_start first && Seq.for_all name_tail rest)
let parse text =
  let flush chars parts = if List.is_empty chars then parts
    else Text (String.of_seq (List.to_seq (List.rev chars))) :: parts in
  let rec slot chars = function
    | [] -> invalid "unclosed placeholder"
    | '}' :: rest ->
        let name = String.of_seq (List.to_seq (List.rev chars)) in
        if valid_name name then Ok (name, rest) else invalid "invalid placeholder name"
    | c :: rest -> slot (c :: chars) rest in
  let rec walk chars parts = function
    | [] -> Ok (List.rev (flush chars parts))
    | '#' :: '{' :: rest ->
        let* name, rest = slot [] rest in walk [] (Slot name :: flush chars parts) rest
    | c :: rest -> walk (c :: chars) parts rest in
  if String.equal (String.trim text) "" then invalid "empty template"
  else walk [] [] (List.of_seq (String.to_seq text))
let slots template = List.filter_map (function Text _ -> None | Slot name -> Some name) template
let unique what names =
  if List.length names = List.length (List.sort_uniq String.compare names) then Ok ()
  else invalid ("duplicate " ^ what)
let render template bindings =
  let* () = unique "binding" (List.map fst bindings) in
  let names = slots template |> List.sort_uniq String.compare in
  if List.sort String.compare (List.map fst bindings) <> names then invalid "binding set differs from placeholders"
  else Rules.all_ok (List.map (function
    | Text text -> Ok text
    | Slot name -> List.assoc_opt name bindings |> Option.to_result
        ~none:(Error.Mismatch ("Rust print rule: missing binding " ^ name))) template)
    |> Result.map (String.concat "")

(** Evaluate runtime arguments once in telescope order. One slots move their
    value exactly once. Many slots borrow Arc storage; an explicit clone in
    the target rule determines whether the foreign value itself is copied. *)
let call ~parameters ~types ~arguments text =
  let* template = parse text in
  let* () = unique "parameter" (List.map fst parameters @ List.map fst types) in
  let names = slots template in
  let declared = List.map fst parameters @ List.map fst types in
  let bad_quantity (name, quantity) =
    let uses = List.length (List.filter (String.equal name) names) in
    match quantity with
    | Quantity.Zero -> true
    | Quantity.One -> uses <> 1
    | Quantity.Many -> uses < 1 in
  match () with
  | () when List.exists (fun name -> not (List.mem name declared)) names -> invalid "undeclared placeholder"
  | () when List.exists bad_quantity parameters -> invalid "runtime placeholder quantity"
  | () when List.length parameters <> List.length arguments -> invalid "argument count"
  | () ->
    let* bound = Rules.all_ok (List.mapi (fun index (name, quantity) ->
      let* code = List.to_seq arguments |> Seq.drop index |> Seq.uncons |> Option.map fst
        |> Option.to_result ~none:(Error.Mismatch "Rust print rule: argument count") in
      let local = "__lan_arg_" ^ string_of_int index in
      let use = match quantity with
        | Quantity.Zero | Quantity.One -> local
        | Quantity.Many -> "(&*(" ^ local ^ "))" in
      Ok ("let " ^ local ^ " = " ^ code ^ "; ", (name, use))) parameters) in
    let bindings = List.map snd bound @ List.filter (fun (name, _code) -> List.mem name names) types in
    let* body = render template bindings in
    Ok ("{ " ^ String.concat "" (List.map fst bound) ^ body ^ " }")
