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
  let* specialized = Lower.specialize checked in
  let* instances = Lower.connections specialized in
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
  "inline schema", "async fn f_6f70656e",
    emit (base ^ "def open : Bytes -> Db := fun (url : Bytes) => Db.connect Counter Bytes url");
  "inline beside alias", "async fn f_6f74686572",
    emit (base ^ alias ^ "def other : Bytes -> Db := fun (url : Bytes) => Db.connect Counter Bytes url");
  "annotated application", ".connect(&__lan_url).await?",
    emit (base ^ "def open : Bytes -> Db := fun (url : Bytes) => (Db.connect Counter Bytes : Bytes -> Db) url");
  "inline product", "toasty::models!(LanModel436f756e746572, LanModel4175646974)",
    emit (base ^ "model Audit with | id : Nat end\ndef open : Bytes -> Db := fun (url : Bytes) => Db.connect (prod (Counter, Audit)) Bytes url");
  "nullary connection", "async fn f_6f70656e",
    emit (base ^ "def open : Db := Db.connect Counter Bytes b\"sqlite::memory:\"");
  "nested let", "async fn f_6f70656e",
    emit (base ^ "def open : Bytes -> Db := fun (url : Bytes) => let saved : Bytes := url in Db.connect Counter Bytes saved");
  "fresh definition name", "async fn f_5f5f6c616e5f636f6e6e6563745f31(",
    emit (base ^ "def __lan_connect_0 : Nat := 17\ndef open : Bytes -> Db := fun (url : Bytes) => Db.connect Counter Bytes url");
  "fresh later name", "async fn f_5f5f6c616e5f636f6e6e6563745f31(",
    emit (base ^ "def open : Bytes -> Db := fun (url : Bytes) => Db.connect Counter Bytes url\ndef __lan_connect_0 : Nat := 19");
  "fresh family name", "async fn f_5f5f6c616e5f636f6e6e6563745f31(",
    emit (base ^ "mu __lan_connect_0 : Type 0 := | empty : __lan_connect_0\ndef open : Bytes -> Db := fun (url : Bytes) => Db.connect Counter Bytes url");
  "erased connection argument",
    "\nfn f_6b656570() -> Result<Nat, Error> {\n    f_69676e6f7265()\n}",
    emit (base ^ "def ignore : (0 ignored : Db) -> Nat := fun (0 ignored : Db) => 23\n"
      ^ "def keep : (0 M : Type 0) -> Nat := fun (0 M : Type 0) => ignore (Db.connect M Bytes b\"unused\")");
  "erased constructor field",
    "\nfn f_6b656570() -> Result<T6e6f6d696e616c28363a48696464656e29, Error> {\n    Ok(T6e6f6d696e616c28363a48696464656e29::V0(Box::new((Nat::decimal(\"29\")?,))))\n}",
    emit (base ^ "mu Hidden : Type 0 := | hidden (0 ignored : Db) (value : Nat) : Hidden\n"
      ^ "def keep : (0 M : Type 0) -> Hidden := fun (0 M : Type 0) => hidden (Db.connect M Bytes b\"unused\") 29");
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
  "inline impostor", "requires a declared model",
    emit (base ^ "def open : Bytes -> Db := fun (url : Bytes) => Db.connect Nat Bytes url");
  "open model argument", "connection type arguments must be closed",
    emit (base ^ "def open : (0 M : Type 0) -> Bytes -> Db := fun (0 M : Type 0) (url : Bytes) => Db.connect M Bytes url");
  "open text argument", "connection type arguments must be closed",
    emit (base ^ "def open : (0 T : Type 0) -> T -> Db := fun (0 T : Type 0) (url : T) => Db.connect Counter T url");
  "connection function value", "function value needs eta expansion",
    emit (base ^ "def open : Bytes -> Db := fun (url : Bytes) => let call : Bytes -> Db := Db.connect Counter Bytes in call url");
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
