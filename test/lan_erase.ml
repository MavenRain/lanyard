open Kanon_kernel
open Kanon_surface
let ( let* ) = Result.bind

let lower source =
  let* checked = Elab.check_lanyard source in Lower.program checked

let contains text part =
  let n = String.length part in
  List.init (String.length text + 1) Fun.id |> List.exists (fun start ->
    String.equal (text |> String.to_seq |> Seq.drop start |> Seq.take n |> String.of_seq) part)

let printed source required forbidden () =
  let* rows = lower source |> Result.map_error Error.to_string in
  let text = Erase.print rows in
  if List.for_all (contains text) required &&
     List.for_all (fun part -> not (contains text part)) forbidden then Ok ()
  else Error ("unexpected Rust IR:\n" ^ text)

let refuses source word () =
  lower source |> Result.fold ~ok:(fun _rows -> Error "unsupported erasure accepted")
    ~error:(fun error -> if contains (Error.to_string error) word then Ok ()
      else Error (Error.to_string error))

let foreign_metadata () =
  let* checked = Elab.check_lanyard
    "model Todo with | id : Nat | title : Nat end" |> Result.map_error Error.to_string in
  let* rows = Lower.catalog checked |> Result.map_error Error.to_string in
  List.find_opt (fun (row : Rir.foreign) -> String.equal row.name "Todo_create") rows
  |> Option.fold ~none:(Error "missing instance") ~some:(fun (row : Rir.foreign) ->
    if row.arity = 2 && row.schema = "Model.create" &&
       row.type_arguments = [ "M", "Todo" ] &&
       List.mem "DbExec" row.effects && contains row.print_rule "await?"
    then Ok () else Error "foreign metadata lost")

let foreign_arity () =
  let* checked = Elab.check_lanyard "model Todo with | id : Nat end"
    |> Result.map_error Error.to_string in
  let* rows = Lower.catalog checked |> Result.map_error Error.to_string in
  Rir.resolve ~known:[] rows (Rir.RCall ("Todo_create", [])) |> Result.fold
    ~ok:(fun _term -> Error "foreign call accepted missing arguments")
    ~error:(fun error -> if Error.message error = "foreign call arity: Todo_create"
      then Ok () else Error (Error.to_string error))

(** A binder the erasure dropped has no runtime value. A use of that
    binder at a runtime position is refused, never printed as unit. *)
let erased_binder () =
  let* checked = Elab.check_lanyard "def n : Nat := 5"
    |> Result.map_error Error.to_string in
  let* declared = Global.find "n" checked.globals
    |> Option.fold ~none:(Error "missing n") ~some:(fun (entry : Global.entry) ->
      match entry with
      | Global.Def row -> Ok row.Global.ty
      | Global.Axiom row -> Ok row.Global.ax_ty
      | Global.Prim row -> Ok row.Global.p_ty) in
  let* nat = Eval.eval checked.globals [] declared
    |> Result.map_error Error.to_string in
  let ec : Erase.ectx = {
    c = Check.bind "witness" Quantity.Many nat
      (Check.make checked.globals Budget.unlimited);
    slots = [ Erase.SDrop ]; self = "main" } in
  let ac : Erase.acc = { next = 0; lifted = []; groups = [] } in
  Erase.term ec ac ~tail:false ~expected:(Some nat) (Term.Var 0)
  |> Result.fold ~ok:(fun (_pair : Rir.rtm * Erase.acc) ->
      Error "erased binder reached the Rust IR")
    ~error:(fun error ->
      if String.equal (Error.message error)
        "Rust erasure: runtime use of an erased binder"
      then Ok () else Error (Error.to_string error))

let cases = [
  "many", printed "def identity : Nat -> Nat := fun (x : Nat) => x"
    [ "fun identity (Arc<union nat>)"; "RClone (RVar 0)" ] [];
  "one", printed "def identity : (1 x : Nat) -> Nat := fun (1 x : Nat) => x"
    [ "fun identity (union nat)"; "RVar 0" ] [ "RClone" ];
  "zero", printed "def main : (0 witness : Nat) -> Nat := fun (0 witness : Nat) => 7"
    [ "fun main ()"; "RLit 7" ] [ "RVar"; "RUnit" ];
  "unit-effect", printed "def main : Db -> prod () := fun (db : Db) => Db.push_schema db"
    [ "RForeign Db_push_schema [RClone (RVar 0)]" ] [];
  "unit-value", printed "def main : prod () := tuple ()" [ "fun main ()"; "RUnit" ] [];
  "unit-argument", printed "def main : prod () -> Nat := fun (unit : prod ()) => 1"
    [ "fun main (Arc<struct tuple<>>)" ] [];
  "erased-call", printed
    "def ignore : (0 witness : Nat) -> Nat -> Nat := fun (0 witness : Nat) (x : Nat) => x def main : Nat := ignore 9 3"
    [ "RCall ignore [RLit 3]" ] [ "RLit 9" ];
  "eta-many", printed "def identity : Nat -> Nat := fun (x : Nat) => x def alias : Nat -> Nat := identity"
    [ "RCall identity [RClone (RVar 0)]" ] [];
  "eta-one", printed "def identity : (1 x : Nat) -> Nat := fun (1 x : Nat) => x def alias : (1 x : Nat) -> Nat := identity"
    [ "RCall identity [RVar 0]" ] [ "RClone" ];
  "capture", printed "def pack : Nat -> prod (Nat -> Nat) := fun (x : Nat) => tuple (fun (y : Nat) => x)"
    [ "RLam pack$0 1 [RClone (RVar 0)]"; "fun pack$0 (Arc<union nat>, Arc<union nat>)" ] [];
  "projection", printed "def main : Nat := (tuple (1, 2) : prod (Nat, Nat)).1"
    [ "RProj"; "RStruct" ] [];
  "constructor", printed "mu N : Type 0 := | z : N | s (n : N) : N def main : N := s z"
    [ "RTag mu<N> 1 [RTag mu<N> 0 []]" ] [];
  "case", printed "def Opt : Type 0 := sum ((prod () : Type 0), Nat) def unwrap : Opt -> Nat := fun (x : Opt) => case x with | 0 (u : prod ()) => 0 | 1 (v : Nat) => v"
    [ "RCase"; "{0 1 (RLit 0)}"; "{1 1 (RClone (RVar 0))}" ] [];
  "let", printed "def main : Nat := let x : Nat := 8 in natAdd x x"
    [ "RLet x (RLit 8)"; "RCall natAdd [RClone (RVar 0); RClone (RVar 0)]" ] [];
  "global-value", printed "def n : Nat := 5 def m : Nat := natAdd n n"
    [ "fun n () : union nat := RLit 5";
      "fun m () : union nat := RCall natAdd [RCall n []; RCall n []]" ] [ "RGlobal n" ];
  "partial-application", refuses
    "def add : Nat -> Nat -> Nat := fun (x : Nat) (y : Nat) => natAdd x y def apply : (Nat -> Nat) -> Nat := fun (f : Nat -> Nat) => f 5 def main : Nat := apply (add 1)"
    "native call arity: add";
  "prim-partial-application", refuses
    "def apply : (Nat -> Nat) -> Nat := fun (f : Nat -> Nat) => f 5 def main : Nat := apply (natAdd 1)"
    "native call arity: natAdd";
  "erased-binder", erased_binder;
  "function-value", refuses
    "def identity : Nat -> Nat := fun (x : Nat) => x def apply : (Nat -> Nat) -> Nat := fun (f : Nat -> Nat) => f 5 def main : Nat := apply identity"
    "function value needs eta expansion: identity";
  "foreign-arity", foreign_arity;
  "foreign-metadata", foreign_metadata;
  "proof-erasure", printed "axiom P : Prop axiom proof : P def identity : P -> P := fun (p : P) => p"
    [ "erased proof"; "erased identity"; "erased Deferred" ] [ "fun identity" ];
  "explicit-unit-proof", printed "def P : Prop := (prod () : Prop) axiom proof : P"
    [ "erased proof" ] [ "axiom proof" ];
  "type-erasure", printed "def T : Type 0 := Nat def family : Type 0 -> Type 0 := fun (T : Type 0) => T"
    [ "erased T"; "erased family" ] [ "fun family" ];
  "unknown-value", refuses "axiom mystery : Nat def main : Nat := mystery"
    "Rust target metadata missing: mystery";
  "unknown-foreign", refuses "axiom mystery : Nat -> Nat def main : Nat := mystery 1"
    "Rust target metadata missing: mystery";
]

let () =
  let failed = List.filter_map (fun (name, test) -> test () |> Result.fold
    ~ok:(fun () -> print_endline ("LAN-ERASE " ^ name ^ " OK"); None)
    ~error:(fun error -> prerr_endline ("LAN-ERASE " ^ name ^ " FAIL: " ^ error); Some name)) cases in
  if List.is_empty failed then
    Printf.printf "LAN-ERASE OK cases=%d\n" (List.length cases)
  else exit 1
