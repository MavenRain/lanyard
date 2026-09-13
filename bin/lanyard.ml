(** The lanyard driver.  M0 Stage A deletes the wasm back end at the
    fork point, so the driver holds check, axioms and spec-count.
    The first Stage E slice also prints native Rust through emit --native.
    Target slices print synchronous and async foreign constants through --target.
    The crate command writes a standalone target program with a main entry point.

    Exit codes.  0 is a file that checks, 1 is a file that does not and
    64 is a usage error or a missing file.  A check failure writes one
    [Error.to_string] line to stderr and nothing to stdout, so a caller
    reads stdout as the answer alone (SB-D5).

    Reading a file.  The whole repository holds one catch site, in
    test/main.ml, so this file reaches [In_channel] behind a
    [Sys.file_exists] guard (SB-D33) and reports a path it cannot see as
    a usage error.  A path that disappears between the guard and the
    read leaves the process, which is loud, and never a wrong answer.

    [Option.fold] reads its [~none] argument eagerly, so no arm of this
    file hides an [exit] behind it:  the two answers of a guard are an
    if and an else. *)

let usage () : unit =
  prerr_endline
    "usage: lanyard check [--print|--erased] FILE | emit [--native|--target|--crate DIR [--print-model MODEL]] FILE.lan | axioms [--names] FILE | spec-count"

let read_file (path : string) : string =
  if Sys.file_exists path then In_channel.with_open_bin path In_channel.input_all
  else (
    prerr_endline (Printf.sprintf "lanyard: cannot read %s" path);
    exit 64)

(** The file, checked, with the globals it was checked in.  M1 Stage G:
    a mu group leaves its family in those globals and adds no entry row,
    so erasure and emission read this pair and not the rows alone
    (brief 3.8). *)
let checked_in (path : string) :
    Kanon_kernel.Global.t * (string * Kanon_kernel.Global.entry) list =
  (if Filename.check_suffix path ".lan" then
     Kanon_surface.Elab.check_lanyard_in (read_file path)
   else Kanon_surface.Elab.check_in Kanon_kernel.Global.initial (read_file path))
  |> Result.fold
       ~ok:
         (fun
           (((g : Kanon_kernel.Global.t),
             (rows : (string * Kanon_kernel.Global.entry) list)))
         -> (g, rows))
       ~error:(fun (e : Kanon_kernel.Error.t) ->
         prerr_endline (Kanon_kernel.Error.to_string e);
         exit 1)

let checked (path : string) : (string * Kanon_kernel.Global.entry) list =
  snd (checked_in path)

(** Parse, elaborate and check one file against [Global.initial].  With
    the flag, print the checked form of every entry in order. *)
let run_check (print_form : bool) (path : string) : unit =
  let rows = checked path in
  if print_form then print_string (Kanon_surface.Elab.checked_form rows) else ()

(** "check --erased FILE" (SC-D1).  The file is checked first, so erasure
    never reads a declaration the kernel did not accept, and the erased
    program is printed in declaration order.  An erasure that refuses a
    declaration prints one error line and exits 1, exactly as a checker
    error does. *)
let run_erased (path : string) : unit =
  (if Filename.check_suffix path ".lan" then
     Result.bind (Kanon_surface.Elab.check_lanyard (read_file path))
       Kanon_surface.Lower.program
     |> Result.map Kanon_kernel.Erase.print
   else
     let globals, rows = checked_in path in
     Kanon_kernel.Erase_kan.program globals rows
     |> Result.map Kanon_kernel.Erase_kan.print)
  |> Result.fold
       ~ok:print_string
       ~error:(fun (e : Kanon_kernel.Error.t) ->
         prerr_endline (Kanon_kernel.Error.to_string e);
         exit 1)

(** R-Q3: the postulates of the file, one name per line, in declaration
    order.  A file with no postulate prints nothing. *)
let run_axiom_names (path : string) : unit =
  List.iter print_endline (Kanon_surface.Elab.axiom_names (checked path))

(** Lanyard reports the four M0 classes and the unbound ratio inputs.
    The carried .kan command keeps its declaration-name contract. *)
let run_axioms (path : string) : unit =
  if Filename.check_suffix path ".lan" then
    Kanon_surface.Elab.check_lanyard (read_file path)
    |> Fun.flip Result.bind Kanon_surface.Axioms.report
    |> Result.fold ~ok:print_string ~error:(fun error ->
        prerr_endline (Kanon_kernel.Error.to_string error); exit 1)
  else run_axiom_names path

let run_spec_count () : unit =
  Kanon_surface.Elab.target_environment ()
  |> Result.fold
       ~ok:(fun (_globals, _rows, foreign_types) ->
         print_string (Kanon_kernel.Spec_count.print ~foreign_types ()))
       ~error:(fun error ->
         prerr_endline (Kanon_kernel.Error.to_string error);
         exit 1)

(** A fresh directory prevents overwriting any existing output. The parent
    entries are read with [Sys.readdir], so a name that [Sys.file_exists]
    cannot see, a dangling symlink, is refused as well. The files go to a
    staging directory beside the destination and [Sys.rename] publishes
    them in one step, so a write that stops part way leaves the
    destination free and the next run is never blocked by half a crate.
    As with input reads, an I/O failure after the guards is loud, and it
    leaves the staging directory in place for inspection. All semantic
    validation finishes before any file is written. *)
let write_crate directory files =
  let parent = Filename.dirname directory in
  let staging = directory ^ ".partial" in
  let entry_at path =
    Sys.file_exists path
    || Array.exists (String.equal (Filename.basename path)) (Sys.readdir parent)
  in
  match () with
  | () when not (Sys.file_exists parent && Sys.is_directory parent) ->
      prerr_endline ("lanyard: output parent is not a directory: " ^ parent);
      exit 64
  | () when entry_at directory ->
      prerr_endline ("lanyard: output path exists: " ^ directory);
      exit 64
  | () when entry_at staging ->
      prerr_endline ("lanyard: output path exists: " ^ staging);
      exit 64
  | () ->
      Sys.mkdir staging 0o755;
      Sys.mkdir (Filename.concat staging "src") 0o755;
      List.iter (fun (path, contents) ->
        Out_channel.with_open_bin (Filename.concat staging path)
          (fun channel -> Out_channel.output_string channel contents)) files;
      Sys.rename staging directory

let run_crate (output : Lanyard_rust.Model.output) (directory : string)
    (path : string) : unit =
  Kanon_surface.Elab.check_lanyard (read_file path)
  |> Fun.flip Result.bind (Lanyard_rust.Crate.files ~output)
  |> Result.fold ~ok:(write_crate directory) ~error:(fun error ->
      prerr_endline (Kanon_kernel.Error.to_string error); exit 1)
(** Source goes to stdout, or crate files to a fresh directory, only after
    the entire module prints. Emission never invokes Cargo or the program. *)
let dispatch_emit args =
  match args with
  | [ "--crate"; directory; "--print-model"; model; path ] when Filename.check_suffix path ".lan" ->
      run_crate (Lanyard_rust.Model.Print_model model) directory path
  | [ "--crate"; directory; path ] when Filename.check_suffix path ".lan" ->
      run_crate Lanyard_rust.Model.Discard directory path
  | [ "--native"; path ] when Filename.check_suffix path ".lan" ->
      Kanon_surface.Elab.check_lanyard (read_file path)
      |> Fun.flip Result.bind Kanon_surface.Lower.program
      |> Fun.flip Result.bind Lanyard_rust.Emit.native
      |> Result.fold ~ok:print_string ~error:(fun error ->
          prerr_endline (Kanon_kernel.Error.to_string error); exit 1)
  | [ "--target"; path ] when Filename.check_suffix path ".lan" ->
      Kanon_surface.Elab.check_lanyard (read_file path)
      |> Fun.flip Result.bind Lanyard_rust.Model.source
      |> Result.fold ~ok:print_string ~error:(fun error ->
          prerr_endline (Kanon_kernel.Error.to_string error); exit 1)
  | [] | _ :: _ -> usage (); exit 64

(** "check [--print|--erased] FILE".  A flag is read before the path, so
    "check --print F", "check --erased F" and "check F" are the only
    three forms (SC-D1). *)
let dispatch_check (args : string list) : unit =
  match args with
  | "--print" :: path :: _rest -> run_check true path
  | [ "--print" ] ->
      usage ();
      exit 64
  | "--erased" :: path :: _rest -> run_erased path
  | [ "--erased" ] ->
      usage ();
      exit 64
  | path :: _rest -> run_check false path
  | [] ->
      usage ();
      exit 64

let dispatch_axioms (args : string list) : unit =
  match args with
  | [ "--names"; path ] when not (String.starts_with ~prefix:"--" path) ->
      run_axiom_names path
  | [ path ] when not (String.starts_with ~prefix:"--" path) -> run_axioms path
  | [] | _ :: _ -> usage (); exit 64

(* A string match cannot be exhaustive without a last arm, so the last arm
   binds the unknown command instead of writing a wildcard. *)
let dispatch (cmd : string) (args : string list) : unit =
  match cmd with
  | "spec-count" -> run_spec_count ()
  | "check" -> dispatch_check args
  | "axioms" -> dispatch_axioms args
  | "emit" -> dispatch_emit args
  | _unknown ->
      usage ();
      exit 64

let () =
  match Array.to_list Sys.argv with
  | [] ->
      usage ();
      exit 64
  | _prog :: rest -> (
      match rest with
      | [] ->
          usage ();
          exit 64
      | cmd :: args -> dispatch cmd args)
