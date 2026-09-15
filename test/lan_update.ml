open Kanon_kernel
module Model = Lanyard_rust.Model
module Store = Lanyard_rust.Run_store
module V = Lanyard_rust.Run_value
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let base = "model Counter with | id : Nat | value : Nat end\n"
let source = base ^ "def main : Counter -> Db -> Counter := fun (fields : Counter) (db : Db) => Counter.update fields db"
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
let product fields = V.Product (Rir.Tid "tuple<union nat,union nat>", fields)
let row key value = product [nat key; nat value]
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
let after_update test =
  let* catalog, db, other_db, store = setup in
  let* value, store = call catalog "Counter_update" [row 7 23; db] store in
  test catalog db other_db value store
let metadata ?(rewrite = Fun.id) change_row change_entry =
  let* checked = checked in
  let* models = Model.catalog checked in
  let models = List.map (fun model -> {model with Model.instances = List.map rewrite model.Model.instances}) models in
  let* row = models |> List.concat_map (fun model -> model.Model.instances)
    |> List.find_opt (fun (row : Rir.foreign) -> row.schema = "Model.update")
    |> Option.to_result ~none:(Error.Unbound "Counter_update") in
  let entries = List.map (fun (entry : Catalog.entry) ->
    if entry.name = "Model.update" then change_entry entry else entry) Catalog.entries in
  Model.foreign_call entries models (change_row row)
let tests = [
  "checked model result", (let* checked = checked in
    let* text = Model.source checked in
    if contains text "toasty::update!(__lan_row { id: lan_model_to_i64(&__lan_value.f0)?"
       && contains text "::get_by_id(&mut __lan_db, &__lan_fields.id).await?"
    then Ok () else fail "missing pinned update call");
  "model representation", (let* inputs, result, _render, effects = metadata Fun.id Fun.id in
    equal ([Rir.TyArc result; Rir.TyArc (Rir.TyForeign ("Db", []))], Lanyard_rust.Effects.Async_db)
      (Ok (inputs, effects)));
  "wrong checked result", refuses "mismatch" (Kanon_surface.Elab.check_lanyard
    (base ^ "def main : Counter -> Db -> prod () := fun (fields : Counter) (db : Db) => Counter.update fields db"));
  "update returns replacement", after_update (fun _catalog _db _other_db value _store -> equal (row 7 23) (Ok value));
  "updated row stored", after_update (fun catalog db _other_db _value store ->
    equal (row 7 23) (call catalog "Counter_get_by_id" [nat 7; db] store |> Result.map fst));
  "other key preserved", after_update (fun catalog db _other_db _value store ->
    equal (row 8 99) (call catalog "Counter_get_by_id" [nat 8; db] store |> Result.map fst));
  "other model preserved", after_update (fun catalog db _other_db _value store ->
    equal (row 7 61) (call catalog "Other_get_by_id" [nat 7; db] store |> Result.map fst));
  "other database preserved", after_update (fun catalog _db other_db _value store ->
    equal (row 7 88) (call catalog "Counter_get_by_id" [nat 7; other_db] store |> Result.map fst));
  "repeated update", after_update (fun catalog db _other_db _value store ->
    equal (row 7 23, store) (call catalog "Counter_update" [row 7 23; db] store));
  "missing row refused", (let* catalog, db, _other_db, store = setup in
    refuses "model row not found" (call catalog "Counter_update" [row 90 23; db] store));
  "deleted row refused", (let* catalog, db, _other_db, store = setup in
    let* _unit, store = call catalog "Counter_delete_by_id" [nat 7; db] store in
    refuses "model row not found" (call catalog "Counter_update" [row 7 23; db] store));
  "schema required", (let* catalog = catalog in
    let db, store = Store.allocate ["Counter"] Store.empty in
    refuses "schema has not been initialized" (call catalog "Counter_update" [row 7 23; V.Database db.id] store));
  "model registration required", (let* catalog, _db, other_db, store = setup in
    refuses "model not registered" (call catalog "Other_update" [row 7 23; other_db] store));
  "row layout", (let* catalog, db, _other_db, store = setup in
    refuses "model result layout" (call catalog "Counter_update" [nat 7; db] store));
  "field count", (let* catalog, db, _other_db, store = setup in
    refuses "model result layout" (call catalog "Counter_update" [product [nat 7]; db] store));
  "field type", (let* catalog, db, _other_db, store = setup in
    refuses "natural number" (call catalog "Counter_update" [product [nat 7; V.Unit]; db] store));
  "field range", (let* catalog, db, _other_db, store = setup in
    let huge = V.Nat (Bignum.mul (Bignum.of_int 1000000000) (Bignum.of_int 10000000000)) in
    refuses "range" (call catalog "Counter_update" [product [nat 7; huge]; db] store));
  "key range", (let* catalog, db, _other_db, store = setup in
    let huge = V.Nat (Bignum.mul (Bignum.of_int 1000000000) (Bignum.of_int 10000000000)) in
    refuses "range" (call catalog "Counter_update" [product [huge; nat 23]; db] store));
  "invalid handle", (let* catalog, _db, _other_db, store = setup in
    refuses "unknown database" (call catalog "Counter_update" [row 7 23; V.Database 100] store));
  "runtime arity", (let* catalog, db, _other_db, store = setup in
    refuses "foreign argument count" (call catalog "Counter_update" [db] store));
  "runtime metadata", (let* catalog, db, _other_db, store = setup in
    let* entry = foreign catalog "Counter_update" in
    refuses "foreign metadata differs" (Store.foreign catalog {entry with effects = []} [row 7 23; db] store));
  "instance metadata", refuses "model metadata differs" (metadata (fun row -> {row with effects = []}) Fun.id);
  "schema effects", refuses "model schema metadata" (metadata Fun.id (fun entry -> {entry with effects = []}));
  "schema quantity", refuses "model schema metadata" (metadata Fun.id (fun entry -> {entry with quantities = []}));
  "schema type", refuses "model schema metadata" (metadata Fun.id (fun entry -> {entry with kernel_type = "Nat"}));
  "schema kind", refuses "model schema kind" (metadata Fun.id (fun entry -> {entry with kind = Catalog.Constant}));
  "checked arity", refuses "model schema metadata" (metadata ~rewrite:(fun row -> {row with arity = 1}) Fun.id Fun.id);
  "schema placeholders", refuses "model schema placeholders" (metadata
    ~rewrite:(fun row -> {row with print_rule = "#{M} #{fields}"}) Fun.id
    (fun entry -> {entry with print_rule = "#{M} #{fields}"}));
]
let () =
  let failures = List.filter_map (fun (name, result) -> Result.fold
    ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) tests in
  List.iter prerr_endline failures;
  Printf.printf "LAN-UPDATE %s checks=%d failures=%d\n"
    (if List.is_empty failures then "OK" else "FAIL") (List.length tests) (List.length failures);
  if not (List.is_empty failures) then exit 1
