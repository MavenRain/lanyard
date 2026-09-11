open Kanon_kernel
open Rir
module Foreign = Lanyard_rust.Foreign
module Catalog = Lanyard_target.Target_generated
module Printer = Foreign.Printer
let ( let* ) = Result.bind
let nat = TyUnion (Tid "nat")
let unit = TyStruct (Tid "tuple<>")
let uri = TyForeign ("Uri", [])
let applied name arguments = TyForeign (name, arguments)
let form = applied "Form" [uri]
let fn params result body = "id", Erase.Code [RFun (Fid "id", params, result, body)]
let emit ty = Foreign.source [fn [ty] ty (RVar 0)]
let holds text needle = List.init (String.length text + 1) Fun.id |> List.exists (fun index ->
  String.starts_with ~prefix:needle (String.to_seq text |> Seq.drop index |> String.of_seq))
let edit change = List.map (fun (entry : Catalog.entry) ->
  if String.equal entry.name "Form" then change entry else entry) Catalog.entries
let changed change = Foreign.foreign_type (edit change) "Form" ["Nat"]
let parsed text = Printer.representation text |> Result.map Printer.rust_type
let refusals = [
  "missing argument", "foreign type argument count: Form", emit (applied "Form" []);
  "extra argument", "foreign type argument count: Form", emit (applied "Form" [uri; nat]);
  "applied atom", "foreign type argument count: Uri", emit (applied "Uri" [nat]);
  "unknown argument", "foreign type missing", emit (applied "Form" [applied "missing" []]);
  "wrong result", "conversion from", Foreign.source [fn [form] (applied "Form" [nat]) (RVar 0)];
  "shared to owned", "owned copy of a shared foreign value", Foreign.source [fn [TyArc form] form (RVar 0)];
  "owned clone", "clone of an owned foreign value", Foreign.source [fn [form] form (RClone (RVar 0))];
  "foreign tuple argument", "foreign aggregate layout", emit (applied "Form" [TyStruct (Tid "tuple<foreign Uri>")]);
  "closure argument", "foreign closure argument", emit (applied "Form" [TyFunc (Tid "fn<union nat;union nat>")]);
  "missing nominal metadata", "missing family metadata", emit (applied "Form" [TyUnion (Tid "mu<Missing>")]);
  "missing delimiter", "malformed foreign layout", parsed "foreign Form<foreign Uri";
  "extra delimiter", "unbalanced layout", parsed "foreign Form<foreign Uri>>";
  "layout arity", "foreign type argument count: Form", parsed "foreign Form<foreign Uri,union nat>";
  "runtime type parameter", "foreign type metadata", changed (fun entry -> {entry with kernel_type="(T : Type 0) -> Type 0"});
  "quantity drift", "foreign type metadata", changed (fun entry -> {entry with quantities=[Catalog.One]});
  "effect drift", "foreign type metadata", changed (fun entry -> {entry with effects=["DbExec"]});
  "result drift", "foreign type metadata", changed (fun entry -> {entry with kernel_type="(0 T : Type 0) -> Uri"});
  "deleted placeholder", "binding set differs", changed (fun entry -> {entry with print_rule="topcoat::router::content::Form<()>"});
  "wrong placeholder", "binding set differs", changed (fun entry -> {entry with print_rule="topcoat::router::content::Form<#{U}>"});
  "native refusal", "foreign type Uri", Lanyard_rust.Emit.native [fn [form] form (RVar 0)];
]
let positives = [
  "nested type", "topcoat::router::content::Form<toasty::Deferred<topcoat::router::Uri>>",
    emit (applied "Form" [applied "Deferred" [uri]]);
  "shared result", "Arc<topcoat::router::content::Form<topcoat::router::Uri>>",
    Foreign.source [fn [TyArc form] (TyArc form) (RClone (RVar 0))];
  "aggregate argument", "struct T70726f64756374286e61742c6e617429",
    emit (applied "Form" [TyStruct (Tid "tuple<union nat,union nat>")]);
  "nested layout", "topcoat::router::content::Form<toasty::Deferred<topcoat::router::Uri>>",
    parsed "foreign Form<foreign Deferred<foreign Uri>>";
  "unit argument", "toasty::Deferred<()>", emit (applied "Deferred" [unit]);
  "shared argument", "toasty::Deferred<Arc<Nat>>", emit (applied "Deferred" [TyArc nat]);
]
let check () =
  let failures = List.filter_map (fun (name, needle, result) -> Result.fold
    ~ok:(fun _text -> Some (name ^ ": unexpectedly printed"))
    ~error:(fun error -> let text = Error.to_string error in
      if holds text needle then None else Some (name ^ ": " ^ text)) result) refusals in
  let failures = failures @ List.filter_map (fun (name, needle, result) -> Result.fold
    ~ok:(fun text -> if holds text needle then None else Some (name ^ ": missing " ^ needle))
    ~error:(fun error -> Some (name ^ ": " ^ Error.to_string error)) result) positives in
  if List.is_empty failures then Printf.printf "LAN-FOREIGN-TYPES-EMIT OK positives=%d refusals=%d\n"
    (List.length positives) (List.length refusals)
  else (List.iter prerr_endline failures; exit 1)
let () = check ()
