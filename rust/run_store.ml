(** Each connection owns an immutable, initially empty store. No host I/O. *)
open Kanon_kernel
open Run_value
type database = { id : int; models : string list; ready : bool;
  rows : (string * Bignum.t * Run_value.t) list }
type t = { next : int; databases : database list }
let empty = { next = 0; databases = [] }

let allocate models store =
  let database = { id = store.next; models; ready = false; rows = [] } in
  database, { next = store.next + 1; databases = database :: store.databases }

let context models store =
  let database, store = allocate models store in
  Context database.id, store

let connect (connection : Connection.t) arguments store = match arguments with
  | [url] ->
      let* url = text ~what:"connection URL" connection.family url in
      if not (String.equal url "sqlite::memory:") then
        refuse "in-memory connection requires sqlite::memory:"
      else
        let database, store = allocate connection.models store in
        Ok (Database database.id, store)
  | [] | _ :: _ -> invalid "connection argument count"

let database value store = match value with
  | Database id -> List.find_opt (fun database -> database.id = id) store.databases
      |> Option.to_result ~none:(Error.Mismatch "run: unknown database handle")
  | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _
  | Context _ | Uri _ | See_other _ | Response_text _ | Response_html _ -> invalid "expected a database"

let replace database store = { store with databases =
  List.map (fun previous -> if previous.id = database.id then database else previous) store.databases }

let push arguments store = match arguments with
  | [handle] ->
      let* db = database handle store in
      Ok (Unit, replace { db with ready = true } store)
  | [] | _ :: _ -> invalid "schema argument count"

let model (model : Model.t) schema arguments store = match arguments with
  | [handle] when String.equal schema "Model.all" ->
      let* db = database handle store in
      let* () = match () with
        | () when not (List.mem model.name db.models) -> invalid ("model not registered: " ^ model.name)
        | () when not db.ready -> invalid "database schema has not been initialized"
        | () -> Ok () in
      let rows = List.filter (fun (name, _key, _row) -> String.equal name model.name) db.rows
        |> List.sort (fun (_left_name, left, _left_row) (_right_name, right, _right_row) -> Bignum.compare left right) in
      let tid = Erase.mu_tid (Model.rows_name model) in
      let value = List.fold_left (fun tail (_name, _key, row) -> Tag (tid, 1, [row; tail]))
        (Tag (tid, 0, [])) (List.rev rows) in
      Ok (value, store)
  | [value; handle] ->
      let* db = database handle store in
      let* () = match () with
        | () when not (List.mem model.name db.models) -> invalid ("model not registered: " ^ model.name)
        | () when not db.ready -> invalid "database schema has not been initialized"
        | () -> Ok () in
      let* operation = Model.operation schema in
      let* key = match operation with
        | Model.Create | Model.Update -> key model value
        | Model.Get | Model.Delete -> scalar_nat value
        | Model.All -> invalid "model argument count" in
      let previous () = List.find_opt (fun (name, stored_key, _row) ->
        String.equal name model.name && Bignum.equal key stored_key) db.rows in
      (match operation with
       | Model.Create when Option.is_some (previous ()) ->
           invalid ("duplicate model key: " ^ model.name)
       | Model.Create ->
           Ok (value, replace { db with rows = (model.name, key, value) :: db.rows } store)
       | Model.Get -> previous () |> Option.to_result ~none:(Error.Mismatch ("run: model row not found: " ^ model.name))
           |> Result.map (fun (_name, _key, row) -> row, store)
       | Model.Update ->
           let* _previous = previous () |> Option.to_result
             ~none:(Error.Mismatch ("run: model row not found: " ^ model.name)) in
           let rows = List.map (fun (name, stored_key, stored_row) ->
             let updated = if String.equal model.name name && Bignum.compare key stored_key = 0
               then value else stored_row in
             name, stored_key, updated) db.rows in
           Ok (value, replace { db with rows } store)
       | Model.Delete ->
           let rows = List.filter (fun (name, stored_key, _row) ->
             not (String.equal name model.name && Bignum.equal stored_key key)) db.rows in
           Ok (Unit, replace { db with rows } store)
       | Model.All -> invalid "model argument count")
  | [] | _ :: _ -> invalid "model argument count"

type catalog = { models : Model.t list; connections : Connection.t list;
  texts : Text_ops.t list; constants : Rir.foreign list }
let foreign catalog (row : Rir.foreign) arguments store = match () with
  | () when List.length arguments <> row.arity -> invalid "foreign argument count"
  | () when String.equal row.schema "Db.connect" ->
      let* connection = List.find_opt (fun (connection : Connection.t) -> connection.row = row) catalog.connections
        |> Option.to_result ~none:(Error.Mismatch "run: connection metadata differs") in
      connect connection arguments store
  | () when String.starts_with ~prefix:"Text." row.schema || String.equal row.schema "Uri.from_text"
      || String.equal row.schema "Uri.to_text"
      || String.equal row.schema "Uri.path" || String.equal row.schema "Uri.query"
       || String.equal row.schema "Form.field" || String.equal row.schema "Form.has" || String.equal row.schema "Response.text"
      || String.equal row.schema "Html.text" || String.equal row.schema "Response.html" ->
      let* operation = List.find_opt (fun (text : Text_ops.t) -> text.row = row) catalog.texts
        |> Option.to_result ~none:(Error.Mismatch "run: text metadata differs") in
      let* _contract = Text_ops.foreign_call Lanyard_target.Target_generated.entries catalog.texts row in
      (match arguments with
       | [value] when operation.operation = Text_ops.From_nat ->
           let* number = natural value in
           Ok (of_text operation.family (Bignum.to_string number), store)
       | [Uri uri] when Text_ops.input operation.operation = Text_ops.Request_uri ->
           let* uri = Run_http.uri uri in
           let* uri = Text_ops.uri_text operation.operation uri in
           Ok (of_text operation.family uri, store)
       | [_value] when Text_ops.input operation.operation = Text_ops.Request_uri -> invalid "expected a request URI"
       | [left; right] when operation.operation = Text_ops.Concat ->
           let* left = text ~what:"concat left" operation.family left in
           let* right = text ~what:"concat right" operation.family right in
           Ok (of_text operation.family (left ^ right), store)
       | [left; right] when operation.operation = Text_ops.Equal ->
           let* left = text ~what:"equal left" operation.family left in
           let* right = text ~what:"equal right" operation.family right in
           Ok (Tag (Text_ops.bool_tid, (if String.equal left right then 1 else 0), [Unit]), store)
       | [body; name] when operation.operation = Text_ops.Form_field ->
           let* body = text ~what:"form body" operation.family body in
           let* name = text ~what:"form field name" operation.family name in
           let* value = Form_data.field body name in
           Ok (of_text operation.family value, store)
       | [body; name] when operation.operation = Text_ops.Form_has ->
           let* body = text ~what:"form body" operation.family body in
           let* name = text ~what:"form field name" operation.family name in
           let* present = Form_data.has body name in
           Ok (Tag (Text_ops.bool_tid, (if present then 1 else 0), [Unit]), store)
       | [value] ->
           let* text = text ~what:"text operation" operation.family value in
           let* value = match operation.operation with
             | Text_ops.Trim -> Text_ops.trim text |> Result.map (of_text operation.family)
             | Text_ops.To_nat -> Text_ops.to_nat text |> Result.map (fun number -> Nat number)
             | Text_ops.Is_empty ->
                 Ok (Tag (Text_ops.bool_tid, (if String.equal text "" then 1 else 0), [Unit]))
             | Text_ops.Uri_from_text -> Run_http.uri text |> Result.map (fun uri -> Uri uri)
             | Text_ops.Response_text -> Ok (Response_text text)
             | Text_ops.Html_text -> Text_ops.html_text text |> Result.map (of_text operation.family)
             | Text_ops.Response_html -> Ok (Response_html text)
             | Text_ops.From_nat | Text_ops.Uri_to_text | Text_ops.Uri_path | Text_ops.Uri_query
             | Text_ops.Equal | Text_ops.Concat | Text_ops.Form_field | Text_ops.Form_has ->
                 invalid "text pair argument count" in
           Ok (value, store)
       | [] | _ :: _ -> invalid "text argument count")
  | () when not (List.mem row catalog.constants) -> invalid "foreign metadata differs"
  | () when String.equal row.schema "topcoat.db" ->
      (match arguments with
       | [Context id] ->
           let* _database = database (Database id) store in
           Ok (Database id, store)
       | [] | _ :: _ -> invalid "expected a request context")
  | () when String.equal row.schema "topcoat.see_other" ->
      (match arguments with
       | [Uri location] ->
           let* location = Run_http.uri location in
           Ok (See_other location, store)
       | [] | _ :: _ -> invalid "expected a request URI")
  | () when String.equal row.schema "Db.push_schema" -> push arguments store
  | () when Result.is_ok (Model.operation row.schema) ->
      let* selected = List.find_opt (fun (model : Model.t) -> List.mem row model.instances) catalog.models
        |> Option.to_result ~none:(Error.Mismatch "run: unknown model instance") in
      model selected row.schema arguments store
  | () -> refuse ("foreign operation " ^ row.schema)
