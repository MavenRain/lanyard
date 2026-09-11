(** Rust erasure IR. RUnit is a runtime value, never a proof placeholder.
    Shared binders carry Arc ownership; closure environments are by value.
    Symbolic layout groups retain the carried eraser's structural identities. *)
type tid = Tid of string
type fid = Fid of string
type repr =
  | TyI31
  | TyStruct of tid
  | TyUnion of tid
  | TyFunc of tid
  | TyThunk of tid
  | TyArc of repr
  | TyForeign of string * repr list

type foreign = {
  name : string;
  schema : string;
  print_rule : string;
  effects : string list;
  type_arguments : (string * string) list;
  arity : int;
}

type rtm =
  | RVar of int
  | RLit of Literal.t
  | RGlobal of string
  | RUnit
  | RLet of string * rtm * rtm
  | RLam of fid * int * rtm list
  | RCall of string * rtm list
  | RCallC of rtm * rtm list
  | RStruct of tid * rtm list
  | RProj of tid * int * rtm
  | RTag of tid * int * rtm list
  | RCase of tid * rtm * rbranch list
  | RForeign of foreign * rtm list
  | RClone of rtm
and rbranch = { tag : int; arity : int; body : rtm }

type rdecl =
  | RFun of fid * repr list * repr * rtm
  | RData of tid list

let tid_text (Tid text) = text
let fid_text (Fid text) = text
let literal_text (literal : Literal.t) : string =
  match literal with
  | Literal.LString text -> "\"" ^ String.escaped text ^ "\""
  | Literal.LInt number -> Bignum.to_string number

let rec print_repr (r : repr) : string =
  match r with
  | TyI31 -> "i31"
  | TyStruct t -> "struct " ^ tid_text t
  | TyUnion t -> "union " ^ tid_text t
  | TyFunc t -> "func " ^ tid_text t
  | TyThunk t -> "thunk " ^ tid_text t
  | TyArc inner -> "Arc<" ^ print_repr inner ^ ">"
  | TyForeign (name, arguments) -> "foreign " ^ name
      ^ (if List.is_empty arguments then "" else
          "<" ^ String.concat "," (List.map print_repr arguments) ^ ">")

let rec print_rtm (t : rtm) : string =
  match t with
  | RVar i -> Printf.sprintf "RVar %d" i
  | RLit l -> "RLit " ^ literal_text l
  | RGlobal n -> "RGlobal " ^ n
  | RUnit -> "RUnit"
  | RLet (x, v, b) -> Printf.sprintf "RLet %s (%s) (%s)" x (print_rtm v) (print_rtm b)
  | RLam (f, n, cs) -> Printf.sprintf "RLam %s %d %s" (fid_text f) n (rtm_list cs)
  | RCall (name, args) -> Printf.sprintf "RCall %s %s" name (rtm_list args)
  | RCallC (head, args) -> Printf.sprintf "RCallC (%s) %s" (print_rtm head) (rtm_list args)
  | RStruct (tid, fields) -> Printf.sprintf "RStruct %s %s" (tid_text tid) (rtm_list fields)
  | RProj (tid, index, scrut) -> Printf.sprintf "RProj %s %d (%s)" (tid_text tid) index (print_rtm scrut)
  | RTag (tid, tag, args) -> Printf.sprintf "RTag %s %d %s" (tid_text tid) tag (rtm_list args)
  | RCase (tid, scrut, branches) -> Printf.sprintf "RCase %s (%s) [%s]"
      (tid_text tid) (print_rtm scrut) (String.concat "; " (List.map print_branch branches))
  | RForeign (row, args) -> Printf.sprintf "RForeign %s %s" row.name (rtm_list args)
  | RClone value -> "RClone (" ^ print_rtm value ^ ")"
and rtm_list xs = "[" ^ String.concat "; " (List.map print_rtm xs) ^ "]"
and print_branch b = Printf.sprintf "{%d %d (%s)}" b.tag b.arity (print_rtm b.body)

let print_decl (d : rdecl) : string =
  match d with
  | RFun (f, params, result, body) -> Printf.sprintf "fun %s (%s) : %s := %s"
      (fid_text f) (String.concat ", " (List.map print_repr params))
      (print_repr result) (print_rtm body)
  | RData tids -> "data [" ^ String.concat "; " (List.map tid_text tids) ^ "]"

let owned (q : Quantity.t) (ty : repr) : repr =
  match q with
  | Quantity.Zero | Quantity.One -> ty
  | Quantity.Many -> TyArc ty

let use (q : Quantity.t) (term : rtm) : rtm =
  match q with
  | Quantity.Zero | Quantity.One -> term
  | Quantity.Many -> RClone term

(** Resolve fully applied target calls using the checked instance catalog.
    A missing argument cannot silently print a partial foreign expression.
    [known] holds the emitted parameter count of a native name. [None] marks
    a definition that erased to a dropped item or to a postulate. A prim
    carries [Some count] from its runtime arity, as a foreign row does. *)
let rec resolve ~(known : (string * int option) list) (foreign : foreign list) (term : rtm) : (rtm, Error.t) result =
  let ( let* ) = Result.bind in
  let walk = resolve ~known foreign in
  let all args = Rules.all_ok (List.map walk args) in
  let missing name = Error (Error.Not_yet ("Rust target metadata missing: " ^ name)) in
  let fits count declared = Option.fold ~none:true ~some:(Int.equal count) declared in
  let native name args =
    Option.fold ~none:(missing name) ~some:(fun (declared : int option) ->
      if fits (List.length args) declared then Ok (RCall (name, args))
      else Error (Error.Mismatch ("native call arity: " ^ name)))
      (List.assoc_opt name known) in
  let call name args =
    let* args = all args in
    Option.fold ~none:(native name args) ~some:(fun (row : foreign) ->
      if Int.equal row.arity (List.length args) then Ok (RForeign (row, args))
      else Error (Error.Mismatch ("foreign call arity: " ^ name)))
      (List.find_opt (fun row -> String.equal row.name name) foreign) in
  match term with
  | RVar _ | RLit _ | RUnit -> Ok term
  | RGlobal name ->
      if List.exists (fun row -> String.equal row.name name) foreign then
        Error (Error.Not_yet ("foreign function value needs eta expansion: " ^ name))
      else Option.fold ~none:(missing name) ~some:(fun (declared : int option) ->
        if Option.equal Int.equal (Some 0) declared then Ok (RCall (name, []))
        else Error (Error.Not_yet ("function value needs eta expansion: " ^ name)))
        (List.assoc_opt name known)
  | RLet (name, value, body) ->
      let* value = walk value in let* body = walk body in Ok (RLet (name, value, body))
  | RLam (fid, arity, captures) ->
      let* captures = all captures in Ok (RLam (fid, arity, captures))
  | RCall (name, args) | RCallC (RGlobal name, args) -> call name args
  | RCallC ((RVar _ | RLit _ | RUnit | RLet _ | RLam _ | RCall _ | RCallC _
      | RStruct _ | RProj _ | RTag _ | RCase _ | RForeign _ | RClone _) as head, args) ->
      let* head = walk head in let* args = all args in Ok (RCallC (head, args))
  | RStruct (tid, fields) -> let* fields = all fields in Ok (RStruct (tid, fields))
  | RProj (tid, index, scrut) -> let* scrut = walk scrut in Ok (RProj (tid, index, scrut))
  | RTag (tid, tag, args) -> let* args = all args in Ok (RTag (tid, tag, args))
  | RCase (tid, scrut, branches) ->
      let* scrut = walk scrut in
      let* branches = Rules.all_ok (List.map (fun branch ->
        let* body = walk branch.body in Ok { branch with body }) branches) in
      Ok (RCase (tid, scrut, branches))
  | RForeign (row, args) -> call row.name args
  | RClone value -> let* value = walk value in Ok (RClone value)

let resolve_decl ~known foreign (decl : rdecl) : (rdecl, Error.t) result =
  match decl with
  | RData _ -> Ok decl
  | RFun (fid, params, result, body) ->
      resolve ~known foreign body |> Result.map (fun body -> RFun (fid, params, result, body))
