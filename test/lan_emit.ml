open Kanon_kernel
open Rir
module Emit = Lanyard_rust.Emit
let nat = TyUnion (Tid "nat")
let lit n = RLit (Literal.LInt (Bignum.of_int n))
let function_row name params result body =
  (name, Erase.Code [ RFun (Fid name, params, result, body) ])
let drop n text = String.to_seq text |> Seq.drop n |> String.of_seq
(** A row passes only when the printer refuses with the diagnostic the row names.
    The expected text carries the constructor decoration of [Error.to_string], so a
    row pins the arm as well as the wording. *)
let holds text expected = List.init (String.length text + 1) Fun.id
  |> List.exists (fun index -> String.starts_with ~prefix:expected (drop index text))
let report expected rows = Emit.native rows |> Result.fold
  ~ok:(fun _code -> "printed a program")
  ~error:(fun error ->
    let text = Error.to_string error in
    if holds text expected then "" else text)
let term body = [ function_row "main" [] nat body ]
let prefix = "Rust emission: "
let mismatch text = "mismatch: " ^ prefix ^ text
let not_yet text = "not yet: " ^ prefix ^ text
let tests = [
  "negative literal", mismatch "negative Nat literal", term (lit (-1));
  "negative slot", mismatch "negative runtime index", term (RVar (-1));
  "missing slot", mismatch "runtime index 0", term (RVar 0);
  "unresolved global", not_yet "unresolved global unknown", term (RGlobal "unknown");
  "missing function", not_yet "native call unknown", term (RCall ("unknown", []));
  "call arity", mismatch "argument count",
    [ function_row "id" [nat] nat (RVar 0); function_row "main" [] nat (RCall ("id", [])) ];
  "primitive arity", mismatch "argument count", term (RCall ("natAdd", [lit 1]));
  "projection bounds", mismatch "runtime index 1",
    term (RProj (Tid "tuple<union nat>", 1, RStruct (Tid "tuple<union nat>", [lit 1])));
  "tag bounds", mismatch "runtime index 1", term (RTag (Tid "sum<union nat>", 1, [lit 1]));
  "case coverage", mismatch "case coverage",
    term (RCase (Tid "sum<union nat>", RTag (Tid "sum<union nat>", 0, [lit 1]), []));
  "case arity", mismatch "case binder count",
    term (RCase (Tid "sum<union nat>", RTag (Tid "sum<union nat>", 0, [lit 1]),
      [ { tag = 0; arity = 0; body = lit 1 } ]));
  "bad result conversion", mismatch "conversion from unit to nat", term RUnit;
  "duplicate function", mismatch "duplicate function",
    [ function_row "main" [] nat (lit 1); function_row "main" [] nat (lit 2) ];
  "closure", mismatch "missing closure function unknown", term (RLam (Fid "unknown", 0, []));
  "closure call", mismatch "closure call needs a function", term (RCallC (RUnit, []));
  "untyped closure", mismatch "closure layout requires parameters and result",
    [function_row "untyped" [TyFunc (Tid "fn<1>")] nat (lit 1)];
  "closure result layout", not_yet "representation missing",
    [function_row "untyped" [TyFunc (Tid "fn<;missing>")] nat (lit 1)];
  "closure representation", mismatch "function representation needs closure layout",
    [function_row "untyped" [TyFunc (Tid "nat")] nat (lit 1)];
  "closure arity", mismatch "closure arity",
    [function_row "id" [nat] nat (RVar 0);
     function_row "main" [] nat (RLam (Fid "id", 2, []))];
  "negative closure arity", mismatch "closure arity",
    [function_row "id" [nat] nat (RVar 0);
     function_row "main" [] nat (RLam (Fid "id", -1, []))];
  "closure capture count", mismatch "capture count",
    [function_row "id" [nat; nat] nat (RVar 0);
     function_row "main" [] nat (RCallC (RLam (Fid "id", 1, []), [lit 1]))];
  "closure capture type", mismatch "conversion from unit to nat",
    [function_row "id" [nat; nat] nat (RVar 0);
     function_row "main" [] nat (RCallC (RLam (Fid "id", 1, [RUnit]), [lit 1]))];
  "closure argument count", mismatch "argument count",
    [function_row "id" [nat] nat (RVar 0);
     function_row "main" [] nat (RCallC (RLam (Fid "id", 1, []), []))];
  "closure argument type", mismatch "conversion from unit to nat",
    [function_row "id" [nat] nat (RVar 0);
     function_row "main" [] nat (RCallC (RLam (Fid "id", 1, []), [RUnit]))];
  "foreign call", not_yet "foreign call unknown",
    term (RForeign ({name="unknown"; schema="unknown"; print_rule="";
      effects=[]; type_arguments=[]; arity=0}, []));
]
let () =
  let failures = List.filter_map (fun (name, expected, rows) ->
    let text = report expected rows in
    if String.equal text "" then None else Some (name ^ ": " ^ text)) tests in
  if List.is_empty failures then Printf.printf "LAN-EMIT OK refusals=%d\n" (List.length tests)
  else (List.iter prerr_endline failures; exit 1)
