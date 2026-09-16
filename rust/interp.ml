(** An interpreter for checked Rust IR with explicit store, step and depth bounds. *)
open Kanon_kernel
open Rir
open Run_value
module Lower = Kanon_surface.Lower
type fn = { name : string; params : repr list; result : repr; body : rtm }
type context = { functions : fn list; foreign : Run_store.catalog; families : Foreign.Printer.family list }
type state = { steps : int; store : Run_store.t }
let default_steps = 100000
let max_steps = 1000000
let depth_limit = 512
let step depth state = match () with
  | () when state.steps <= 0 -> invalid "step limit exhausted"
  | () when depth > depth_limit -> invalid "nesting limit exhausted"
  | () -> Ok { state with steps = state.steps - 1 }

let find context name = List.find_opt (fun fn -> String.equal fn.name name) context.functions
  |> Option.to_result ~none:(Error.Mismatch ("run: missing runtime function " ^ name))

(* The model representation owns the Boolean layout. Read the tag identity
   from it, so a change there cannot drift away from the interpreter. *)
let boolean_tid = match Model.bool_repr with
  | TyUnion tid -> Ok tid
  | TyI31 | TyStruct _ | TyFunc _ | TyThunk _ | TyArc _ | TyForeign _ ->
      invalid "Boolean representation is not a union"

let primitive name arguments = match arguments with
  | [left; right] ->
      let* left = natural left in let* right = natural right in
      let* tid = boolean_tid in
      let boolean answer = Tag (tid, (if answer then 1 else 0), [Unit]) in
      Ok (match name with
        | Prim.Nat_add -> Nat (Bignum.add left right)
        | Prim.Nat_sub -> Nat (Bignum.sub left right)
        | Prim.Nat_mul -> Nat (Bignum.mul left right)
        | Prim.Nat_eq -> boolean (Bignum.equal left right)
        | Prim.Nat_lt -> boolean (Bignum.compare left right < 0))
  | [] | _ :: _ -> invalid "primitive argument count"

let rec evaluate context depth state env term =
  let* state = step depth state in
  let walk state = evaluate context (depth + 1) state env in
  let values state = values context (depth + 1) state env in
  match term with
  | RVar index -> at index env |> Result.map (fun value -> value, state)
  | RLit (Literal.LInt number) ->
      let* number = natural (Nat number) in Ok (Nat number, state)
  | RLit (Literal.LString text) -> Ok (Text text, state)
  | RGlobal name -> call context (depth + 1) state name []
  | RUnit -> Ok (Unit, state)
  | RLet (_name, term, body) ->
      let* value, state = walk state term in
      evaluate context (depth + 1) state (value :: env) body
  | RLam (fid, arity, captures) ->
      let* fn = find context (fid_text fid) in
      if arity < 0 || List.length fn.params <> arity + List.length captures then
        invalid "closure argument count"
      else let* captures, state = values state captures in
        Ok (Closure (fid, arity, captures), state)
  | RCall (name, terms) ->
      let* arguments, state = values state terms in
      call context (depth + 1) state name arguments
  | RCallC (head, terms) ->
      let* head, state = walk state head in
      let* arguments, state = values state terms in
      (match head with
       | Closure (fid, arity, captures) ->
           if List.length arguments <> arity then invalid "closure call argument count"
           else call context (depth + 1) state (fid_text fid) (captures @ arguments)
       | Nat _ | Text _ | Unit | Product _ | Tag _ | Database _
       | Context _ | Uri _ | See_other _ -> invalid "expected a closure")
  | RStruct (tid, terms) ->
      let* fields, state = values state terms in
      let value = if tid = Tid "tuple<>" && List.is_empty fields then Unit else Product (tid, fields) in
      Ok (value, state)
  | RProj (tid, index, term) ->
      let* value, state = walk state term in
      (match value with
       | Product (actual, fields) when tid = actual ->
           at index fields |> Result.map (fun value -> value, state)
       | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ | Database _
       | Context _ | Uri _ | See_other _ -> invalid "projection layout differs")
  | RTag (tid, tag, terms) ->
      let* fields, state = values state terms in Ok (Tag (tid, tag, fields), state)
  | RCase (tid, term, branches) ->
      let* value, state = walk state term in
      (match value with
       | Tag (actual, tag, fields) when tid = actual ->
           let* branch = List.find_opt (fun branch -> branch.tag = tag) branches
             |> Option.to_result ~none:(Error.Mismatch "run: missing case branch") in
           if branch.arity <> List.length fields then invalid "case binder count"
           else evaluate context (depth + 1) state (List.rev fields @ env) branch.body
       | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ | Database _
       | Context _ | Uri _ | See_other _ -> invalid "case layout differs")
  | RForeign (row, terms) ->
      let* arguments, state = values state terms in
      let* value, store = Run_store.foreign context.foreign row arguments state.store in
      Ok (value, { state with store })
  | RClone term -> walk state term
and values context depth state env terms =
  List.fold_left (fun result term ->
    let* reversed, state = result in
    let* value, state = evaluate context depth state env term in
    Ok (value :: reversed, state)) (Ok ([], state)) terms
  |> Result.map (fun (reversed, state) -> List.rev reversed, state)
and call context depth state name arguments =
  let* state = step depth state in
  (* A checked definition may shadow a primitive name. *)
  Option.fold ~none:(fun () ->
      let* prim = Prim.of_name name
        |> Option.to_result ~none:(Error.Mismatch ("run: missing runtime function " ^ name)) in
      let* value = primitive prim arguments in Ok (value, state))
    ~some:(fun fn () ->
      if List.length arguments <> List.length fn.params then invalid ("function argument count: " ^ name)
      else evaluate context (depth + 1) state (List.rev arguments) fn.body)
    (List.find_opt (fun fn -> String.equal fn.name name) context.functions) ()

let functions rows = List.concat_map (fun (_name, entry) -> match entry with
  | Erase.Dropped | Erase.Postulate _ -> []
  | Erase.Code declarations -> List.filter_map (function
      | RData _ -> None
      | RFun (fid, params, result, body) -> Some { name = fid_text fid; params; result; body }) declarations) rows

let prepare checked =
  let* checked = Reachable.program "main" checked in
  let* checked = if List.is_empty checked.Kanon_surface.Elab.signatures then Ok checked else
    let* checked = Kanon_surface.Fuse.program checked in
    let* checked = Reachable.program "main" checked in
    Kanon_surface.Fuse.closed checked in
  let* specialized = Lower.specialize checked in
  let checked = specialized.Lower.specialized in
  let* models = Model.catalog checked in
  let* instances = Lower.connections specialized in
  let* connections = Connection.catalog checked (List.map (fun (model : Model.t) -> model.name, model.name) models) instances in
  let* text_instances = Lower.text_operations specialized in
  let* texts = Text_ops.catalog checked text_instances in
  let* constants = Lower.catalog checked in
  let* rows = Lower.program_with instances specialized in
  let* families = Foreign.Printer.family_catalog rows in
  Ok { functions = functions rows; foreign = { Run_store.models; connections; texts; constants }; families }

let checked_steps steps =
  if steps <= 0 || steps > max_steps then invalid "steps must be in 1..1000000" else Ok ()

let run ?(steps = default_steps) ?(output = Model.Discard) checked =
  let* () = checked_steps steps in
  let* context = prepare checked in
  let* main = find context "main" in
  let* () = if List.is_empty main.params then Ok () else invalid "entry point requires runtime arguments: main" in
  let* printed = match output with
    | Model.Discard -> Ok None
    | Model.Print_model name ->
        let* model = List.find_opt (fun (model : Model.t) -> String.equal model.name name) context.foreign.models
          |> Option.to_result ~none:(Error.Mismatch ("run: printed model is unknown or not reachable: " ^ name)) in
        if main.result = model.repr then Ok (Some model) else invalid "entry point result differs from printed model" in
  let* value, _state = call context 0 { steps; store = Run_store.empty } "main" [] in
  let* text = Option.fold ~none:(Ok "") ~some:(fun model -> print_model model value) printed in
  Ok (value, text)

let foreign_repr name = function
  | TyForeign (actual, []) | TyArc (TyForeign (actual, [])) -> String.equal name actual
  | TyI31 | TyStruct _ | TyUnion _ | TyFunc _ | TyThunk _ | TyArc _ | TyForeign _ -> false

let request ?(steps = default_steps) ?form ~uri checked =
  let* () = checked_steps steps in
  let* uri = Run_http.uri uri in
  let* _fields = Option.fold ~none:(Ok []) ~some:Form_data.parse form in
  let* context = prepare checked in
  let* main = find context "main" in
  let* body = match main.params, form with
    | [cx_type; uri_type], None when foreign_repr "Cx" cx_type && foreign_repr "Uri" uri_type
        && foreign_repr "SeeOther" main.result -> Ok []
    | [cx_type; uri_type; body_type], Some body when foreign_repr "Cx" cx_type && foreign_repr "Uri" uri_type
        && foreign_repr "SeeOther" main.result ->
        let* family = Text_ops.byte_family body_type context.families in
        Ok [of_text family.family_name body]
    | ([] | _ :: _), (None | Some _) ->
        invalid (Option.fold ~none:"request entry point must have type Cx -> Uri -> SeeOther"
          ~some:(fun _body -> "form request entry point must have type Cx -> Uri -> Bytes -> SeeOther (Bytes is a checked byte list)") form) in
  let cx, store = Run_store.context
    (List.map (fun (model : Model.t) -> model.name) context.foreign.models) Run_store.empty in
  let* value, _state = call context 0 { steps; store } "main" ([cx; Uri uri] @ body) in
  let* text = Run_http.response value in
  Ok (value, text)
