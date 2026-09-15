open Kanon_kernel
open Rir
module I = Lanyard_rust.Interp
module V = Lanyard_rust.Run_value
module Store = Lanyard_rust.Run_store
let ( let* ) = Result.bind
let lit number = RLit (Literal.LInt (Bignum.of_int number))
let nat number = V.Nat (Bignum.of_int number)
let nat_repr = TyUnion (Tid "nat")
let fn name arity body : I.fn = { name; params = List.init arity (fun _index -> nat_repr);
  result = nat_repr; body }
let context functions : I.context = { functions;
  foreign = { Store.models = []; connections = []; constants = [] } }
let eval ?(steps = I.default_steps) ?(functions = []) term =
  I.evaluate (context functions) 0 { I.steps; store = Store.empty } [] term |> Result.map fst
let source text = Kanon_surface.Elab.check_lanyard text
  |> Fun.flip Result.bind I.run |> Result.map fst
let equal expected result () =
  let* actual = result in
  if actual = expected then Ok () else Error (Error.Mismatch "unexpected interpreter value")
let contains text needle = List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
  String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let refuses needle result () = Result.fold
  ~ok:(fun _value -> Error (Error.Mismatch "expected interpreter refusal"))
  ~error:(fun error -> if contains (Error.to_string error) needle then Ok () else Error error) result
let tuple = Tid "tuple<union nat,union nat>"
let family = Tid "mu<Pair>"
(* The expected Boolean layout comes from the interpreter helper, which reads
   it from the model representation. No literal tag identity lives here. *)
let boolean tag result () =
  let* tid = I.boolean_tid in
  equal (V.Tag (tid, tag, [V.Unit])) result ()

let tests = [
  "checked bigint", equal (V.Nat (Bignum.mul (Bignum.of_int 1000000000) (Bignum.of_int 1000000000)))
    (source "def main : Nat := natMul 1000000000 1000000000");
  "checked closure", equal (nat 14) (source
    "def pack : Nat -> prod (Nat -> Nat) := fun (x : Nat) => tuple (fun (y : Nat) => natSub x y)\n def main : Nat := let f : Nat -> Nat := (pack 23).0 in f 9");
  "checked product", equal (nat 5) (source
    "def main : Nat := let pair : prod (Nat, Nat) := tuple (3, 5) in pair.1");
  "checked case", equal (nat 17) (source
    "def choose : sum (Nat, Nat) -> Nat := fun (x : sum (Nat, Nat)) => case x with | 0 (n : Nat) => natSub n 2 | 1 (n : Nat) => natSub n 3\n def main : Nat := choose (inj 1 of 2 20)");
  "checked recursive family", equal (nat 31) (source
    "mu List : Type 0 := | nil : List | cons (head : Nat) (tail : List) : List\n def rec sumList : List -> Nat := fun (xs : List) => match xs as self in List return Nat with | nil => 0 | cons head tail => natAdd head (sumList tail)\n def main : Nat := sumList (cons 7 (cons 11 (cons 13 nil)))");
  "unit", equal V.Unit (eval RUnit);
  "empty product", equal V.Unit (eval (RStruct (Tid "tuple<>", [])));
  "string literal", equal (V.Text "text") (eval (RLit (Literal.LString "text")));
  "global", equal (nat 8) (eval ~functions:[fn "answer" 0 (lit 8)] (RGlobal "answer"));
  "let and clone", equal (nat 9) (eval (RLet ("a", lit 9, RLet ("b", lit 3, RClone (RVar 1)))));
  "arguments in declaration order", equal (nat 14)
    (eval ~functions:[fn "subtract" 2 (RCall ("natSub", [RVar 1; RVar 0]))]
      (RCall ("subtract", [lit 23; lit 9])));
  "multiple closure captures", equal (nat 12)
    (eval ~functions:[fn "capture" 3 (RCall ("natSub", [RCall ("natSub", [RVar 2; RVar 1]); RVar 0]))]
      (RCallC (RLam (Fid "capture", 1, [lit 23; lit 9]), [lit 2])));
  "projection", equal (nat 9) (eval (RProj (tuple, 1, RStruct (tuple, [lit 3; lit 9]))));
  "case field order and outer scope", equal (nat 9)
    (eval (RLet ("outer", lit 2, RCase (family, RTag (family, 1, [lit 20; lit 9]),
      [{tag = 0; arity = 0; body = RVar 99}; {tag = 1; arity = 2;
        body = RCall ("natSub", [RCall ("natSub", [RVar 1; RVar 0]); RVar 2])}]))));
  "addition", equal (nat 32) (eval (RCall ("natAdd", [lit 23; lit 9])));
  "truncated subtraction", equal (nat 0) (eval (RCall ("natSub", [lit 9; lit 23])));
  "multiplication", equal (nat 207) (eval (RCall ("natMul", [lit 23; lit 9])));
  "equal true", boolean 1 (eval (RCall ("natEq", [lit 9; lit 9])));
  "equal false", boolean 0 (eval (RCall ("natEq", [lit 9; lit 23])));
  "less true", boolean 1 (eval (RCall ("natLt", [lit 9; lit 23])));
  "less false", boolean 0 (eval (RCall ("natLt", [lit 23; lit 9])));
  "native precedes primitive", equal (nat 4)
    (eval ~functions:[fn "natAdd" 2 (lit 4)] (RCall ("natAdd", [lit 23; lit 9])));
  "negative literal", refuses "natural number" (eval (lit (-1)));
  "unbound slot", refuses "index" (eval (RVar 0));
  "negative slot", refuses "index" (eval (RLet ("x", lit 1, RVar (-1))));
  "missing function", refuses "missing runtime function" (eval (RCall ("absent", [])));
  "function arity", refuses "argument count" (eval ~functions:[fn "f" 1 (RVar 0)] (RCall ("f", [])));
  "primitive arity", refuses "argument count" (eval (RCall ("natAdd", [lit 1])));
  "primitive type", refuses "natural number" (eval (RCall ("natAdd", [RUnit; lit 1])));
  "closure definition arity", refuses "closure argument count"
    (eval ~functions:[fn "f" 1 (RVar 0)] (RLam (Fid "f", 2, [])));
  "closure call arity", refuses "closure call argument count"
    (eval ~functions:[fn "f" 1 (RVar 0)] (RCallC (RLam (Fid "f", 1, []), [])));
  "non-closure call", refuses "expected a closure" (eval (RCallC (lit 1, [])));
  "projection identity", refuses "layout differs" (eval (RProj (Tid "other", 0, RStruct (tuple, [lit 1]))));
  "projection index", refuses "index" (eval (RProj (tuple, 1, RStruct (tuple, [lit 1]))));
  "case identity", refuses "layout differs" (eval (RCase (Tid "other", RTag (family, 0, []), [])));
  "missing branch", refuses "missing case branch" (eval (RCase (family, RTag (family, 0, []), [])));
  "branch arity", refuses "case binder count" (eval (RCase (family, RTag (family, 0, []),
    [{tag = 0; arity = 1; body = RUnit}])));
  "step bound", refuses "step limit" (eval ~steps:10 ~functions:[fn "forever" 0 (RCall ("forever", []))]
    (RCall ("forever", [])));
  "depth bound", refuses "nesting limit" (eval ~functions:[fn "forever" 0 (RCall ("forever", []))]
    (RCall ("forever", [])));
  "foreign refusal", (fun () ->
    let* checked = Kanon_surface.Elab.check_lanyard "def main : Nat := 1" in
    let* constants = Kanon_surface.Lower.catalog checked in
    let* row = List.find_opt (fun (row : Rir.foreign) -> row.schema = "topcoat.db") constants
      |> Option.to_result ~none:(Error.Mismatch "missing target row") in
    let row = { row with schema = "future.operation" } in
    refuses "foreign operation future.operation"
      (Store.foreign { Store.models = []; connections = []; constants = [row] } row [V.Unit] Store.empty) ());
]

let () =
  let results = List.map (fun (name, test) -> name, test ()) tests in
  let failures = List.filter_map (fun (name, result) -> Result.fold ~ok:(fun () -> None)
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) results in
  List.iter prerr_endline failures;
  if List.is_empty failures then Printf.printf "LAN-RUN OK observations=%d\n" (List.length tests)
  else exit 1
