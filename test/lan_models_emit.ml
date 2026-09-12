open Kanon_kernel
module Model = Lanyard_rust.Model
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let base = "model Counter with | id : Nat | value : Nat end\n"
let bit = "def Bit : Type 0 := sum ((prod () : Type 0), (prod () : Type 0))\n"
let emit text = Kanon_surface.Elab.check_lanyard text |> Fun.flip Result.bind Model.source
let create = base ^ "def main : Db -> Counter := fun (db : Db) => Counter.create (tuple (7, 42)) db"
let holds text needle = List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
  String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let metadata ?(rewrite = Fun.id) change_row change_entry =
  let* checked = Kanon_surface.Elab.check_lanyard create in
  let* models = Model.catalog checked in
  let models = List.map (fun model -> {model with Model.instances = List.map rewrite model.Model.instances}) models in
  let* row = models |> List.concat_map (fun model -> model.Model.instances)
    |> List.find_opt (fun (row : Rir.foreign) -> String.equal row.schema "Model.create")
    |> Option.to_result ~none:(Error.Unbound "Counter_create") in
  let entries = List.map (fun (entry : Catalog.entry) ->
    if String.equal entry.name "Model.create" then change_entry entry else entry) Catalog.entries in
  Model.foreign_call entries models (change_row row) |> Result.map (fun _call -> "printed")
let refusals = [
  "unit field", "model field Counter.value requires Nat or Bool",
    emit "model Counter with | id : Nat | value : prod () end";
  "non-Nat key", "model field Counter.id requires Nat",
    emit "model Counter with | id : Uri end";
  "opaque field", "model field Counter.value requires Nat or Bool",
    emit "model Counter with | id : Nat | value : Uri end";
  "Bool key", "model field Counter.id requires Nat",
    emit (bit ^ "model Counter with | id : Bit end");
  "payload sum", "model field Counter.value requires Nat or Bool",
    emit "model Counter with | id : Nat | value : sum ((prod () : Type 0), Nat) end";
  "three-unit sum", "model field Counter.value requires Nat or Bool",
    emit "model Counter with | id : Nat | value : sum ((prod () : Type 0), (prod () : Type 0), (prod () : Type 0)) end";
  "Bool name with unsupported layout", "model field Counter.value requires Nat or Bool",
    emit "def Bool : Type 0 := prod ()\nmodel Counter with | id : Nat | value : Bool end";
  "missing key", "needs an id field", emit "model Counter with | value : Nat end";
  "duplicate field", "duplicate declaration", emit "model Counter with | id : Nat | id : Nat end";
  "forged name", "unknown model instance", metadata (fun row -> {row with name="Other_create"}) Fun.id;
  "forged type", "model metadata differs", metadata (fun row -> {row with type_arguments=["M", "Other"]}) Fun.id;
  "forged arity", "model metadata differs", metadata (fun row -> {row with arity=1}) Fun.id;
  "forged effects", "model metadata differs", metadata (fun row -> {row with effects=[]}) Fun.id;
  "forged template", "model metadata differs", metadata (fun row -> {row with print_rule="bad"}) Fun.id;
  "constant kind", "model schema kind", metadata Fun.id (fun entry -> {entry with kind=Catalog.Constant});
  "type kind", "model schema kind", metadata Fun.id (fun entry -> {entry with kind=Catalog.Type_constant});
  "quantity drift", "model schema metadata", metadata Fun.id (fun entry -> {entry with quantities=[]});
  "effect drift", "model schema metadata", metadata Fun.id (fun entry -> {entry with effects=[]});
  "result drift", "model schema metadata", metadata Fun.id (fun entry -> {entry with kernel_type="(0 M : Type 0) -> (fields : M) -> (db : Db) -> Nat"});
  "deleted rule", "model schema metadata", metadata Fun.id (fun entry -> {entry with print_rule=""});
  "missing fields slot", "model schema placeholders",
    metadata ~rewrite:(fun row -> {row with print_rule="#{M}::get_by_id(&mut #{db}, &0).await?"}) Fun.id
      (fun entry -> {entry with print_rule="#{M}::get_by_id(&mut #{db}, &0).await?"});
  "extra slot", "model schema placeholders",
    metadata ~rewrite:(fun row -> {row with print_rule="#{M} #{fields} #{db} #{extra}"}) Fun.id
      (fun entry -> {entry with print_rule="#{M} #{fields} #{db} #{extra}"});
]
let positives = [
  "model declaration", "#[key]", emit base;
  "create", ".exec(&mut __lan_db).await?", emit create;
  "lookup", "::get_by_id(&mut __lan_db, &lan_model_to_i64(&__lan_value)?).await?",
    emit (base ^ "def main : Nat -> Db -> Counter := fun (id : Nat) (db : Db) => Counter.get_by_id id db");
  "alias", "id: i64", emit "def Key : Type 0 := Nat\nmodel Counter with | id : Key end";
  "keyword field", "f_74797065: i64", emit "model Counter with | id : Nat | type : Nat end";
  "range error", "ModelRange", emit create;
  "Bool field alias", "f_76616c7565: bool",
    emit (bit ^ "def State : Type 0 := Bit\nmodel Counter with | id : Nat | value : State end");
  "structural Bool", "f_76616c7565: bool",
    emit "model Counter with | value : sum ((prod () : Type 0), (prod () : Type 0)) | id : Nat end";
  "Bool name with Nat layout", "f_76616c7565: i64",
    emit "def Bool : Type 0 := Nat\nmodel Counter with | id : Nat | value : Bool end";
]
let () =
  let failures = List.filter_map (fun (name, needle, result) -> Result.fold
    ~ok:(fun _text -> Some (name ^ ": unexpectedly printed"))
    ~error:(fun error -> let text = Error.to_string error in
      if holds text needle then None else Some (name ^ ": " ^ text)) result) refusals in
  let failures = failures @ List.filter_map (fun (name, needle, result) -> Result.fold
    ~ok:(fun text -> if holds text needle then None else Some (name ^ ": missing " ^ needle))
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) positives in
  if List.is_empty failures then Printf.printf "LAN-MODELS-EMIT OK positives=%d refusals=%d\n"
    (List.length positives) (List.length refusals)
  else (List.iter prerr_endline failures; exit 1)
