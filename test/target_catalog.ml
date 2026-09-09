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

let () =
  if List.length Target.entries = 15
     && List.length Target.foreign_types = 9
     && Option.is_none (Target.find "streaming_ssr")
     && Option.is_none (Target.find "missing")
     && create_schema ()
  then print_endline "TARGET-CATALOG OK rows=15 foreign_types=9"
  else (prerr_endline "TARGET-CATALOG FAIL"; exit 1)
