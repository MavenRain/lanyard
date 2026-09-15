(** The lanyard driver.  M0 Stage A deletes the wasm back end at the
    fork point, so the driver holds check, axioms and spec-count.
    The first Stage E slice also prints native Rust through emit --native.
    Target slices print synchronous and async foreign constants through --target.
    The crate command writes a standalone target program with a main entry point.
    The build command emits that crate and reports the Cargo subprocess time.
    The run command interprets checked IR with a private in-memory model store.
    With --request URI the same command runs request mode: it validates the
    URI before any source I/O and exits 64 on a malformed one, calls the
    checked [Cx -> Uri -> SeeOther] entry point, exits 1 when the handler
    yields no response, and exits 0 with the 303 response on stdout.

    Exit codes.  0 is a file that checks, 1 is a file that does not and
    64 is a usage error or a missing file.  A check failure writes one
    [Error.to_string] line to stderr and nothing to stdout, so a caller
    reads stdout as the answer alone (SB-D5).  The build command forwards
    Cargo's own exit status after the crate is written, so 1, 64, 101, 127
    and 255 can come from Cargo; the refusals before Cargo keep the 0, 1
    and 64 meanings.

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
    ("usage: lanyard check [--print|--erased] FILE"
    ^ " | emit [--native|--target|--crate DIR [--print-model MODEL]] FILE.lan"
    ^ " | build --out DIR [--release] [--offline] [--print-model MODEL] FILE.lan"
    ^ " | run [--steps N] [--print-model MODEL | --request URI] FILE.lan"
    ^ " | axioms [--names] FILE | spec-count")

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

(** A source path names a .lan file with a stem, so a bare ".lan" is a
    usage error in every arm that takes a source path. *)
let lan_file (path : string) : bool =
  Filename.check_suffix path ".lan" && String.length (Filename.basename path) > 4

(** The flags the build command passes on. They are complete on their own,
    so the consumer never reads the parse accumulator. *)
type build_flags = {
  output : Lanyard_rust.Model.output;
  release : bool;
  offline : bool;
}

(** The parse accumulator. The output directory stays an option here to
    detect a repeat, and it leaves the parse as its own result, so no
    stale copy of it travels with the flags. *)
type build_options = {
  directory : string option;
  flags : build_flags;
}

(** Parse all options before checking or publishing the crate. Paths beginning
    with a dash can be written with an explicit relative or absolute prefix. *)
let rec build_options options args =
  let value text = not (String.starts_with ~prefix:"-" text) && text <> "" in
  match args with
  | "--out" :: directory :: rest when value directory && Option.is_none options.directory ->
      build_options { options with directory = Some directory } rest
  | "--print-model" :: model :: rest when value model ->
      (match options.flags.output with
       | Lanyard_rust.Model.Discard ->
           build_options
             { options with
               flags = { options.flags with output = Lanyard_rust.Model.Print_model model } }
             rest
       | Lanyard_rust.Model.Print_model _model -> Error ())
  | "--release" :: rest when not options.flags.release ->
      build_options { options with flags = { options.flags with release = true } } rest
  | "--offline" :: rest when not options.flags.offline ->
      build_options { options with flags = { options.flags with offline = true } } rest
  | [ path ] when value path && lan_file path ->
      options.directory |> Option.to_result ~none:()
      |> Result.map (fun directory -> options.flags, directory, path)
  | [] | _ :: _ -> Error ()

(** Cargo runs inside the fresh crate, so Cargo configuration follows the
    output directory. The command consists only of fixed, quoted arguments;
    source paths and output paths never become shell text. Sys.command keeps
    the child's streams and normal exit status; signals remain unsuccessful.
    A missing executable returns 127.
    The wall time is informational and excludes checking and emission.
    An I/O failure after the guards is loud, so the process exits 2 with
    the system error text, the same as the crate command. *)
let dispatch_build args =
  let initial = { directory = None;
                  flags = { output = Lanyard_rust.Model.Discard;
                            release = false; offline = false } } in
  build_options initial args
  |> Result.fold ~error:(fun () -> usage (); exit 64)
       ~ok:(fun (flags, directory, path) ->
         run_crate flags.output directory path;
         Sys.chdir directory;
         let command = ["cargo"; "build"]
           @ (if flags.release then ["--release"] else [])
           @ (if flags.offline then ["--offline"] else [])
           |> List.map Filename.quote |> String.concat " " in
         let started = Unix.gettimeofday () in
         let code = Sys.command command in
         let milliseconds = (Unix.gettimeofday () -. started) *. 1000. in
         Printf.eprintf "LANYARD-BUILD REPORTED cargo_exit=%d cargo_ms=%.3f\n%!"
           code milliseconds;
         exit code)

(** Source goes to stdout, or crate files to a fresh directory, only after
    the entire module prints. Emission never invokes Cargo or the program. *)
let dispatch_emit args =
  match args with
  | [ "--crate"; directory; "--print-model"; model; path ] when lan_file path ->
      run_crate (Lanyard_rust.Model.Print_model model) directory path
  | [ "--crate"; directory; path ] when lan_file path ->
      run_crate Lanyard_rust.Model.Discard directory path
  | [ "--native"; path ] when lan_file path ->
      Kanon_surface.Elab.check_lanyard (read_file path)
      |> Fun.flip Result.bind Kanon_surface.Lower.program
      |> Fun.flip Result.bind Lanyard_rust.Emit.native
      |> Result.fold ~ok:print_string ~error:(fun error ->
          prerr_endline (Kanon_kernel.Error.to_string error); exit 1)
  | [ "--target"; path ] when lan_file path ->
      Kanon_surface.Elab.check_lanyard (read_file path)
      |> Fun.flip Result.bind Lanyard_rust.Model.source
      |> Result.fold ~ok:print_string ~error:(fun error ->
          prerr_endline (Kanon_kernel.Error.to_string error); exit 1)
  | [] | _ :: _ -> usage (); exit 64

(** A run checks and lowers the file before evaluating main. Options are
    validated before source I/O, and no output is printed on a failed run.
    --request URI selects request mode: a malformed URI is a usage error
    here, before any file is read, and a run that yields no response
    exits 1 while a 303 response is printed on stdout with exit 0. *)
let rec run_options output request steps args =
  let value text = not (String.starts_with ~prefix:"-" text) && text <> "" in
  match args with
  | "--steps" :: amount :: rest when Option.is_none steps && value amount ->
      let number = if String.for_all (fun digit -> digit >= '0' && digit <= '9') amount
        then int_of_string_opt amount else None in
      number |> Option.to_result ~none:() |> Fun.flip Result.bind (fun number ->
        if number <= 0 || number > Lanyard_rust.Interp.max_steps then Error ()
        else run_options output request (Some number) rest)
  | "--request" :: uri :: rest when Option.is_none request && value uri ->
      (match output with
       | Lanyard_rust.Model.Discard ->
           Lanyard_rust.Run_http.uri uri |> Result.map_error (fun _error -> ())
           |> Fun.flip Result.bind (fun uri -> run_options output (Some uri) steps rest)
       | Lanyard_rust.Model.Print_model _model -> Error ())
  | "--print-model" :: model :: rest when Option.is_none request && value model ->
      (match output with
       | Lanyard_rust.Model.Discard ->
           run_options (Lanyard_rust.Model.Print_model model) request steps rest
       | Lanyard_rust.Model.Print_model _model -> Error ())
  | [path] when value path && lan_file path -> Ok (output, request, steps, path)
  | [] | _ :: _ -> Error ()

let dispatch_run args =
  run_options Lanyard_rust.Model.Discard None None args
  |> Result.fold ~error:(fun () -> usage (); exit 64)
       ~ok:(fun (output, request, steps, path) ->
         Kanon_surface.Elab.check_lanyard (read_file path)
         |> Fun.flip Result.bind (fun checked ->
              Option.fold ~none:(fun () -> Lanyard_rust.Interp.run ?steps ~output checked)
                ~some:(fun uri () -> Lanyard_rust.Interp.request ?steps ~uri checked) request ())
         |> Result.fold ~ok:(fun (_value, text) -> print_string text)
              ~error:(fun error ->
                prerr_endline (Kanon_kernel.Error.to_string error); exit 1))

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
  | "build" -> dispatch_build args
  | "run" -> dispatch_run args
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
