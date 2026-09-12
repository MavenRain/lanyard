(** A standalone target crate uses the same printer and checked entry point as
    module emission. Dependency revisions are checked against target/PIN.json
    by the crate gate. Files are returned before the driver writes anything. *)
let manifest = {|[package]
name = "lanyard-program"
version = "0.0.0"
edition = "2024"
license = "MIT OR Apache-2.0"
publish = false

[workspace]

[dependencies]
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = ["rt", "macros"] }
toasty = { git = "https://github.com/tokio-rs/toasty", rev = "7bd502cbf44cc47f70db9f2b27ab35d77a096364", default-features = false, features = ["sqlite"] }
topcoat = { git = "https://github.com/tokio-rs/topcoat", rev = "51caa01dca3a8f20bdacfa771b1b8ac8b6f2668a", default-features = false, features = ["router"] }
|}

let files checked =
  let entrypoint = "main" in
  Result.bind (Reachable.program entrypoint checked) (Model.source ~entrypoint)
  |> Result.map (fun source -> ["Cargo.toml", manifest; "src/main.rs", source])
