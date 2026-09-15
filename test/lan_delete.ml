open Kanon_kernel
module Model = Lanyard_rust.Model
module Store = Lanyard_rust.Run_store
module V = Lanyard_rust.Run_value
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let base = "model Counter with | id : Nat | value : Nat end\n"
let source = base ^ "def main : Nat -> Db -> prod () := fun (key : Nat) (db : Db) => Counter.delete_by_id key db"
let checked = Kanon_surface.Elab.check_lanyard source
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
  let* _row, store = call catalog "Counter_create" [row 8 99; db] store in
  let* _row, store = call catalog "Other_create" [row 7 61; db] store in
  let* _row, store = call catalog "Counter_create" [row 7 88; other_db] store in
  Ok (catalog, db, other_db, store)
let after_delete test =
  let* catalog, db, other_db, store = setup in
  let* value, store = call catalog "Counter_delete_by_id" [nat 7; db] store in
  test catalog db other_db value store
let metadata ?(rewrite = Fun.id) change_row change_entry =
  let* checked = checked in
  let* models = Model.catalog checked in
  let models = List.map (fun model -> {model with Model.instances = List.map rewrite model.Model.instances}) models in
  let* row = models |> List.concat_map (fun model -> model.Model.instances)
    |> List.find_opt (fun (row : Rir.foreign) -> row.schema = "Model.delete_by_id")
    |> Option.to_result ~none:(Error.Unbound "Counter_delete_by_id") in
  let entries = List.map (fun (entry : Catalog.entry) ->
    if entry.name = "Model.delete_by_id" then change_entry entry else entry) Catalog.entries in
  Model.foreign_call entries models (change_row row)
let tests = [
  "checked unit result", (let* checked = checked in
    let* text = Model.source checked in
    if contains text "::delete_by_id(&mut __lan_db, lan_model_to_i64(&__lan_value)?).await?"
    then Ok () else fail "missing pinned delete call");
  "unit representation", (let* _inputs, result, _render, effects = metadata Fun.id Fun.id in
    equal (Rir.TyStruct (Rir.Tid "tuple<>"), Lanyard_rust.Effects.Async_db) (Ok (result, effects)));
  "wrong checked result", refuses "mismatch" (Kanon_surface.Elab.check_lanyard
    (base ^ "def main : Nat -> Db -> Counter := fun (key : Nat) (db : Db) => Counter.delete_by_id key db"));
  "delete returns unit", after_delete (fun _catalog _db _other_db value _store -> equal V.Unit (Ok value));
  "deleted row absent", after_delete (fun catalog db _other_db _value store ->
    refuses "model row not found" (call catalog "Counter_get_by_id" [nat 7; db] store));
  "other key preserved", after_delete (fun catalog db _other_db _value store ->
    equal (row 8 99) (call catalog "Counter_get_by_id" [nat 8; db] store |> Result.map fst));
  "other model preserved", after_delete (fun catalog db _other_db _value store ->
    equal (row 7 61) (call catalog "Other_get_by_id" [nat 7; db] store |> Result.map fst));
  "other database preserved", after_delete (fun catalog _db other_db _value store ->
    equal (row 7 88) (call catalog "Counter_get_by_id" [nat 7; other_db] store |> Result.map fst));
  "deleted key reusable", after_delete (fun catalog db _other_db _value store ->
    let* _row, store = call catalog "Counter_create" [row 7 23; db] store in
    equal (row 7 23) (call catalog "Counter_get_by_id" [nat 7; db] store |> Result.map fst));
  "repeated delete", after_delete (fun catalog db _other_db _value store ->
    equal (V.Unit, store) (call catalog "Counter_delete_by_id" [nat 7; db] store));
  "missing key", (let* catalog, db, _other_db, store = setup in
    equal (V.Unit, store) (call catalog "Counter_delete_by_id" [nat 90; db] store));
  "schema required", (let* catalog = catalog in
    let db, store = Store.allocate ["Counter"] Store.empty in
    refuses "schema has not been initialized" (call catalog "Counter_delete_by_id" [nat 7; V.Database db.id] store));
  "model registration required", (let* catalog, _db, other_db, store = setup in
    refuses "model not registered" (call catalog "Other_delete_by_id" [nat 7; other_db] store));
  "key type", (let* catalog, db, _other_db, store = setup in
    refuses "natural number" (call catalog "Counter_delete_by_id" [V.Unit; db] store));
  "key range", (let* catalog, db, _other_db, store = setup in
    let key = V.Nat (Bignum.mul (Bignum.of_int 1000000000) (Bignum.of_int 10000000000)) in
    refuses "range" (call catalog "Counter_delete_by_id" [key; db] store));
  "invalid handle", (let* catalog, _db, _other_db, store = setup in
    refuses "unknown database" (call catalog "Counter_delete_by_id" [nat 7; V.Database 100] store));
  "argument count", (let* catalog, db, _other_db, store = setup in
    refuses "foreign argument count" (call catalog "Counter_delete_by_id" [db] store));
  "runtime metadata", (let* catalog, db, _other_db, store = setup in
    let* row = foreign catalog "Counter_delete_by_id" in
    refuses "foreign metadata differs" (Store.foreign catalog {row with effects = []} [nat 7; db] store));
  "emitter metadata", refuses "model metadata differs" (metadata (fun row -> {row with arity = 1}) Fun.id);
  "emitter result drift", refuses "model schema metadata" (metadata Fun.id (fun entry ->
    {entry with kernel_type = "(0 M : Type 0) -> (0 Key : Type 0) -> (key : Key) -> (db : Db) -> M"}));
  "emitter effects drift", refuses "model schema metadata" (metadata Fun.id (fun entry -> {entry with effects = []}));
  "emitter kind drift", refuses "model schema kind" (metadata Fun.id (fun entry -> {entry with kind = Catalog.Constant}));
  "emitter key slot", refuses "model schema placeholders"
    (metadata ~rewrite:(fun row -> {row with print_rule = "#{M}::delete_by_id(&mut #{db}, 0).await?"}) Fun.id
      (fun entry -> {entry with print_rule = "#{M}::delete_by_id(&mut #{db}, 0).await?"}));
]
let () =
  let failures = List.filter_map (fun (name, result) -> Result.fold
    ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) tests in
  List.iter (fun failure -> prerr_endline ("LAN-DELETE FAIL " ^ failure)) failures;
  Printf.printf "LAN-DELETE %s checks=%d failures=%d\n"
    (if List.is_empty failures then "OK" else "FAIL") (List.length tests) (List.length failures);
  if not (List.is_empty failures) then exit 1
