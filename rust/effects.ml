(** Async propagation follows direct calls and evaluated subexpressions.
    Closure bodies have their own signatures. Recursive futures need a later
    representation, so cycles through async functions are refused. *)
open Kanon_kernel
open Rir
let ( let* ) = Result.bind
type t = Sync | Async_db
let join a b = match a, b with Sync, Sync -> Sync
  | Async_db, Sync | Sync, Async_db | Async_db, Async_db -> Async_db
let prefix = function Sync -> "" | Async_db -> "async "
let await = function Sync -> "" | Async_db -> ".await"
let lookup names name = Option.value ~default:Sync (List.assoc_opt name names)
let rec dependencies foreign term =
  let walk = dependencies foreign in
  let combine terms =
    let* rows = Rules.all_ok (List.map walk terms) in
    Ok (List.fold_left (fun effect (next, _calls) -> join effect next) Sync rows,
      List.concat_map snd rows) in
  match term with
  | RVar _ | RLit _ | RGlobal _ | RUnit -> Ok (Sync, [])
  | RCall (name, args) -> let* effect, calls = combine args in Ok (effect, name :: calls)
  | RForeign (row, args) ->
      let* effect = foreign row in let* nested, calls = combine args in Ok (join effect nested, calls)
  | RLet (_, value, body) -> combine [value; body]
  | RLam (_, _, captures) | RStruct (_, captures) | RTag (_, _, captures) -> combine captures
  | RCallC (head, args) -> combine (head :: args)
  | RProj (_, _, term) | RClone term -> walk term
  | RCase (_, term, branches) -> combine (term :: List.map (fun branch -> branch.body) branches)
let infer ~foreign bodies =
  let* graph = Rules.all_ok (List.map (fun (name, body) ->
    let* dependencies = dependencies foreign body in Ok (name, dependencies)) bodies) in
  let rec settle remaining effects =
    if Int.equal remaining 0 then effects else
    let next = List.map (fun (name, (direct, calls)) -> name,
      List.fold_left (fun effect name -> join effect (lookup effects name)) direct calls) graph in
    if next = effects then effects else settle (remaining - 1) next in
  let effects = settle (List.length graph) (List.map (fun (name, (direct, _calls)) -> name, direct) graph) in
  let rec search target (found, visited) name = match () with
    | () when found || String.equal name target -> (true, visited)
    | () when List.mem name visited -> (false, visited) | () -> Option.fold ~none:(false, visited) ~some:(fun (_effect, calls) ->
      List.fold_left (search target) (false, name :: visited) calls) (List.assoc_opt name graph) in
  let reaches target seen name = fst (search target (false, seen) name) in
  let cycle = List.find_opt (fun (name, (_direct, calls)) -> match lookup effects name with
    | Sync -> false | Async_db -> List.exists (reaches name []) calls) graph in
  Option.fold ~none:(Ok effects) ~some:(fun (name, _dependencies) ->
    Error (Error.Not_yet ("Rust emission: recursive async function " ^ name))) cycle
