(** Capture avoiding reconstruction for the checked handler specializer.
    Kernel terms and their rules stay unchanged. Every result is rechecked. *)
open Kanon_kernel

let rec map variables depth source =
  let term = map variables depth in
  let shape = shape variables depth in
  let point = point variables depth in
  let leg = leg variables depth in
  match source with
  | Term.Var index -> variables depth index
  | Term.Univ _ | Term.Global _ | Term.Lit _ | Term.Auto -> source
  | Term.Lan (s, body) -> Term.Lan (shape s, under variables depth s body)
  | Term.Ran (s, body) -> Term.Ran (shape s, under variables depth s body)
  | Term.In (s, address, args) -> Term.In (shape s, point address, List.map term args)
  | Term.Out (s, address, head) -> Term.Out (shape s, point address, term head)
  | Term.Sec (s, legs) -> Term.Sec (shape s, List.map leg legs)
  | Term.Let (name, ty, value, body) ->
      Term.Let (name, term ty, term value, map variables (depth + 1) body)
  | Term.Ann (body, ty) -> Term.Ann (term body, term ty)
  | Term.Elim e -> Term.Elim { e with
      e_shape = shape e.e_shape; e_scrut = term e.e_scrut;
      e_motive = Option.map (fun (m : Term.motive) ->
        { m with m_body = map variables (depth + List.length m.m_idx + 1) m.m_body }) e.e_motive;
      e_branches = List.map (fun (address, branch) -> point address, leg branch) e.e_branches }
and shape variables depth = function
  | Shape.SPi (q, name, ty) -> Shape.SPi (q, name, map variables depth ty)
  | Shape.SColl n -> Shape.SColl n
  | Shape.SPar (left, right) -> Shape.SPar (map variables depth left, map variables depth right)
  | Shape.SMu (name, args) -> Shape.SMu (name, List.map (map variables depth) args)
  | Shape.SNu (name, args) -> Shape.SNu (name, List.map (map variables depth) args)
and under variables depth s body =
  (* A dependent function type binds its domain in the codomain, so the body of
     Lan and Ran over SPi sits one binder deeper than the shape itself. *)
  match s with
  | Shape.SPi (_, _, _) -> map variables (depth + 1) body
  | Shape.SColl _ | Shape.SPar (_, _) | Shape.SMu (_, _) | Shape.SNu (_, _) ->
      map variables depth body
and point variables depth = function
  | Term.APt (q, arg) -> Term.APt (q, map variables depth arg)
  | Term.ALeg n -> Term.ALeg n
  | Term.ACtor name -> Term.ACtor name
and leg variables depth (source : Term.leg) =
  { source with l_body = map variables (depth + List.length source.l_binders) source.l_body }

let shift ?(depth = 0) amount = map (fun depth index ->
  Term.Var (if index < depth then index else index + amount)) depth

(** Arguments are supplied in binder order, outermost first. *)
let instantiate args =
  let values = List.rev args in
  map (fun depth index ->
    if index < depth then Term.Var index else
    let rec select index = function
      | [] -> Term.Var (depth + index)
      | value :: rest -> if Int.equal index 0 then shift depth value else select (index - 1) rest in
    select (index - depth) values) 0
