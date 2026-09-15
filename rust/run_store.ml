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
  | Context _ | Uri _ | See_other _ -> invalid "expected a database"

let replace database store = { store with databases =
  List.map (fun previous -> if previous.id = database.id then database else previous) store.databases }

let push arguments store = match arguments with
  | [handle] ->
      let* db = database handle store in
      Ok (Unit, replace { db with ready = true } store)
  | [] | _ :: _ -> invalid "schema argument count"

let model (model : Model.t) schema arguments store = match arguments with
  | [value; handle] ->
      let* db = database handle store in
      let* () = match () with
        | () when not (List.mem model.name db.models) -> invalid ("model not registered: " ^ model.name)
        | () when not db.ready -> invalid "database schema has not been initialized"
        | () -> Ok () in
      let* operation = Model.operation schema in
      let* key = match operation with
        | Model.Create | Model.Update -> key model value
        | Model.Get | Model.Delete -> scalar_nat value in
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
           Ok (Unit, replace { db with rows } store))
  | [] | _ :: _ -> invalid "model argument count"

type catalog = { models : Model.t list; connections : Connection.t list; constants : Rir.foreign list }
let foreign catalog (row : Rir.foreign) arguments store = match () with
  | () when List.length arguments <> row.arity -> invalid "foreign argument count"
  | () when String.equal row.schema "Db.connect" ->
      let* connection = List.find_opt (fun (connection : Connection.t) -> connection.row = row) catalog.connections
        |> Option.to_result ~none:(Error.Mismatch "run: connection metadata differs") in
      connect connection arguments store
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
