(** Select a crate's definitions before specialization and erasure. The complete
    file has already checked. Its globals stay available for type evaluation;
    source order, types, family fields and foreign schema arguments are retained. *)
open Kanon_kernel
module Elab = Kanon_surface.Elab
module Names = Set.Make (String)
let ( let* ) = Result.bind

let rec term names = function
  | Term.Var _ | Term.Univ _ | Term.Lit _ | Term.Auto -> names
  | Term.Global name -> Names.add name names
  | Term.Lan (s, body) | Term.Ran (s, body) -> term (shape names s) body
  | Term.In (s, address, args) -> terms (point (shape names s) address) args
  | Term.Out (s, address, head) -> term (point (shape names s) address) head
  | Term.Sec (s, legs) -> List.fold_left leg (shape names s) legs
  | Term.Elim e ->
      let names = term (shape names e.e_shape) e.e_scrut in
      let names = Option.fold ~none:names ~some:(fun (m : Term.motive) ->
        term (Option.fold ~none:names ~some:(fun name -> Names.add name names) m.m_ind)
          m.m_body) e.e_motive in
      List.fold_left (fun names (address, branch) -> leg (point names address) branch)
        names e.e_branches
  | Term.Let (_name, ty, value, body) -> terms names [ty; value; body]
  | Term.Ann (body, ty) -> terms names [body; ty]
and terms names sources = List.fold_left term names sources
and shape names s =
  let names = Option.fold ~none:names ~some:(fun name -> Names.add name names) (Shape.family s) in
  terms names (Shape.payload s)
and point names = function
  | Term.APt (_quantity, arg) -> term names arg
  | Term.ALeg _ | Term.ACtor _ -> names
and leg names (source : Term.leg) = term names source.l_body

let entry names = function
  | Global.Def definition -> terms names [definition.ty; definition.def]
  | Global.Axiom axiom -> term names axiom.ax_ty
  | Global.Prim primitive -> term names primitive.p_ty
let telescope names fields =
  List.fold_left (fun names (_quantity, _name, ty) -> term names ty) names fields
let family names (source : Positivity.family) =
  List.fold_left (fun names (ctor : Positivity.ctor) ->
    terms (telescope names ctor.c_args) ctor.c_res_idx)
    (telescope names (source.f_params @ source.f_indices)) source.f_ctors

let program root (checked : Elab.lan_program) =
  let instances = List.fold_left (fun table (instance : Elab.foreign_instance) ->
    Global.StringMap.add instance.instance_name instance table)
    Global.StringMap.empty checked.instances in
  let context = Check.make checked.globals Budget.unlimited in
  let dependencies name =
    let names = Option.fold ~none:Names.empty ~some:(entry Names.empty)
      (Global.find name checked.globals) in
    let names = Option.fold ~none:names ~some:(family names)
      (Global.find_family name checked.globals) in
    (* Quoted instance types can lose a model alias. Follow its retained schema
       arguments too, so equal layouts never merge distinct database models. *)
    Option.fold ~none:(Ok names) ~some:(fun (instance : Elab.foreign_instance) ->
      List.fold_left (fun acc (_parameter, syntax) ->
        let* names = acc in
        let* source = Elab.elab context ~expected:None syntax in
        Ok (term names source)) (Ok names) instance.type_arguments)
      (Global.StringMap.find_opt name instances) in
  let rec visit seen = function
    | [] -> Ok seen
    | name :: pending ->
        if Names.mem name seen then visit seen pending else
        let* next = dependencies name in
        visit (Names.add name seen) (Names.elements next @ pending) in
  let* names = visit Names.empty [root] in
  Ok { checked with
    rows = List.filter (fun (name, _entry) -> Names.mem name names) checked.rows;
    models = List.filter (fun (model : Elab.model_info) -> Names.mem model.model_name names) checked.models;
    instances = List.filter (fun (instance : Elab.foreign_instance) ->
      Names.mem instance.instance_name names) checked.instances }
