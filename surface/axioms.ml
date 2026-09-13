(** Stage F disclosure over the checked module, before crate selection.
    The ambient Nat and primitive entries are not module declarations.
    Arbitrary source postulates have no class in the four-class M0 policy. *)
open Kanon_kernel
module Target = Lanyard_target.Target_generated

type class_ = Framework | Foreign | Classical | Div
type item = { class_ : class_; name : string; statement : string }

let class_name = function
  | Framework -> "Framework"
  | Foreign -> "Foreign"
  | Classical -> "Classical"
  | Div -> "Div"

let classes = [ Framework; Foreign; Classical; Div ]

let foreign_schemas (program : Elab.lan_program) =
  let catalog = List.map (fun (entry : Target.entry) ->
    (Elab.target_name entry.name, entry.name)) Target.entries in
  catalog @ List.map (fun (instance : Elab.foreign_instance) ->
    (instance.instance_name, instance.schema.name)) program.instances

let classify schemas (name, entry) =
  match entry with
  | Global.Axiom axiom ->
      List.assoc_opt name schemas
      |> Option.to_result ~none:(Error.Cannot_infer
        ("axiom disclosure: unclassified postulate " ^ name
         ^ "; use axioms --names for declaration names"))
      |> Result.map (fun schema -> Some { class_ = Foreign; name;
        statement = Pp.term [] axiom.Global.ax_ty ^ " [schema=" ^ schema ^ "]" })
  | Global.Def definition ->
      Ok (if definition.Global.partial then
        Some { class_ = Div; name; statement = Pp.term [] definition.Global.ty }
      else None)
  | Global.Prim _primitive -> Ok None

let definitions rows =
  List.fold_left (fun count (_name, entry) -> match entry with
    | Global.Def definition -> if definition.Global.partial then count else count + 1
    | Global.Axiom _ | Global.Prim _ -> count) 0 rows

let report (program : Elab.lan_program) : (string, Error.t) result =
  let schemas = foreign_schemas program in
  List.fold_left (fun result row ->
    Result.bind result (fun items ->
      classify schemas row |> Result.map (fun item ->
        Option.fold ~none:items ~some:(fun item -> item :: items) item)))
    (Ok [ { class_ = Framework; name = "imax_zero";
            statement = "imax l zero = zero" } ]) program.rows
  |> Result.map (fun items ->
    let grouped = List.map (fun class_ ->
      let members = List.filter (fun item -> item.class_ = class_) items
        |> List.sort (fun left right -> String.compare left.name right.name) in
      (class_, members, List.length members)) classes in
    let foreign_count = List.fold_left (fun total (class_, _members, size) ->
      match class_ with
      | Foreign -> total + size
      | Framework | Classical | Div -> total) 0 grouped in
    let entries = List.concat_map (fun (_class, members, _size) ->
      List.map (fun item -> Printf.sprintf "%s %s : %s\n"
        (class_name item.class_) item.name item.statement) members) grouped in
    let counts = List.map (fun (class_, _members, size) ->
      Printf.sprintf "COUNT %s=%d\n" (class_name class_) size) grouped in
    Printf.sprintf "AXIOMS scope=checked-module target-sha256=%s\n"
      Target.signature_sha256
    ^ String.concat "" (entries @ counts)
    ^ Printf.sprintf "AXIOMS total=%d\n" (List.length items)
    ^ Printf.sprintf "AXIOM-RATIO constants=%d definitions=%d status=REPORTED\n"
        foreign_count (definitions program.rows))
