(** The source grammar cannot yet construct Div. Exercise the carried
    checked-entry marker directly, without admitting partial source code. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Axioms = Kanon_surface.Axioms

let contains_all text expected =
  let lines = String.split_on_char '\n' text in
  List.for_all (fun needle -> List.exists (String.equal needle) lines) expected

let checked = Elab.check_lanyard "def main : Nat := 1\n"

let partial = Result.bind checked (fun program ->
  let rows = List.map (fun (name, entry) -> match entry with
    | Global.Def definition -> (name, Global.Def { definition with partial = true })
    | Global.Axiom _ | Global.Prim _ -> (name, entry)) program.Elab.rows in
  Axioms.report { program with rows })

let primitives = Result.bind checked (fun program ->
  let rows = Global.StringMap.bindings Global.initial.Global.entries
    |> List.filter (fun (_name, entry) -> match entry with
      | Global.Prim _ -> true
      | Global.Def _ | Global.Axiom _ -> false) in
  Axioms.report { program with rows = program.rows @ rows })

let cases = [
  "partial marker", partial,
    [ "Div main : Nat"; "COUNT Div=1"; "AXIOMS total=17";
      "AXIOM-RATIO constants=15 definitions=0 status=REPORTED" ];
  "primitive exclusion", primitives,
    [ "COUNT Div=0"; "AXIOMS total=16";
      "AXIOM-RATIO constants=15 definitions=1 status=REPORTED" ];
]

let () =
  let failures = List.filter_map (fun (name, result, expected) ->
    Result.fold ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error))
      ~ok:(fun text -> if contains_all text expected then None
        else Some (name ^ ": report differs\n" ^ text)) result) cases in
  if List.is_empty failures then
    Printf.printf "LAN-AXIOMS-REPORT OK observations=%d\n" (List.length cases)
  else (List.iter prerr_endline failures; exit 1)
