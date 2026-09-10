open Kanon_kernel
open Rir
module Emit = Lanyard_rust.Emit
let nat = TyUnion (Tid "nat")
let nominal name = TyUnion (Tid ("mu<" ^ name ^ ">"))
let lit n = RLit (Literal.LInt (Bignum.of_int n))
let data tids = ("data", Erase.Code [RData (List.map (fun text -> Tid text) tids)])
let fn name params result body = (name, Erase.Code [RFun (Fid name, params, result, body)])
let n = data ["leg<mu<N>,0>"; "leg<mu<N>,1,union mu<N>>"]
let one = RTag (Tid "mu<N>", 1, [RTag (Tid "mu<N>", 0, [])])
let tests = [
  "missing signature metadata", "missing family metadata N", [fn "id" [nominal "N"] (nominal "N") (RVar 0)];
  "missing nested metadata", "missing family metadata Other", [data ["leg<mu<N>,0,union mu<Other>>"]];
  "sparse tags", "noncontiguous constructor tags N", [data ["leg<mu<N>,1>"]];
  "conflicting fields", "conflicting constructor metadata N",
    [data ["leg<mu<N>,0>"; "leg<mu<N>,0,union nat>"]];
  "negative tag", "invalid constructor tag", [data ["leg<mu<N>,-1>"]];
  "noncanonical tag", "invalid constructor tag", [data ["leg<mu<N>,00>"]];
  "nonnumeric tag", "constructor tag is not an integer", [data ["leg<mu<N>,x>"]];
  "truncated metadata", "malformed constructor metadata", [data ["leg<mu<N>,0"]];
  "incomplete metadata", "incomplete constructor metadata", [data ["leg<mu<N>>"]];
  "malformed family", "malformed family name", [data ["leg<mu<>,0>"]];
  "constructor arity", "constructor field count", [n; fn "main" [] (nominal "N") (RTag (Tid "mu<N>", 1, []))];
  "constructor tag bounds", "constructor tag 2 of N", [n; fn "main" [] (nominal "N") (RTag (Tid "mu<N>", 2, []))];
  "constructor type", "conversion from nat to nominal", [n; fn "main" [] (nominal "N") (RTag (Tid "mu<N>", 1, [lit 2]))];
  "case coverage", "family case coverage", [n; fn "main" [] nat (RCase (Tid "mu<N>", one, []))];
  "duplicate case", "family case coverage", [n; fn "main" [] nat (RCase (Tid "mu<N>", one,
    [{tag=0; arity=0; body=lit 1}; {tag=0; arity=0; body=lit 2}]))];
  "case arity", "family case binder count", [n; fn "main" [] nat (RCase (Tid "mu<N>", one,
    [{tag=0; arity=0; body=lit 1}; {tag=1; arity=0; body=lit 2}]))];
  "different nominal family", "conversion from nominal", [n; data ["leg<mu<Other>,0>"];
    fn "main" [] (nominal "Other") one];
  "unclosed family", "malformed family layout", [fn "id" [TyUnion (Tid "mu<N")] nat (lit 0)];
]
let contains text needle =
  List.init (String.length text + 1) Fun.id |> List.exists (fun offset ->
    String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop offset |> String.of_seq))
let () =
  let failures = List.filter_map (fun (name, expected, rows) ->
    Emit.native rows |> Result.fold ~ok:(fun _text -> Some (name ^ ": unexpectedly printed"))
      ~error:(fun error -> let text = Error.to_string error in
        if contains text expected then None else Some (name ^ ": " ^ text))) tests in
  let duplicates = [Emit.native [n; n; fn "main" [] (nominal "N") one]] in
  let duplicate = List.concat_map (fun result -> Result.fold ~ok:(fun _text -> [])
    ~error:(fun error -> [Error.to_string error]) result) duplicates in
  let failures = failures @ duplicate in
  if List.is_empty failures then Printf.printf "LAN-RECURSIVE-EMIT OK refusals=%d duplicates=%d\n"
    (List.length tests) (List.length duplicates)
  else (List.iter prerr_endline failures; exit 1)
