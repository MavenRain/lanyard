(** A standalone target crate uses the same printer and checked entry point as
    module emission. Dependency revisions are checked against target/PIN.json
    by the crate gate. Files are returned before the driver writes anything. *)
type transport = Batch | Http
let manifest_for transport =
  let tokio_features, topcoat_features = match transport with
    | Batch -> "\"rt\", \"macros\"", "\"router\""
    | Http -> "\"rt\", \"macros\", \"net\", \"sync\", \"time\"", "\"router\", \"serve\"" in
  {|[package]
name = "lanyard-program"
version = "0.0.0"
edition = "2024"
license = "MIT OR Apache-2.0"
publish = false

[workspace]

[dependencies]
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = [|} ^ tokio_features ^ {|] }
toasty = { git = "https://github.com/tokio-rs/toasty", rev = "7bd502cbf44cc47f70db9f2b27ab35d77a096364", default-features = false, features = ["sqlite"] }
topcoat = { git = "https://github.com/tokio-rs/topcoat", rev = "51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a", default-features = false, features = [|} ^ topcoat_features ^ {|] }
|}
let manifest = manifest_for Batch

let files ?output ?requests ?listen checked =
  let entrypoint = "main" in
  let ( let* ) = Result.bind in
  let* () = if Option.is_some requests && Option.is_some listen then
    Error (Kanon_kernel.Error.Mismatch "listen and requests are mutually exclusive") else Ok () in
  let* checked = Reachable.program entrypoint checked in
  let* checked =
    if List.is_empty checked.Kanon_surface.Elab.signatures then Ok checked else
    let* checked = Kanon_surface.Fuse.program checked in
    let* checked = Reachable.program entrypoint checked in
    Kanon_surface.Fuse.closed checked in
  let batch () = Option.fold
    ~none:(fun () -> Model.source ~entrypoint ?output checked)
    ~some:(fun script () ->
      let* () = match Option.value ~default:Model.Discard output with
        | Model.Discard -> Ok ()
        | Model.Print_model _name ->
            Error (Kanon_kernel.Error.Mismatch "request sessions cannot print a model") in
      let* entry_output, input_text = Session_emit.entry checked script in
      Model.source ~entrypoint ~entry_output ~input_text checked) requests () in
  let* source = Option.fold ~none:batch ~some:(fun address () ->
    let* () = match Option.value ~default:Model.Discard output with
      | Model.Discard -> Ok ()
      | Model.Print_model _name -> Error (Kanon_kernel.Error.Mismatch "HTTP listeners cannot print a model") in
    let* entry_output, input_text = Server_emit.entry checked address in
    Model.source ~entrypoint ~entry_output ~input_text ~http_input:true checked) listen () in
  let manifest = Option.fold ~none:manifest ~some:(fun _address -> manifest_for Http) listen in
  Ok source
  |> Result.map (fun source -> ["Cargo.toml", manifest; "src/main.rs", source])
