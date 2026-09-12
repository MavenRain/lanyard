open Kanon_kernel
module Elab = Kanon_surface.Elab
module Model = Lanyard_rust.Model
module Connection = Lanyard_rust.Connection
module Lower = Kanon_surface.Lower
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let bytes = "mu Bytes : Type 0 := | bytesNil : Bytes | bytesCons (head : Nat) (tail : Bytes) : Bytes\n"
let base = bytes ^ "model Counter with | id : Nat | value : Nat end\n"
let alias = "def open : Bytes -> Db := Db.connect Counter Bytes\n"
let emit text = Elab.check_lanyard text |> Fun.flip Result.bind Model.source
let holds text needle = List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
  String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let metadata ?(rewrite = Fun.id) change_row change_entry =
  let* checked = Elab.check_lanyard (base ^ alias) in
  let* models = Model.catalog checked in
  let* instances = Lower.connections checked in
  let* connections = Connection.catalog checked (List.map (fun model -> model.Model.name, Model.rust_name model) models) instances in
  let connections = List.map (fun connection -> {connection with Connection.row = rewrite connection.Connection.row}) connections in
  let* connection = List.find_opt (fun _connection -> true) connections
    |> Option.to_result ~none:(Error.Unbound "open") in
  let entries = List.map (fun (entry : Catalog.entry) ->
    if String.equal entry.name "Db.connect" then change_entry entry else entry) Catalog.entries in
  Connection.foreign_call entries connections (change_row connection.row) |> Result.map (fun _call -> "printed")
let positives = [
  "connection", ".connect(&__lan_url).await?", emit (base ^ alias);
  "model product", "toasty::models!(LanModel436f756e746572, LanModel4175646974)",
    emit (base ^ "model Audit with | id : Nat | value : Nat end\n"
      ^ "def Models : Type 0 := prod (Counter, Audit)\ndef open : Bytes -> Db := Db.connect Models Bytes");
  "model alias", "toasty::models!(LanModel436f756e746572)",
    emit (base ^ "def Selected : Type 0 := Counter\ndef open : Bytes -> Db := Db.connect Selected Bytes");
  "text alias", "lan_model_text_to_4279746573(&__lan_url_arg)?",
    emit (base ^ "def Text : Type 0 := Bytes\ndef open : Text -> Db := Db.connect Counter Text");
  "propagation", "async fn f_63616c6c6572", emit (base ^ alias ^ "def caller : Bytes -> Db := fun (url : Bytes) => open url");
  "alternative family", "lan_model_text_to_4f6374657473",
    emit (base ^ "mu Octets : Type 0 := | nil : Octets | cons (head : Nat) (tail : Octets) : Octets\n"
      ^ "def open : Octets -> Db := Db.connect Counter Octets");
  "separate specializations", "toasty::models!(LanModel4175646974)",
    emit (base ^ "model Audit with | id : Nat | value : Nat end\n" ^ alias
      ^ "def other : Bytes -> Db := Db.connect Audit Bytes");
]
let refusals = [
  "not a model", "requires a declared model", emit (base ^ "def open : Bytes -> Db := Db.connect Nat Bytes");
  "structural impostor", "requires a declared model",
    emit (base ^ "def Fake : Type 0 := prod (Nat, Nat)\ndef open : Bytes -> Db := Db.connect Fake Bytes");
  "empty models", "at least one model", emit (base ^ "def open : Bytes -> Db := Db.connect (prod ()) Bytes");
  "duplicate models", "duplicate models",
    emit (base ^ "def open : Bytes -> Db := Db.connect (prod (Counter, Counter)) Bytes");
  "duplicate alias", "duplicate models", emit (base ^ "def Alias : Type 0 := Counter\n"
    ^ "def open : Bytes -> Db := Db.connect (prod (Counter, Alias)) Bytes");
  "Nat URL", "URL requires a byte list", emit (base ^ "def open : Nat -> Db := Db.connect Counter Nat");
  "reversed list", "URL requires a byte list",
    emit "mu Bytes : Type 0 := | cons (head : Nat) (tail : Bytes) : Bytes | nil : Bytes\nmodel Counter with | id : Nat end\ndef open : Bytes -> Db := Db.connect Counter Bytes";
  "inline schema", "metadata missing: Db_connect",
    emit (base ^ "def open : Bytes -> Db := fun (url : Bytes) => Db.connect Counter Bytes url");
  "schema remains scoped", "metadata missing: Db_connect",
    emit (base ^ alias ^ "def other : Bytes -> Db := fun (url : Bytes) => Db.connect Counter Bytes url");
  "forged name", "connection metadata differs", metadata (fun row -> {row with name="other"}) Fun.id;
  "forged model", "connection metadata differs", metadata (fun row -> {row with type_arguments=[]}) Fun.id;
  "forged arity", "connection metadata differs", metadata (fun row -> {row with arity=2}) Fun.id;
  "forged effect", "connection metadata differs", metadata (fun row -> {row with effects=[]}) Fun.id;
  "constant kind", "connection schema kind", metadata Fun.id (fun entry -> {entry with kind=Catalog.Constant});
  "type kind", "connection schema kind", metadata Fun.id (fun entry -> {entry with kind=Catalog.Type_constant});
  "quantity drift", "connection schema metadata", metadata Fun.id (fun entry -> {entry with quantities=[]});
  "effect drift", "connection schema metadata", metadata Fun.id (fun entry -> {entry with effects=[]});
  "result drift", "connection schema metadata", metadata Fun.id (fun entry -> {entry with kernel_type="(0 Models : Type 0) -> (0 Text : Type 0) -> (url : Text) -> Nat"});
  "template drift", "connection schema metadata", metadata Fun.id (fun entry -> {entry with print_rule="bad"});
  "missing model slot", "connection schema placeholders",
    metadata ~rewrite:(fun row -> {row with print_rule="#{url}"}) Fun.id (fun entry -> {entry with print_rule="#{url}"});
  "extra slot", "connection schema placeholders",
    metadata ~rewrite:(fun row -> {row with print_rule="#{Models} #{url} #{extra}"}) Fun.id
      (fun entry -> {entry with print_rule="#{Models} #{url} #{extra}"});
]
let () =
  let failures = List.filter_map (fun (name, needle, result) -> Result.fold
    ~ok:(fun _text -> Some (name ^ ": unexpectedly printed"))
    ~error:(fun error -> let text = Error.to_string error in
      if holds text needle then None else Some (name ^ ": " ^ text)) result) refusals in
  let failures = failures @ List.filter_map (fun (name, needle, result) -> Result.fold
    ~ok:(fun text -> if holds text needle then None else Some (name ^ ": missing " ^ needle))
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) positives in
  if List.is_empty failures then Printf.printf "LAN-CONNECTIONS-EMIT OK positives=%d refusals=%d\n"
    (List.length positives) (List.length refusals)
  else (List.iter prerr_endline failures; exit 1)
