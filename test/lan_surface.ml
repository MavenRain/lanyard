open Kanon_kernel
open Kanon_surface

let ( let* ) = Result.bind

let accepts source () =
  Elab.check_lanyard source |> Result.map (fun _program -> ())
  |> Result.map_error Error.to_string

let refuses source expected () =
  Elab.check_lanyard source |> Result.fold
    ~ok:(fun _program -> Error "invalid source accepted")
    ~error:(fun error ->
      if String.equal (Error.message error) expected then Ok ()
      else Error (Error.to_string error))

let todo = "model Todo with | id : Nat | title : Nat | completed : Nat end\n"
let app = "signature App : Nat with | DbExec (db : Db) : Todo end\n"

let model_conversion () =
  let* program = Elab.check_lanyard todo |> Result.map_error Error.to_string in
  let* actual = Eval.eval program.globals [] (Term.Global "Todo")
    |> Result.map_error Error.to_string in
  let* expected = Elab.target_type "prod (Nat, Nat, Nat)" |> Result.map_error Error.to_string in
  let c = Check.make program.globals Budget.unlimited in
  let* term = Elab.elab c ~expected:None expected |> Result.map_error Error.to_string in
  let* value = Eval.eval program.globals [] term |> Result.map_error Error.to_string in
  let* same = Conv.conv_type Check.ops c actual value |> Result.map_error Error.to_string in
  if same && List.map (fun i -> i.Elab.instance_name) program.instances =
             [ "Todo_create"; "Todo_get_by_id" ] then Ok ()
  else Error "model representation or instances differ"

let catalog_refuses name ty kind expected () =
  let row : Elab.Target.entry = {
    name; kernel_type = ty; kind; quantities = []; effects = [];
    print_rule = name; status = Elab.Target.Proposed } in
  Elab.target_environment ~entries:(Elab.Target.entries @ [ row ]) ()
  |> Result.fold ~ok:(fun _catalog -> Error "invalid target row accepted")
    ~error:(fun error -> if String.equal (Error.message error) expected then Ok ()
      else Error (Error.to_string error))

let catalog () =
  let* _g, rows, atoms = Elab.target_environment () |> Result.map_error Error.to_string in
  if List.length rows = 15 && List.length atoms = 9 then Ok ()
  else Error "catalog inventory differs"

let cases = [
  "catalog", catalog;
  "model-conversion", model_conversion;
  "model-value", accepts (todo ^ "def item : Todo := tuple (1, 2, 0)");
  "model-create", accepts (todo ^
    "def create : Db -> Todo := fun (db : Db) => Todo.create (tuple (1, 2, 0)) db");
  "signature", accepts (todo ^ app ^
    "def main : App := App.pure 0\ndef step : Db -> App := fun (db : Db) => App.DbExec db (fun (t : Todo) => App.pure t.1)");
  "empty-signature", accepts "signature App : Nat with end def main : App := App.pure 1";
  "closed-inductive-response", accepts
    "mu Bytes : Type 0 := | nil : Bytes | cons (byte : Nat) (tail : Bytes) : Bytes signature App : Bytes with | Read : Bytes end";
  "inductive-exponent", refuses
    "mu Hidden : Type 0 := | wrap (fn : Nat -> Nat) : Hidden signature App : Nat with | Bad : Hidden end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "recursive-inductive-exponent", refuses
    "mu Hidden : Type 0 := | wrap (tail : Hidden) (fn : Nat -> Nat) : Hidden signature App : Nat with | Bad : Hidden end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "mutual-inductive-exponent", refuses
    "mutual mu A : Type 0 := | a (b : B) : A mu B : Type 0 := | b (a : A) (fn : Nat -> Nat) : B end signature App : Nat with | Bad : A end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "applied-first-order", accepts "signature App : Nat with | Read : Form Nat end";
  "mixed-declarations", accepts ("def Field : Type 0 := Nat\n" ^ todo ^
    "def n : Nat := 0\nsignature App : Field with | Read : Field end");
  "qualified-error", accepts "def identity : toasty::Error -> toasty::Error := fun (e : toasty::Error) => e";
  "duplicate-field", refuses "model Todo with | id : Nat | id : Nat end" "duplicate declaration id";
  "missing-key", refuses "model Todo with | title : Nat end" "model Todo needs an id field";
  "foreign-shadow", refuses "def Db : Type 0 := Nat" "duplicate declaration Db";
  "constructor-shadow", refuses "mu N : Type 0 with | Db : N" "duplicate declaration Db";
  "duplicate-operation", refuses "signature App : Nat with | Read : Nat | Read : Nat end"
    "duplicate declaration Read";
  "duplicate-argument", refuses "signature App : Nat with | Read (x : Nat) (x : Nat) : Nat end"
    "duplicate declaration x";
  "pure-collision", refuses "signature App : Nat with | pure : Nat end"
    "duplicate declaration App_pure";
  "exponent", refuses "signature App : Nat with | Bad : Nat -> Nat end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "alias-exponent", refuses "def Hidden : Type 0 := Nat -> Nat signature App : Nat with | Bad : Hidden end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "nested-exponent", refuses "signature App : Nat with | Bad : prod (Nat, Nat -> Nat) end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "applied-exponent", refuses "signature App : Nat with | Bad : Form (Nat -> Nat) end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "shadowed-response", refuses
    "signature App : Nat with | Bad (0 Nat : Type 0) : Nat end"
    "operation Bad: response must be first order through M2 (exponent or unsupported type)";
  "family-argument-shadow", refuses
    "signature App : Nat with | Bad (0 App : Type 0) : Nat end"
    "operation Bad: argument shadows signature App";
  "tenth-atom", catalog_refuses "Hidden" "Type 0" Elab.Target.Type_constant
    "R0-TARGET: foreign type constant outside closed atom list: Hidden";
  "mislabelled-atom", catalog_refuses "Hidden" "Type 0" Elab.Target.Constant
    "R0-TARGET: kind disagrees with checked type of Hidden";
  "parenthesized-atom", catalog_refuses "Hidden" "(Type 0)" Elab.Target.Type_constant
    "R0-TARGET: foreign type constant outside closed atom list: Hidden";
  "type-constructor", catalog_refuses "Hidden" "(0 T : Type 0) -> Type 0" Elab.Target.Type_constant
    "R0-TARGET: foreign type constant outside closed atom list: Hidden";
]

let () =
  let failures = List.filter_map (fun (name, run) -> run () |> Result.fold
    ~ok:(fun () -> None) ~error:(fun error -> Some (name ^ ": " ^ error))) cases in
  if List.is_empty failures then
    Printf.printf "LAN-SURFACE OK cases=%d\n" (List.length cases)
  else (List.iter prerr_endline failures; exit 1)
