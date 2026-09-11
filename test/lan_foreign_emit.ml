open Kanon_kernel
open Rir
module Foreign = Lanyard_rust.Foreign
module Template = Lanyard_rust.Template
module Catalog = Lanyard_target.Target_generated
let ( let* ) = Result.bind
let call = Template.call
let uri = TyForeign "Uri"
let response = TyForeign "SeeOther"
let fn name params result body = name, Erase.Code [RFun (Fid name, params, result, body)]
let holds text needle = List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
  String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let entry = Foreign.lookup Catalog.entries "topcoat.see_other"
let row = Result.map (fun (entry : Catalog.entry) ->
  {name="topcoat_see_other"; schema=entry.name; print_rule=entry.print_rule;
   effects=entry.effects; type_arguments=[]; arity=1}) entry
let emit_row edit = let* row = row in
  Foreign.source [fn "redirect" [TyArc uri] response (RForeign (edit row, [RVar 0]))]
let render text bindings = let* template = Template.parse text in Template.render template bindings
let catalog_call schema =
  let* entry = Foreign.lookup Catalog.entries schema in
  Foreign.foreign_call Catalog.entries {name=Kanon_surface.Elab.target_name schema; schema;
    print_rule=entry.print_rule; effects=entry.effects; type_arguments=[]; arity=1}
  |> Result.map (fun _signature -> "")
let edited edit = List.map (fun (entry : Catalog.entry) ->
  if String.equal entry.name "topcoat.see_other" then edit entry else entry) Catalog.entries
let catalog_row edit = let* row = row in
  Foreign.foreign_call (edited edit) row |> Result.map (fun _signature -> "")
let sum_tid = Tid "sum<struct tuple<>|struct tuple<>>"
let case_arms text = String.split_on_char '\n' text
  |> List.filter (fun line -> holds line "::V0(") |> String.concat "\n"
let shared_case = Foreign.source [fn "pick" [TyUnion sum_tid; TyArc uri] (TyArc uri)
  (RCase (sum_tid, RVar 1, [{tag=0; arity=1; body=RVar 1}; {tag=1; arity=1; body=RVar 1}]))]
  |> Result.map case_arms
let tests = [
  "empty rule", "empty template", Template.parse " " |> Result.map (fun _parts -> "");
  "unclosed slot", "unclosed placeholder", render "#{arg" [];
  "invalid slot", "invalid placeholder name", render "#{0arg}" [];
  "nested slot", "invalid placeholder name", render "#{#{arg}}" [];
  "missing binding", "binding set differs", render "#{arg}" [];
  "extra binding", "binding set differs", render "()" ["arg", "value"];
  "duplicate binding", "duplicate binding", render "#{arg}" ["arg", "a"; "arg", "b"];
  "missing runtime use", "runtime placeholder quantity",
    call ~parameters:["arg", Quantity.Many] ~types:[] ~arguments:["Arc::new(3)"] "()";
  "duplicated One", "runtime placeholder quantity",
    call ~parameters:["arg", Quantity.One] ~types:[] ~arguments:["3"] "(#{arg}, #{arg})";
  "runtime Zero", "runtime placeholder quantity",
    call ~parameters:["arg", Quantity.Zero] ~types:[] ~arguments:["3"] "#{arg}";
  "undeclared slot", "undeclared placeholder", call ~parameters:[] ~types:[] ~arguments:[] "#{arg}";
  "arity", "argument count", call ~parameters:["arg", Quantity.One] ~types:[] ~arguments:[] "#{arg}";
  "colliding type binding", "duplicate parameter",
    call ~parameters:["arg", Quantity.One] ~types:["arg", "Nat"] ~arguments:["3"] "#{arg}";
  "foreign rule drift", "foreign metadata differs", emit_row (fun row -> {row with print_rule="()"});
  "foreign effect drift", "foreign metadata differs", emit_row (fun row -> {row with effects=["DbExec"]});
  "foreign name drift", "foreign metadata differs", emit_row (fun row -> {row with name="forged"});
  "foreign type arguments", "foreign metadata differs", emit_row (fun row -> {row with type_arguments=["T", "Uri"]});
  "foreign arity", "foreign arity", emit_row (fun row -> {row with arity=0});
  "catalog quantity drift", "foreign quantities",
    catalog_row (fun entry -> {entry with quantities=[Catalog.One]});
  "non-atomic call type", "non-atomic foreign call type",
    catalog_row (fun entry -> {entry with kernel_type="(x : Deferred Uri) -> SeeOther"});
  "foreign missing rule", "missing print rule", emit_row (fun row -> {row with schema="missing"});
  "deleted catalog rule", "missing print rule", (let* row = row in
    Foreign.foreign_call (List.filter (fun (entry : Catalog.entry) ->
      not (String.equal entry.name row.schema)) Catalog.entries) row |> Result.map (fun _signature -> ""));
  "schema call", "foreign schema", catalog_call "Model.create";
  "type called", "type used as a call", catalog_call "Uri";
  "async constant", "effectful foreign call", catalog_call "Db.push_schema";
  "foreign argument count", "foreign argument count", (let* row = row in
    Foreign.source [fn "bad" [] response (RForeign (row, []))]);
  "foreign argument type", "conversion from unit", (let* row = row in
    Foreign.source [fn "bad" [] response (RForeign (row, [RUnit]))]);
  "unknown foreign type", "Rust emission: foreign type unknown", Foreign.source [fn "id" [TyForeign "unknown"] uri (RVar 0)];
  "parameterized type", "parameterized foreign type Deferred", Foreign.source [fn "id" [TyForeign "Deferred"] uri (RVar 0)];
  "shared opaque move", "Rust emission: owned copy of a shared foreign value", Foreign.source [fn "id" [TyArc response] response (RVar 0)];
  "owned opaque clone", "clone of an owned foreign value", Foreign.source [fn "copy" [response] (TyArc response) (RClone (RVar 0))];
  "foreign product", "foreign aggregate layout",
    Foreign.source [fn "pair" [TyStruct (Tid "tuple<foreign Uri>")] uri (RVar 0)];
  "foreign closure signature", "foreign aggregate layout",
    Foreign.source [fn "callback" [TyFunc (Tid "fn<foreign Uri;foreign Uri>")] uri (RVar 0)];
  "foreign nominal field", "foreign aggregate layout",
    Foreign.source ["data", Erase.Code [RData [Tid "leg<mu<Opaque>,0,foreign Uri>"]]];
  "owned foreign capture", "owned foreign closure capture", Foreign.source [
    fn "captured" [uri; TyUnion (Tid "nat")] (TyUnion (Tid "nat")) (RVar 0);
    fn "closure" [uri] (TyFunc (Tid "fn<union nat;union nat>")) (RLam (Fid "captured", 1, [RVar 0]))];
  "local foreign closure", "foreign aggregate layout", Foreign.source [
    fn "identity" [uri] uri (RVar 0);
    fn "local" [] (TyUnion (Tid "nat"))
      (RLet ("unused", RLam (Fid "identity", 1, []), RLit (Literal.LInt (Bignum.of_int 1))))];
]
let observations () =
  let* ordered = call ~parameters:["first", Quantity.One; "second", Quantity.One]
    ~types:[] ~arguments:["tick(&counter, 7)"; "tick(&counter, 11)"] "(#{second}, #{first})" in
  let* repeated = call ~parameters:["value", Quantity.Many] ~types:[]
    ~arguments:["Arc::new(tick(&counter, 13))"] "(*#{value}, *#{value})" in
  Ok ("fn template_order(counter: &std::cell::Cell<u32>) -> (u32, u32) { " ^ ordered ^ " }\n"
    ^ "fn template_repeat(counter: &std::cell::Cell<u32>) -> (u32, u32) { " ^ repeated ^ " }\n")
let check () =
  let failures = List.filter_map (fun (name, expected, result) -> Result.fold
    ~ok:(fun _text -> Some (name ^ ": unexpectedly printed"))
    ~error:(fun error -> let text = Error.to_string error in
      if holds text expected then None else Some (name ^ ": " ^ text)) result) tests in
  let positives = ["literal replacement", render "#{a}:#{b}" ["a", "#{b}"; "b", "ok"], "#{b}:ok";
    "type substitution", call ~parameters:[] ~types:["T", "Vec<u8>"; "unused", "Nat"]
      ~arguments:[] "make::<#{T}>()", "{ make::<Vec<u8>>() }";
    "shared foreign case", shared_case,
      "    Ok(match a0 { T73756d28756e69742c756e697429::V0(v2) => a1, "
      ^ "T73756d28756e69742c756e697429::V1(v2) => a1 })"] in
  let failures = failures @ List.filter_map (fun (name, result, expected) -> Result.fold
    ~ok:(fun text -> if String.equal text expected then None else Some (name ^ ": " ^ text))
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) positives in
  if List.is_empty failures then Printf.printf "LAN-FOREIGN-EMIT OK refusals=%d positives=%d\n"
    (List.length tests) (List.length positives)
  else (List.iter prerr_endline failures; exit 1)
let () = match Array.to_list Sys.argv with
  | [_program; "--observations"] -> observations () |> Result.fold ~ok:print_string
      ~error:(fun error -> prerr_endline (Error.to_string error); exit 1)
  | [_program] -> check ()
  | [] | _ :: _ -> prerr_endline "usage: lan_foreign_emit [--observations]"; exit 64
