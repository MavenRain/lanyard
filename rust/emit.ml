(** Native Rust printing with typed layouts and explicit ownership conversions.
    Nominal family payloads own boxed tuples; foreign calls remain unsupported. *)
open Kanon_kernel
open Rir
let ( let* ) = Result.bind
let all = Rules.all_ok
let refuse text = Error (Error.Not_yet ("Rust native emission: " ^ text))
let invalid text = Error (Error.Mismatch ("Rust native emission: " ^ text))
type ty = Nat | Unit | Product of ty list | Sum of ty list | Shared of ty
  | Closure of ty list * ty | Nominal of string
type family = { family_name : string; variants : ty list list }
type value = { code : string; ty : ty }
type signature = { name : string; params : ty list; result : ty; body : rtm }
let rec key = function
  | Nat -> "nat" | Unit -> "unit"
  | Nominal name -> "nominal(" ^ string_of_int (String.length name) ^ ":" ^ name ^ ")"
  | Product fields -> "product(" ^ String.concat "," (List.map key fields) ^ ")"
  | Sum fields -> "sum(" ^ String.concat "," (List.map key fields) ^ ")"
  | Shared ty -> "shared(" ^ key ty ^ ")"
  | Closure (params, result) -> "closure(" ^ String.concat "," (List.map key params)
      ^ ";" ^ key result ^ ")"
let same a b = String.equal (key a) (key b)
let identifier prefix text = prefix ^ (String.to_seq text |> Seq.map
  (fun c -> Printf.sprintf "%02x" (Char.code c)) |> List.of_seq |> String.concat "")
let function_name = identifier "f_"
let type_name ty = identifier "T" (key ty)
let drop n text = String.to_seq text |> Seq.drop n |> String.of_seq
let inside prefix text =
  if String.starts_with ~prefix text && String.ends_with ~suffix:">" text then
    Some (String.to_seq text |> Seq.drop (String.length prefix)
      |> Seq.take (max 0 (String.length text - String.length prefix - 1)) |> String.of_seq)
  else None
(** Only delimiters outside nested layouts separate fields. *)
let split delimiter text =
  let step (depth, current, chunks, valid) c =
    if Char.equal c delimiter && Int.equal depth 0 then (depth, [], current :: chunks, valid)
    else let depth = depth + (if Char.equal c '<' then 1 else if Char.equal c '>' then -1 else 0) in
      (depth, c :: current, chunks, valid && depth >= 0) in
  let depth, current, chunks, valid = String.fold_left step (0, [], [], true) text in
  let decode chars = String.of_seq (List.to_seq (List.rev chars)) in
  if not valid || not (Int.equal depth 0) then invalid ("unbalanced layout: " ^ text)
  else if String.equal text "" then Ok []
  else Ok (List.map decode (List.rev (current :: chunks)))
let rec layout text =
  if String.equal text "nat" then Ok Nat
  else if String.starts_with ~prefix:"mu<" text then
    let* name = inside "mu<" text |> Option.to_result
      ~none:(Error.Mismatch "Rust native emission: malformed family layout") in
    if String.equal name "" || String.exists (fun c -> Char.equal c '<' || Char.equal c '>') name
    then invalid "malformed family name" else Ok (Nominal name)
  else if String.starts_with ~prefix:"fn<" text then
    let* contents = inside "fn<" text |> Option.to_result
      ~none:(Error.Mismatch "Rust native emission: malformed closure layout") in
    let* parts = split ';' contents in
    (match parts with
    | [params; result] ->
        let* params = split ',' params in
        let* params = all (List.map representation params) in
        let* result = representation result in Ok (Closure (params, result))
    | [] | [_] | _ :: _ :: _ :: _ -> invalid "closure layout requires parameters and result")
  else Option.fold ~none:(refuse ("layout " ^ text)) ~some:(fun (prefix, delimiter, make) ->
    let* contents = inside prefix text |> Option.to_result
      ~none:(Error.Mismatch ("Rust native emission: malformed layout: " ^ text)) in
    let* fields = split delimiter contents in
    let* fields = all (List.map representation fields) in Ok (make fields))
    (List.find_opt (fun (prefix, _delimiter, _make) -> String.starts_with ~prefix text)
       [ "tuple<", ',', (fun fields -> if List.is_empty fields then Unit else Product fields);
         "pair<", ',', (fun fields -> if List.is_empty fields then Unit else Product fields);
         "sum<", '|', (fun fields -> Sum fields) ])
and representation text =
  if String.equal text "i31" then Ok Nat
  else if String.starts_with ~prefix:"Arc<" text then
    let* contents = inside "Arc<" text |> Option.to_result
      ~none:(Error.Mismatch "Rust native emission: malformed shared layout") in
    let* ty = representation contents in Ok (Shared ty)
  else Option.fold ~none:(refuse ("representation " ^ text)) ~some:(fun prefix ->
    layout (drop (String.length prefix) text))
    (List.find_opt (fun prefix -> String.starts_with ~prefix text) [ "struct "; "union "; "func " ])
let rec repr = function
  | TyI31 -> Ok Nat
  | TyStruct tid | TyUnion tid -> layout (tid_text tid)
  | TyArc ty -> let* ty = repr ty in Ok (Shared ty)
  | TyFunc tid ->
      let* ty = layout (tid_text tid) in
      (match ty with
      | Closure _ -> Ok ty
      | Nat | Unit | Product _ | Sum _ | Shared _ | Nominal _ -> invalid "function representation needs closure layout")
  | TyThunk tid -> refuse ("thunk signature " ^ tid_text tid)
  | TyForeign name -> refuse ("foreign type " ^ name)
let rec rust_type = function
  | Nat -> "Nat" | Unit -> "()"
  | Product fields -> type_name (Product fields)
  | Sum fields -> type_name (Sum fields)
  | Shared ty -> "Arc<" ^ rust_type ty ^ ">"
  | (Closure _ | Nominal _) as ty -> type_name ty
let rec coerce target value =
  if same target value.ty then Ok value.code
  else match target, value.ty with
    | Shared target, (Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _) ->
        let* code = coerce target value in Ok ("Arc::new(" ^ code ^ ")")
    | (Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _), Shared source ->
        coerce target { code = "(*(" ^ value.code ^ ")).clone()"; ty = source }
    | Shared _, Shared _
    | (Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _), (Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _) ->
        invalid ("conversion from " ^ key value.ty ^ " to " ^ key target)
let at index values =
  if index < 0 then invalid "negative runtime index"
  else List.to_seq values |> Seq.drop index |> Seq.uncons |> Option.map fst |> Option.to_result
    ~none:(Error.Mismatch ("Rust native emission: runtime index " ^ string_of_int index))
let rec arguments what params values =
  match params, values with
  | [], [] -> Ok []
  | param :: params, value :: values ->
      let* code = coerce param value in
      let* rest = arguments what params values in Ok (code :: rest)
  | [], _ :: _ | _ :: _, [] -> invalid (what ^ " count")
let bool_ty = Sum [ Unit; Unit ]
(** Clone uses identify shared local slots even though RLet has no quantity field. *)
let rec shared_slot index = function
  | RClone (RVar slot) -> Int.equal index slot
  | RVar _ | RLit _ | RGlobal _ | RUnit -> false
  | RLet (_, value, body) -> shared_slot index value || shared_slot (index + 1) body
  | RLam (_, _, args) | RCall (_, args) | RStruct (_, args) | RTag (_, _, args)
  | RForeign (_, args) -> List.exists (shared_slot index) args
  | RCallC (head, args) -> shared_slot index head || List.exists (shared_slot index) args
  | RProj (_, _, term) -> shared_slot index term
  | RCase (_, term, branches) -> shared_slot index term || List.exists
      (fun branch -> shared_slot (index + branch.arity) branch.body) branches
  | RClone ((RLit _ | RGlobal _ | RUnit | RLet _ | RLam _ | RCall _ | RCallC _
      | RStruct _ | RProj _ | RTag _ | RCase _ | RForeign _ | RClone _) as term) -> shared_slot index term
let local_value shared value =
  if not shared then value else match value.ty with
  | Shared _ -> value
  | Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _ ->
      { code = "Arc::new(" ^ value.code ^ ")"; ty = Shared value.ty }
let closure_signature signatures fid arity =
  let name = fid_text fid in
  let* signature = List.find_opt (fun signature -> String.equal signature.name name) signatures
    |> Option.to_result ~none:(Error.Mismatch ("Rust native emission: missing closure function " ^ name)) in
  if arity < 0 || arity > List.length signature.params then invalid "closure arity"
  else let count = List.length signature.params - arity in
    let captures = List.to_seq signature.params |> Seq.take count |> List.of_seq in
    let params = List.to_seq signature.params |> Seq.drop count |> List.of_seq in
    Ok (captures, params, signature.result)
let closure_name fid arity = identifier "c_" (fid_text fid ^ ":" ^ string_of_int arity)
let find_family families name = List.find_opt (fun family -> String.equal family.family_name name) families
  |> Option.to_result ~none:(Error.Mismatch ("Rust native emission: missing family metadata " ^ name))
let family_fields families name tag = let* family = find_family families name in at tag family.variants |> Result.map_error (fun _error -> Error.Mismatch ("Rust native emission: constructor tag " ^ string_of_int tag ^ " of " ^ name))
let tuple codes = "(" ^ String.concat ", " codes ^ (if List.is_empty codes then "" else ",") ^ ")"
let branch_result arms =
  match arms with
  | [] -> invalid "empty case"
  | (_pattern, first) :: _rest ->
      let result = match first.ty with Shared ty -> ty
        | Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _ -> first.ty in
      let* arms = all (List.map (fun (pattern, body) ->
        let* body = coerce result body in Ok (pattern ^ " => " ^ body)) arms) in
      Ok (result, String.concat ", " arms)
let primitive name args =
  let* primitive = Prim.of_name name |> Option.to_result
    ~none:(Error.Not_yet ("Rust native emission: native call " ^ name)) in
  let* args = arguments "argument" [Nat; Nat] args in
  let* left = at 0 args in let* right = at 1 args in
  let call method_name = "(" ^ left ^ ")." ^ method_name ^ "(&(" ^ right ^ "))?" in
  let comparison ordering = { code = "if (" ^ left ^ ").compare(&(" ^ right ^ "))." ^ ordering
    ^ "() { " ^ rust_type bool_ty ^ "::V1(()) } else { " ^ rust_type bool_ty ^ "::V0(()) }"; ty = bool_ty } in
  match primitive with
  | Prim.Nat_add -> Ok { code = call "add"; ty = Nat }
  | Prim.Nat_sub -> Ok { code = call "sub"; ty = Nat }
  | Prim.Nat_mul -> Ok { code = call "mul"; ty = Nat }
  | Prim.Nat_eq -> Ok (comparison "is_eq")
  | Prim.Nat_lt -> Ok (comparison "is_lt")
let rec expression families signatures env term =
  let walk = expression families signatures env in
  let values terms = all (List.map walk terms) in
  match term with
  | RVar index -> at index env
  | RUnit -> Ok { code = "()"; ty = Unit }
  | RLit (Literal.LString _) -> refuse "string literal without a checked string layout"
  | RLit (Literal.LInt number) ->
      if Bignum.sign number < 0 then invalid "negative Nat literal"
      else Ok { code = "Nat::decimal(\"" ^ Bignum.to_string number ^ "\")?"; ty = Nat }
  | RGlobal name -> refuse ("unresolved global " ^ name)
  | RLet (_name, bound, body) ->
      let* value = walk bound in
      let value = local_value (shared_slot 0 body) value in
      let name = "v" ^ string_of_int (List.length env) in
      let* body = expression families signatures ({ value with code = name } :: env) body in
      Ok { body with code = "{ let " ^ name ^ " = " ^ value.code ^ "; " ^ body.code ^ " }" }
  | RClone term ->
      let* value = walk term in
      (match value.ty with
      | Shared _ -> Ok { value with code = "Arc::clone(&(" ^ value.code ^ "))" }
      | Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _ ->
          Ok { code = "Arc::new((" ^ value.code ^ ").clone())"; ty = Shared value.ty })
  | RCall (name, terms) ->
      let* args = values terms in
      let action = Option.fold ~none:(fun () -> primitive name args)
        ~some:(fun signature () ->
          let* args = arguments "argument" signature.params args in
          Ok { code = function_name name ^ "(" ^ String.concat ", " args ^ ")?"; ty = signature.result })
        (List.find_opt (fun signature -> String.equal signature.name name) signatures) in action ()
  | RStruct (tid, terms) ->
      let* ty = layout (tid_text tid) in let* args = values terms in
      (match ty with
      | Unit -> if List.is_empty args then Ok { code = "()"; ty } else invalid "unit fields"
      | Product fields ->
          let* args = arguments "argument" fields args in
          Ok { code = rust_type ty ^ " { " ^ String.concat ", "
            (List.mapi (fun i code -> "f" ^ string_of_int i ^ ": " ^ code) args) ^ " }"; ty }
      | Nat | Sum _ | Shared _ | Closure _ | Nominal _ -> invalid "product layout")
  | RProj (tid, index, term) ->
      let* ty = layout (tid_text tid) in let* value = walk term in let* code = coerce ty value in
      (match ty with
      | Product fields ->
          let* field = at index fields in
          let names = List.mapi (fun i _field -> "p" ^ string_of_int i) fields in
          let* name = at index names in
          let bindings = List.mapi (fun i name -> "f" ^ string_of_int i ^ ": " ^ name) names in
          Ok { code = "{ let " ^ rust_type ty ^ " { " ^ String.concat ", " bindings ^ " } = "
            ^ code ^ "; " ^ name ^ " }"; ty = field }
      | Nat | Unit | Sum _ | Shared _ | Closure _ | Nominal _ -> invalid "projection layout")
  | RTag (tid, tag, terms) ->
      let* ty = layout (tid_text tid) in let* args = values terms in
      (match ty with
      | Nominal name ->
          let* fields = family_fields families name tag in
          let* args = arguments "constructor field" fields args in
          let payload = if List.is_empty fields then "" else "(Box::new(" ^ tuple args ^ "))" in
          Ok { code = rust_type ty ^ "::V" ^ string_of_int tag ^ payload; ty }
      | Sum fields ->
          let* field = at tag fields in let* args = arguments "argument" [field] args in
          Ok { code = rust_type ty ^ "::V" ^ string_of_int tag ^ "(" ^ String.concat ", " args ^ ")"; ty }
      | Nat | Unit | Product _ | Shared _ | Closure _ -> invalid "sum layout")
  | RCase (tid, term, branches) ->
      let* ty = layout (tid_text tid) in let* value = walk term in let* code = coerce ty value in
      (match ty with
      | Nominal name ->
          let* family = find_family families name in
          if List.sort Int.compare (List.map (fun branch -> branch.tag) branches)
             <> List.init (List.length family.variants) Fun.id then invalid "family case coverage"
          else
            let* arms = all (List.map (fun branch ->
              let* fields = at branch.tag family.variants in
              if not (Int.equal branch.arity (List.length fields)) then invalid "family case binder count"
              else
                let bindings = List.mapi (fun i ty ->
                  let code = "v" ^ string_of_int (List.length env + i) in
                  (code, local_value (shared_slot (branch.arity - i - 1) branch.body) { code; ty })) fields in
                let names = List.map fst bindings in
                let locals = List.map (fun (name, value) -> { value with code = name }) bindings in
                let* body = expression families signatures (List.rev locals @ env) branch.body in
                let shared = List.map (fun (name, value) ->
                  if String.equal name value.code then "" else "let " ^ name ^ " = " ^ value.code ^ "; ") bindings in
                let payload = "payload" ^ string_of_int (List.length env) in
                let unpack = if List.is_empty fields then "" else "let " ^ tuple names ^ " = *" ^ payload ^ "; " in
                let body = { body with code = "{ " ^ unpack ^ String.concat "" shared ^ body.code ^ " }" } in
                let pattern = rust_type ty ^ "::V" ^ string_of_int branch.tag
                  ^ (if List.is_empty fields then "" else "(" ^ payload ^ ")") in
                Ok (pattern, body)) branches) in
            let* result, arms = branch_result arms in
            Ok { code = "match " ^ code ^ " { " ^ arms ^ " }"; ty = result }
      | Sum fields ->
          if List.sort Int.compare (List.map (fun branch -> branch.tag) branches)
             <> List.init (List.length fields) Fun.id then invalid "case coverage"
          else
            let* arms = all (List.map (fun branch ->
              let* field = at branch.tag fields in
              if not (Int.equal branch.arity 1) then invalid "case binder count"
              else let name = "v" ^ string_of_int (List.length env) in
                let value = local_value (shared_slot 0 branch.body) { code = name; ty = field } in
                let* body = expression families signatures ({ value with code = name } :: env) branch.body in
                let body = if same value.ty field then body else
                  { body with code = "{ let " ^ name ^ " = " ^ value.code ^ "; " ^ body.code ^ " }" } in
                Ok (rust_type ty ^ "::V" ^ string_of_int branch.tag ^ "(" ^ name ^ ")", body)) branches) in
            (match arms with
            | [] -> invalid "empty case"
            | (_pattern, first) :: _rest ->
                let result = match first.ty with Shared ty -> ty
                  | Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _ -> first.ty in
                let* arms = all (List.map (fun (pattern, body) ->
                  let* body = coerce result body in Ok (pattern ^ " => " ^ body)) arms) in
                Ok { code = "match " ^ code ^ " { " ^ String.concat ", " arms ^ " }"; ty = result })
      | Nat | Unit | Product _ | Shared _ | Closure _ -> invalid "case layout")
  | RLam (fid, arity, captures) ->
      let* capture_types, params, result = closure_signature signatures fid arity in
      let* captures = values captures in let* captures = arguments "capture" capture_types captures in
      Ok { code = closure_name fid arity ^ "(" ^ String.concat ", " captures ^ ")";
           ty = Closure (params, result) }
  | RCallC (head, args) ->
      let* head = walk head in let* args = values args in
      let rec signature = function
        | Closure (params, result) -> Ok (params, result)
        | Shared ty -> signature ty
        | Nat | Unit | Product _ | Sum _ | Nominal _ -> invalid "closure call needs a function" in
      let* params, result = signature head.ty in let* args = arguments "argument" params args in
      Ok { code = "((" ^ head.code ^ ").call)(" ^ String.concat ", " args ^ ")?"; ty = result }
  | RForeign (row, _args) -> refuse ("foreign call " ^ row.name)
let rec aggregates ty =
  match ty with
  | Nat | Unit | Nominal _ -> []
  | Shared ty -> aggregates ty
  | Product fields | Sum fields -> ty :: List.concat_map aggregates fields
  | Closure (params, result) -> ty :: List.concat_map aggregates (result :: params)
let rec term_layouts = function
  | RVar _ | RLit _ | RGlobal _ | RUnit -> Ok []
  | RLet (_name, value, body) -> layouts [ value; body ]
  | RLam (_, _, captures) | RCall (_, captures) -> layouts captures
  | RCallC (head, args) -> layouts (head :: args)
  | RStruct (tid, args) | RTag (tid, _, args) ->
      let* ty = layout (tid_text tid) in let* nested = layouts args in Ok (ty :: nested)
  | RProj (tid, _index, term) ->
      let* ty = layout (tid_text tid) in let* nested = term_layouts term in Ok (ty :: nested)
  | RCase (tid, term, branches) ->
      let* ty = layout (tid_text tid) in
      let* nested = layouts (term :: List.map (fun (branch : rbranch) -> branch.body) branches) in Ok (ty :: nested)
  | RForeign (_row, args) -> layouts args
  | RClone term -> term_layouts term
and layouts terms = let* rows = all (List.map term_layouts terms) in Ok (List.concat rows)
let rec closure_sites = function
  | RVar _ | RLit _ | RGlobal _ | RUnit -> []
  | RLet (_, value, body) -> closure_sites value @ closure_sites body
  | RLam (fid, arity, captures) -> (fid, arity) :: List.concat_map closure_sites captures
  | RCall (_, args) | RStruct (_, args) | RTag (_, _, args) | RForeign (_, args) ->
      List.concat_map closure_sites args
  | RCallC (head, args) -> List.concat_map closure_sites (head :: args)
  | RProj (_, _, term) | RClone term -> closure_sites term
  | RCase (_, term, branches) -> closure_sites term
      @ List.concat_map (fun (branch : rbranch) -> closure_sites branch.body) branches
let rec has_closure = function
  | Closure _ -> true
  | Nat | Unit -> false
  | Nominal _ -> true
  | Shared ty -> has_closure ty
  | Product fields | Sum fields -> List.exists has_closure fields
let closure_declaration params result =
  let name = rust_type (Closure (params, result)) in
  "struct " ^ name ^ " {\n    call: Box<dyn Fn("
  ^ String.concat ", " (List.map rust_type params) ^ ") -> Result<" ^ rust_type result
  ^ ", Error> + Send + Sync>,\n    duplicate: Box<dyn Fn() -> Self + Send + Sync>,\n}\n"
  ^ "impl Clone for " ^ name ^ " {\n    fn clone(&self) -> Self { (self.duplicate)() }\n}\n"
  ^ "impl std::fmt::Debug for " ^ name ^ " {\n"
  ^ "    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { f.write_str(\"Closure\") }\n}\n"
(* Each factory moves captures into boxed callbacks. The second callback rebuilds
   an owned closure from explicit copies, including Arc handle clones for Many. *)
let closure_factory signatures (fid, arity) =
  let* captures, params, result = closure_signature signatures fid arity in
  let names prefix types = List.mapi (fun i ty -> (prefix ^ string_of_int i, ty)) types in
  let captures = names "c" captures and params = names "p" params in
  let declarations values = String.concat ", " (List.map (fun (name, ty) -> name ^ ": " ^ rust_type ty) values) in
  let copy (name, ty) = match ty with
    | Shared _ -> "Arc::clone(&(" ^ name ^ "))"
    | Nat | Unit | Product _ | Sum _ | Closure _ | Nominal _ -> "(" ^ name ^ ").clone()" in
  let saved = List.map (fun (name, ty) -> ("saved_" ^ name, ty)) captures in
  let name = closure_name fid arity in let ty = Closure (List.map snd params, result) in
  let code = "fn " ^ name ^ "(" ^ declarations captures ^ ") -> " ^ rust_type ty ^ " {\n"
    ^ String.concat "" (List.map (fun ((name, _ty) as value) ->
        "    let saved_" ^ name ^ " = " ^ copy value ^ ";\n") captures)
    ^ "    " ^ rust_type ty ^ " {\n        call: Box::new(move |" ^ declarations params ^ "| "
    ^ function_name (fid_text fid) ^ "("
    ^ String.concat ", " (List.map copy captures @ List.map fst params) ^ ")),\n"
    ^ "        duplicate: Box::new(move || " ^ name ^ "(" ^ String.concat ", " (List.map copy saved)
    ^ ")),\n    }\n}\n" in
  Ok (ty, code)
let declaration ty =
  match ty with
  | Closure (params, result) -> closure_declaration params result
  | Nat | Unit | Product _ | Sum _ | Shared _ | Nominal _ ->
  let fields = match ty with
    | Product fields -> "struct " ^ rust_type ty ^ " { " ^ String.concat ", "
        (List.mapi (fun i ty -> "f" ^ string_of_int i ^ ": " ^ rust_type ty) fields) ^ " }"
    | Sum fields -> "enum " ^ rust_type ty ^ " { " ^ String.concat ", "
        (List.mapi (fun i ty -> "V" ^ string_of_int i ^ "(" ^ rust_type ty ^ ")") fields) ^ " }"
    | Nat | Unit | Shared _ | Closure _ | Nominal _ -> "" in
  (if has_closure ty then "#[derive(Clone, Debug)]\n"
   else "#[derive(Clone, Debug, PartialEq, Eq)]\n") ^ fields ^ "\n"

let runtime = {|// Generated by lanyard's native Rust printer.
use std::sync::Arc;

#[derive(Clone, Debug, PartialEq, Eq)]
struct Nat(Vec<u8>);

#[derive(Debug)]
enum Error { Digit, Arithmetic }
impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Digit => f.write_str("invalid natural digit"),
            Self::Arithmetic => f.write_str("natural limb invariant failed"),
        }
    }
}
impl std::error::Error for Error {}

impl Nat {
    fn canonical(bytes: Vec<u8>) -> Self {
        Self(bytes.into_iter().rev().skip_while(|b| *b == 0).collect::<Vec<_>>()
            .into_iter().rev().collect())
    }
    fn decimal(text: &str) -> Result<Self, Error> {
        text.bytes().try_fold(Self(Vec::new()), |n, c| {
            if c.is_ascii_digit() {
                n.scale(10)?.add(&Self::canonical(vec![c - b'0']))
            } else { Err(Error::Digit) }
        })
    }
    fn compare(&self, other: &Self) -> std::cmp::Ordering {
        self.0.len().cmp(&other.0.len()).then_with(|| self.0.iter().rev().cmp(other.0.iter().rev()))
    }
    fn finish(bytes: Vec<u8>, carry: u16) -> Result<Self, Error> {
        u8::try_from(carry).map_err(|_| Error::Arithmetic)
            .map(|last| Self::canonical(bytes.into_iter().chain(std::iter::once(last)).collect()))
    }
    fn add(&self, other: &Self) -> Result<Self, Error> {
        let (bytes, carry) = (0..self.0.len().max(other.0.len())).try_fold(
            (Vec::new(), 0_u16), |(bytes, carry), i| {
                let sum = self.0.get(i).map_or(0, |b| u16::from(*b))
                    + other.0.get(i).map_or(0, |b| u16::from(*b)) + carry;
                u8::try_from(sum % 256).map_err(|_| Error::Arithmetic)
                    .map(|byte| (bytes.into_iter().chain(std::iter::once(byte)).collect(), sum / 256))
            })?;
        Self::finish(bytes, carry)
    }
    fn sub(&self, other: &Self) -> Result<Self, Error> {
        if self.compare(other).is_lt() { Ok(Self(Vec::new())) } else {
        let (bytes, borrow) = self.0.iter().enumerate().try_fold(
            (Vec::new(), 0_u16), |(bytes, borrow), (i, byte)| {
                let rhs = other.0.get(i).map_or(0, |b| u16::from(*b)) + borrow;
                let lhs = u16::from(*byte);
                u8::try_from((lhs + 256 - rhs) % 256).map_err(|_| Error::Arithmetic)
                    .map(|byte| (bytes.into_iter().chain(std::iter::once(byte)).collect(), u16::from(lhs < rhs)))
            })?;
        if borrow == 0 { Ok(Self::canonical(bytes)) } else { Err(Error::Arithmetic) }
        }
    }
    fn scale(&self, factor: u8) -> Result<Self, Error> {
        let (bytes, carry) = self.0.iter().try_fold((Vec::new(), 0_u16), |(bytes, carry), byte| {
            let product = u16::from(*byte) * u16::from(factor) + carry;
            u8::try_from(product % 256).map_err(|_| Error::Arithmetic)
                .map(|byte| (bytes.into_iter().chain(std::iter::once(byte)).collect(), product / 256))
        })?;
        Self::finish(bytes, carry)
    }
    fn mul(&self, other: &Self) -> Result<Self, Error> {
        other.0.iter().enumerate().try_fold(Self(Vec::new()), |sum, (i, byte)| {
            let scaled = self.scale(*byte)?;
            let shifted = Self::canonical(std::iter::repeat_n(0, i).chain(scaled.0).collect());
            sum.add(&shifted)
        })
    }
}

|}

let family_catalog rows =
  let tids = List.concat_map (fun (_name, entry) -> match entry with
    | Erase.Dropped | Erase.Postulate _ -> []
    | Erase.Code decls -> List.concat_map (function RData tids -> tids | RFun _ -> []) decls) rows in
  let* legs = tids |> List.filter_map (fun tid ->
    let text = tid_text tid in
    if not (String.starts_with ~prefix:"leg<" text) then None else Some (
      let* contents = inside "leg<" text |> Option.to_result
        ~none:(Error.Mismatch "Rust native emission: malformed constructor metadata") in
      let* parts = split ',' contents in
      match parts with
      | family :: tag :: fields ->
          let* family = layout family in
          let* tag_number = int_of_string_opt tag |> Option.to_result
            ~none:(Error.Mismatch "Rust native emission: constructor tag is not an integer") in
          if tag_number < 0 || not (String.equal tag (string_of_int tag_number)) then invalid "invalid constructor tag"
          else let* fields = all (List.map representation fields) in
            (match family with
            | Nominal name -> Ok (name, tag_number, fields)
            | Nat | Unit | Product _ | Sum _ | Shared _ | Closure _ -> invalid "constructor family layout")
      | [] | [_] -> invalid "incomplete constructor metadata")) |> all in
  let* unique = List.fold_left (fun acc (name, tag, fields) ->
    let* acc = acc in
    Option.fold ~none:(Ok ((name, tag, fields) :: acc)) ~some:(fun (_name, _tag, old) ->
      if List.map key fields = List.map key old then Ok acc else invalid ("conflicting constructor metadata " ^ name))
      (List.find_opt (fun (n, t, _fields) -> String.equal n name && Int.equal t tag) acc)) (Ok []) legs in
  let names = List.map (fun (name, _tag, _fields) -> name) unique |> List.sort_uniq String.compare in
  all (List.map (fun name ->
    let variants = List.filter_map (fun (n, tag, fields) -> if String.equal n name then Some (tag, fields) else None) unique
      |> List.sort (fun (a, _fields) (b, _other) -> Int.compare a b) in
    if List.map fst variants <> List.init (List.length variants) Fun.id then invalid ("noncontiguous constructor tags " ^ name)
    else Ok { family_name = name; variants = List.map snd variants }) names)
let rec validate_type families = function
  | Nat | Unit -> Ok ()
  | Nominal name -> let* _family = find_family families name in Ok ()
  | Shared ty -> validate_type families ty
  | Product fields | Sum fields -> let* _checked = all (List.map (validate_type families) fields) in Ok ()
  | Closure (params, result) -> let* _checked = all (List.map (validate_type families) (result :: params)) in Ok ()
let family_declaration family =
  let variants = List.mapi (fun tag fields ->
    "V" ^ string_of_int tag ^ (if List.is_empty fields then "" else "(Box<" ^ tuple (List.map rust_type fields) ^ ">)")) family.variants in
  "#[derive(Clone, Debug)]\nenum " ^ rust_type (Nominal family.family_name) ^ " { " ^ String.concat ", " variants ^ " }\n"
let native rows =
  let* families = family_catalog rows in
  let* signatures = rows |> List.concat_map (fun (_name, entry) ->
    match entry with
    | Erase.Dropped | Erase.Postulate _ -> []
    | Erase.Code decls -> List.filter_map (function
      | RData _ -> None
      | RFun (fid, params, result, body) -> Some (
          let* params = all (List.map repr params) in
          let* result = repr result in Ok { name = fid_text fid; params; result; body })) decls)
    |> all in
  let names = List.map (fun signature -> signature.name) signatures in
  if List.length (List.sort_uniq String.compare names) <> List.length names then invalid "duplicate function"
  else
    let* mentioned = layouts (List.map (fun signature -> signature.body) signatures) in
    let family_types = List.concat_map (fun family -> List.concat family.variants) families in
    let* _checked = all (List.map (validate_type families)
      (family_types @ mentioned @ List.concat_map (fun signature -> signature.result :: signature.params) signatures)) in
    let* bodies = all (List.map (fun signature ->
      let env = List.mapi (fun i ty -> { code = "a" ^ string_of_int i; ty }) signature.params in
      let* value = expression families signatures (List.rev env) signature.body in
      let* body = coerce signature.result value in
      let body = if String.ends_with ~suffix:"?" body then
          String.to_seq body |> Seq.take (String.length body - 1) |> String.of_seq
        else "Ok(" ^ body ^ ")" in
      let params = List.map (fun value -> value.code ^ ": " ^ rust_type value.ty) env in
      Ok ("fn " ^ function_name signature.name ^ "(" ^ String.concat ", " params ^ ") -> Result<"
        ^ rust_type signature.result ^ ", Error> {\n    " ^ body ^ "\n}\n")) signatures) in
    let sites = List.concat_map (fun signature -> closure_sites signature.body) signatures
      |> List.sort_uniq compare in
    let* factories = all (List.map (closure_factory signatures) sites) in
    let types = bool_ty :: List.map fst factories @ mentioned @ family_types
      @ List.concat_map (fun signature -> signature.result :: signature.params) signatures
      |> List.concat_map aggregates |> List.sort_uniq (fun a b -> String.compare (key a) (key b)) in
    let family_code = if List.is_empty families then "" else String.concat "\n" (List.map family_declaration families) ^ "\n" in
    Ok (runtime ^ family_code ^ String.concat "\n" (List.map declaration types) ^ "\n"
      ^ String.concat "\n" (List.map snd factories) ^ (if List.is_empty factories then "" else "\n")
      ^ String.concat "\n" bodies)
