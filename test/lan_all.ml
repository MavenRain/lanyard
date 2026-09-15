open Kanon_kernel
module Model = Lanyard_rust.Model
module Store = Lanyard_rust.Run_store
module V = Lanyard_rust.Run_value
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let base = "model Counter with | id : Nat | value : Nat end\n"
let checked = Kanon_surface.Elab.check_lanyard
  (base ^ "def main : Db -> Counter.rows := fun (db : Db) => Counter.all db")
let fail message = Error (Error.Mismatch message)
let contains text needle = List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
  String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let equal expected result = let* actual = result in
  if actual = expected then Ok () else fail "unexpected result"
let refuses needle result = Result.fold
  ~ok:(fun _value -> fail "expected refusal")
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let nat number = V.Nat (Bignum.of_int number)
let row key value = V.Product (Rir.Tid "tuple<union nat,union nat>", [nat key; nat value])
let rows values =
  let tid = Erase.mu_tid "Counter_rows" in
  List.fold_left (fun tail value -> V.Tag (tid, 1, [value; tail])) (V.Tag (tid, 0, [])) (List.rev values)
let catalog =
  let* checked = Kanon_surface.Elab.check_lanyard (base ^ "model Other with | id : Nat | value : Nat end") in
  let* models = Model.catalog checked in
  let* constants = Kanon_surface.Lower.catalog checked in
  Ok { Store.models; connections = []; texts = []; constants }
let foreign catalog name = List.find_opt (fun (row : Rir.foreign) -> row.name = name) catalog.Store.constants
  |> Option.to_result ~none:(Error.Unbound name)
let call catalog name arguments store =
  let* row = foreign catalog name in Store.foreign catalog row arguments store
let setup =
  let* catalog = catalog in
  let first, store = Store.allocate ["Counter"; "Other"] Store.empty in
  let second, store = Store.allocate ["Counter"] store in
  let db, other_db = V.Database first.id, V.Database second.id in
  let* _unit, store = Store.push [db] store in
  let* _unit, store = Store.push [other_db] store in
  let* _row, store = call catalog "Counter_create" [row 7 42; db] store in
  let* _row, store = call catalog "Counter_create" [row 20 99; db] store in
  let* _row, store = call catalog "Counter_create" [row 3 23; db] store in
  let* _row, store = call catalog "Other_create" [row 7 61; db] store in
  let* _row, store = call catalog "Counter_create" [row 7 88; other_db] store in
  Ok (catalog, db, other_db, store)
let metadata ?(rewrite = Fun.id) change_row change_entry =
  let* checked = checked in
  let* models = Model.catalog checked in
  let models = List.map (fun model -> {model with Model.instances = List.map rewrite model.Model.instances}) models in
  let* row = models |> List.concat_map (fun model -> model.Model.instances)
    |> List.find_opt (fun (row : Rir.foreign) -> row.schema = "Model.all")
    |> Option.to_result ~none:(Error.Unbound "Counter_all") in
  let entries = List.map (fun (entry : Catalog.entry) ->
    if entry.name = "Model.all" then change_entry entry else entry) Catalog.entries in
  Model.foreign_call entries models (change_row row)
let tests = [
  "checked ordered query", (let* checked = checked in
    let* source = Model.source checked in
    if contains source "::all().order_by("
      && contains source ".id().asc()).exec(&mut __lan_db).await?"
      && contains source "__lan_rows.into_iter().rev().try_fold("
    then Ok () else fail "missing ordered query or checked list conversion");
  "model list representation", (let* inputs, result, _render, effects = metadata Fun.id Fun.id in
    equal ([Rir.TyArc (Rir.TyForeign ("Db", []))], Rir.TyUnion (Erase.mu_tid "Counter_rows"),
      Lanyard_rust.Effects.Async_db) (Ok (inputs, result, effects)));
  "wrong result type", refuses "mismatch" (Kanon_surface.Elab.check_lanyard
    (base ^ "def main : Db -> Counter := fun (db : Db) => Counter.all db"));
  "constructor result type", refuses "not a constructor" (Kanon_surface.Elab.check_lanyard
    (base ^ "model Other with | id : Nat | value : Nat end\ndef main : Other.rows := Counter.nil"));
  "ascending keys and model isolation", (let* catalog, db, _other_db, store = setup in
    equal (rows [row 3 23; row 7 42; row 20 99], store) (call catalog "Counter_all" [db] store));
  "connection isolation", (let* catalog, _db, other_db, store = setup in
    equal (rows [row 7 88], store) (call catalog "Counter_all" [other_db] store));
  "empty result", (let* catalog = catalog in
    let db, store = Store.allocate ["Counter"] Store.empty in
    let handle = V.Database db.id in
    let* _unit, store = Store.push [handle] store in
    equal (rows [], store) (call catalog "Counter_all" [handle] store));
  "updated and deleted rows", (let* catalog, db, _other_db, store = setup in
    let* _row, store = call catalog "Counter_update" [row 7 100; db] store in
    let* _unit, store = call catalog "Counter_delete_by_id" [nat 3; db] store in
    equal (rows [row 7 100; row 20 99], store) (call catalog "Counter_all" [db] store));
  "snapshot survives later update", (let* catalog, db, _other_db, store = setup in
    let* snapshot, store = call catalog "Counter_all" [db] store in
    let* _row, _store = call catalog "Counter_update" [row 7 100; db] store in
    equal (rows [row 3 23; row 7 42; row 20 99]) (Ok snapshot));
  "schema required", (let* catalog = catalog in
    let db, store = Store.allocate ["Counter"] Store.empty in
    refuses "schema has not been initialized" (call catalog "Counter_all" [V.Database db.id] store));
  "model registration required", (let* catalog, _db, other_db, store = setup in
    refuses "model not registered" (call catalog "Other_all" [other_db] store));
  "unknown database", (let* catalog, _db, _other_db, store = setup in
    refuses "unknown database" (call catalog "Counter_all" [V.Database 100] store));
  "wrong handle type", (let* catalog, _db, _other_db, store = setup in
    refuses "expected a database" (call catalog "Counter_all" [nat 7] store));
  "runtime arity", (let* catalog, db, _other_db, store = setup in
    refuses "foreign argument count" (call catalog "Counter_all" [nat 7; db] store));
  "runtime metadata", (let* catalog, db, _other_db, store = setup in
    let* entry = foreign catalog "Counter_all" in
    refuses "foreign metadata differs" (Store.foreign catalog {entry with effects = []} [db] store));
  "instance metadata", refuses "model metadata differs" (metadata (fun row -> {row with type_arguments = []}) Fun.id);
  "schema effects", refuses "model schema metadata" (metadata Fun.id (fun entry -> {entry with effects = []}));
  "schema quantity", refuses "model schema metadata" (metadata Fun.id (fun entry -> {entry with quantities = []}));
  "schema type", refuses "model schema metadata" (metadata Fun.id (fun entry -> {entry with kernel_type = "Nat"}));
  "schema kind", refuses "model schema kind" (metadata Fun.id (fun entry -> {entry with kind = Catalog.Constant}));
  "checked arity", refuses "model schema metadata" (metadata ~rewrite:(fun row -> {row with arity = 2}) Fun.id Fun.id);
  "schema placeholders", refuses "model schema placeholders" (metadata
    ~rewrite:(fun row -> {row with print_rule = "#{M} #{db} #{unknown}"}) Fun.id
    (fun entry -> {entry with print_rule = "#{M} #{db} #{unknown}"}));
  "emitter argument count", (let* _inputs, _result, render, _effects = metadata Fun.id Fun.id in
    refuses "model argument count" (render ["value"; "db"]));
]
let () =
  let failures = List.filter_map (fun (name, result) -> Result.fold
    ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) tests in
  List.iter prerr_endline failures;
  Printf.printf "LAN-ALL %s checks=%d failures=%d\n"
    (if List.is_empty failures then "OK" else "FAIL") (List.length tests) (List.length failures);
  if not (List.is_empty failures) then exit 1
