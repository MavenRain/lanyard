open Kanon_kernel
open Rir
module Foreign = Lanyard_rust.Foreign
module Effects = Lanyard_rust.Effects
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let unit = TyStruct (Tid "tuple<>")
let db = TyArc (TyForeign ("Db", []))
let fn name params result body = name, Erase.Code [RFun (Fid name, params, result, body)]
let row = let* entry = Foreign.lookup Catalog.entries "Db.push_schema" in
  Ok {name="Db_push_schema"; schema=entry.name; print_rule=entry.print_rule;
    effects=entry.effects; type_arguments=[]; arity=1}
let push = let* row = row in Ok (RForeign (row, [RVar 0]))
let holds text needle = List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
  String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let tests = [
  "direct recursion", "recursive async function self", (let* push = push in
    Foreign.source [fn "self" [db] unit (RLet ("done", push, RCall ("self", [RVar 1])))]);
  "mutual recursion", "recursive async function", (let* push = push in Foreign.source [
    fn "left" [db] unit (RCall ("right", [RVar 0]));
    fn "right" [db] unit (RLet ("done", push, RCall ("left", [RVar 1])))]);
  "direct closure", "async closure push", (let* row = row in Foreign.source [
    fn "push" [db; unit] unit (RForeign (row, [RVar 1]));
    fn "make" [db] (TyFunc (Tid "fn<struct tuple<>;struct tuple<>>")) (RLam (Fid "push", 1, [RVar 0]))]);
  "transitive closure", "async closure forward", (let* push = push in Foreign.source [
    fn "push" [db] unit push;
    fn "forward" [db; unit] unit (RCall ("push", [RVar 1]));
    fn "make" [db] (TyFunc (Tid "fn<struct tuple<>;struct tuple<>>")) (RLam (Fid "forward", 1, [RVar 0]))]);
  "async metadata drift", "foreign metadata differs", (let* row = row in
    Foreign.source [fn "push" [db] unit (RForeign ({row with effects=[]}, [RVar 0]))]);
  "missing async rule", "missing print rule", (let* row = row in
    Foreign.source [fn "push" [db] unit (RForeign ({row with schema="missing"}, [RVar 0]))]);
]
let mixed = let* row = row in Foreign.source [
  fn "bump" [unit] unit (RVar 0);
  fn "store" [db; unit] unit (RLet ("done", RForeign (row, [RVar 1]), RCall ("bump", [RVar 1])))]
let mixed_rows = ["async fn f_73746f7265", true; "f_62756d70(a1)?", true; "f_62756d70(a1).await", false]
let check () =
  let failures = List.filter_map (fun (name, expected, result) -> Result.fold
    ~ok:(fun _text -> Some (name ^ ": unexpectedly printed"))
    ~error:(fun error -> let text = Error.to_string error in
      if holds text expected then None else Some (name ^ ": " ^ text)) result) tests in
  let effects = let* row = row in
    let foreign row = let* _params, _result, _render, effect = Foreign.foreign_call Catalog.entries row in Ok effect in
    Effects.infer ~foreign ["first", RCall ("second", []); "second", RCall ("third", []);
      "third", RForeign (row, [RUnit]); "pure", RUnit;
      "capture", RLam (Fid "pure", 0, [RCall ("first", [])]);
      "factory", RLam (Fid "third", 0, [])] in
  let failures = Result.fold ~error:(fun error -> Error.to_string error :: failures)
    ~ok:(fun effects -> if effects = ["first", Effects.Async_db; "second", Effects.Async_db;
      "third", Effects.Async_db; "pure", Effects.Sync; "capture", Effects.Async_db; "factory", Effects.Sync]
      then failures else "effect propagation differs" :: failures) effects in
  let failures = Result.fold ~error:(fun error -> Error.to_string error :: failures)
    ~ok:(fun text -> List.filter_map (fun (needle, wanted) ->
      if Bool.equal (holds text needle) wanted then None else Some ("mixed call: " ^ needle))
      mixed_rows @ failures) mixed in
  if List.is_empty failures then Printf.printf "LAN-ASYNC-EMIT OK refusals=%d propagation=1\n" (List.length tests)
  else (List.iter prerr_endline failures; exit 1)
let () = check ()
