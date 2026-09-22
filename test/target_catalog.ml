(* Stage B exercises the generated module through its public OCaml interface. *)
module Target = Lanyard_target.Target_generated

let create_schema () =
  Target.find "Model.create"
  |> Option.fold ~none:false ~some:(fun (entry : Target.entry) ->
         entry.quantities = [ Target.Zero; Target.Many; Target.Many ]
         && entry.effects = [ "DbExec"; "toasty::Error" ]
         && String.equal entry.print_rule
              "toasty::create!(#{M} { #{fields} }).exec(&mut #{db}).await?"
         && match entry.kind with
            | Target.Schema -> true
            | Target.Type_constant | Target.Constant -> false)

let rows = 43
let foreign_types = 9

let () =
  let ok =
    match () with
    | () when List.length Target.entries <> rows -> false
    | () when List.length Target.foreign_types <> foreign_types -> false
    | () when Option.is_some (Target.find "streaming_ssr") -> false
    | () when Option.is_some (Target.find "missing") -> false
    | () -> create_schema ()
  in
  if ok then Printf.printf "TARGET-CATALOG OK rows=%d foreign_types=%d\n" rows foreign_types
  else (prerr_endline "TARGET-CATALOG FAIL"; exit 1)
