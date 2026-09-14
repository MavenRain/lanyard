(** Each connection owns an immutable, initially empty store. No host I/O. *)
open Kanon_kernel
open Run_value
type database = { id : int; models : string list; ready : bool;
  rows : (string * Bignum.t * Run_value.t) list }
type t = { next : int; databases : database list }
let empty = { next = 0; databases = [] }

let connect (connection : Connection.t) arguments store = match arguments with
  | [url] ->
      let* url = text ~what:"connection URL" connection.family url in
      if not (String.equal url "sqlite::memory:") then
        refuse "in-memory connection requires sqlite::memory:"
      else
        let database = { id = store.next; models = connection.models; ready = false; rows = [] } in
        Ok (Database database.id,
          { next = store.next + 1; databases = database :: store.databases })
  | [] | _ :: _ -> invalid "connection argument count"

let database value store = match value with
  | Database id -> List.find_opt (fun database -> database.id = id) store.databases
      |> Option.to_result ~none:(Error.Mismatch "run: unknown database handle")
  | Nat _ | Text _ | Unit | Product _ | Tag _ | Closure _ -> invalid "expected a database"

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
      let creating = String.equal schema "Model.create" in
      let* key = if creating then key model value else scalar_nat value in
      let previous = List.find_opt (fun (name, stored_key, _row) ->
        String.equal name model.name && Bignum.equal key stored_key) db.rows in
      (match () with
       | () when creating && Option.is_some previous ->
           invalid ("duplicate model key: " ^ model.name)
       | () when creating ->
           Ok (value, replace { db with rows = (model.name, key, value) :: db.rows } store)
       | () -> previous |> Option.to_result ~none:(Error.Mismatch ("run: model row not found: " ^ model.name))
           |> Result.map (fun (_name, _key, row) -> row, store))
  | [] | _ :: _ -> invalid "model argument count"

type catalog = { models : Model.t list; connections : Connection.t list; constants : Rir.foreign list }
let foreign catalog (row : Rir.foreign) arguments store = match () with
  | () when List.length arguments <> row.arity -> invalid "foreign argument count"
  | () when String.equal row.schema "Db.connect" ->
      let* connection = List.find_opt (fun (connection : Connection.t) -> connection.row = row) catalog.connections
        |> Option.to_result ~none:(Error.Mismatch "run: connection metadata differs") in
      connect connection arguments store
  | () when not (List.mem row catalog.constants) -> invalid "foreign metadata differs"
  | () when String.equal row.schema "Db.push_schema" -> push arguments store
  | () when String.equal row.schema "Model.create" || String.equal row.schema "Model.get_by_id" ->
      let* selected = List.find_opt (fun (model : Model.t) -> List.mem row model.instances) catalog.models
        |> Option.to_result ~none:(Error.Mismatch "run: unknown model instance") in
      model selected row.schema arguments store
  | () -> refuse ("foreign operation " ^ row.schema)
