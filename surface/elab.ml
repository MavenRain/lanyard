(** The M0 surface elaborator, brief section 3.9.  It reads a surface
    tree and writes the kernel term of the sugar row that SPEC.md
    section 7 gives the production.  There is no metavariable and no
    unification:  a row that needs a type asks the checker for it, so
    the elaborator is bidirectional in the same sense check.ml is.

    Mirrors kan-lang-tot-pin/surface/elab.ml for the walk:  a name
    resolves against the local telescope first and against the globals
    second, a binder pushes one local, and a form that the kernel
    refuses in inference position takes its expected type from the
    caller.  tot's holes, its instance search and its data items have no
    M0 production and are left out.

    The elaboration context is [Check.ctx] itself.  It carries the local
    names, their marks and their types as values, which is exactly what
    the two type directed rows need (SB-D14), and it carries the globals
    a name resolves against.  No second context type exists, so the
    names the elaborator counts and the names the checker counts can
    never drift.

    Every inference the elaborator makes is check time, so it asks
    [Check.infer] at mark [Zero] (SB-D31):  an erased binder is readable
    at that mark, and the mark the kernel enforces on the term is the
    one [Check.check_decls] applies afterwards. *)

open Kanon_kernel

let ( let* ) = Result.bind

let no_expect (what : string) : Error.t =
  Error.Cannot_infer (what ^ " needs an expected type")

(** The de Bruijn index of a name in the local telescope, innermost
    first.  A name that is not local is a global, and an unbound global
    is the checker's [Unbound], not the elaborator's:  the elaborator
    never decides that a name does not exist (SB-D30). *)
let rec index_of (x : string) (names : string list) : int option =
  match names with
  | [] -> None
  | y :: rest ->
      if String.equal x y then Some 0 else Option.map succ (index_of x rest)

let globals_of (c : Check.ctx) : Global.t = c.Check.globals
let env_of (c : Check.ctx) : Value.t list = c.Check.env
let size_of (c : Check.ctx) : int = c.Check.size

let eval_in (c : Check.ctx) (t : Term.t) : (Value.t, Error.t) result =
  Eval.eval (globals_of c) (env_of c) t

let whnf_in (c : Check.ctx) (v : Value.t) : (Value.t, Error.t) result =
  Eval.whnf (globals_of c) v

(** The type of a term, at the check time mark.  The answer feeds a
    type directed row and never reaches the checked term. *)
let type_of (c : Check.ctx) (t : Term.t) : (Value.t, Error.t) result =
  let* v = Check.infer c Quantity.Zero t in
  whnf_in c v

(** The universe a level names, [Prop] at zero and [Type n] at n + 1
    (SB-D2). *)
let univ_of_int (n : int) : (Term.t, Error.t) result =
  Level.of_int n
  |> Option.to_result
       ~none:(Error.Universe (Printf.sprintf "the universe level %d is not a level" n))
  |> Result.map (fun (l : Level.t) -> Term.Univ l)

(** The point former under a left or a right former, as the pair of the
    mark and the domain value the shape carries. *)
let point_of (s : Value.t Shape.t) : (Quantity.t * string * Value.t) option =
  Rules.as_vpi s

let leg_expectations (c : Check.ctx) (expected : Value.t option) (n : int)
    ~(left : bool) : (Value.t option list, Error.t) result =
  let none_list : Value.t option list = List.init n (fun (_k : int) -> None) in
  let view : Value.t -> (Value.t Shape.t * Value.closure * Level.t option) option =
    if left then Value.as_lan else Value.as_ran
  in
  expected
  |> Option.fold ~none:(Ok none_list) ~some:(fun (ty : Value.t) ->
         let* w = whnf_in c ty in
         view w
         |> Option.fold ~none:(Ok none_list)
              ~some:(fun
                  ( (vs : Value.t Shape.t),
                    (dclo : Value.closure),
                    (_u : Level.t option) )
                ->
                Rules.as_vcoll vs
                |> Option.fold ~none:(Ok none_list) ~some:(fun (dn : int) ->
                       if Int.equal dn n then
                         let* dlegs = Rules.coll_legs_of Check.ops c dclo in
                         Rules.all_ok
                           (List.init n (fun (k : int) ->
                                Result.map Option.some
                                  (Rules.coll_leg_ty Check.ops c dlegs k)))
                       else Ok none_list)))

(** M1 Stage G, correction C7:  the three views of a surface tree the mu
    rows read.  Each match is exhaustive and holds no wildcard arm, so a
    new production is a compile error here. *)
let app_split (s : Syntax.t) : (Syntax.t * Syntax.t) option =
  match s with
  | Syntax.SApp (f, a) -> Some (f, a)
  | Syntax.SVar _ | Syntax.SNat _ | Syntax.SProp | Syntax.SType _ | Syntax.SPrim _
  | Syntax.SUnit | Syntax.SAuto | Syntax.SPair (_, _) | Syntax.STuple _ | Syntax.SSum _
  | Syntax.SProd _ | Syntax.SProj (_, _) | Syntax.SInj (_, _, _) | Syntax.SAbsurd _
  | Syntax.SFun (_, _) | Syntax.SArrow (_, _) | Syntax.SStar (_, _)
  | Syntax.SLet (_, _, _, _) | Syntax.SAnn (_, _) | Syntax.SCase (_, _, _)
  | Syntax.SMatch (_, _, _) ->
      None

let arrow_split (s : Syntax.t) : (Syntax.binder * Syntax.t) option =
  match s with
  | Syntax.SArrow (b, cod) -> Some (b, cod)
  | Syntax.SVar _ | Syntax.SNat _ | Syntax.SProp | Syntax.SType _ | Syntax.SPrim _
  | Syntax.SUnit | Syntax.SAuto | Syntax.SPair (_, _) | Syntax.STuple _ | Syntax.SSum _
  | Syntax.SProd _ | Syntax.SProj (_, _) | Syntax.SInj (_, _, _) | Syntax.SAbsurd _
  | Syntax.SFun (_, _) | Syntax.SApp (_, _) | Syntax.SStar (_, _)
  | Syntax.SLet (_, _, _, _) | Syntax.SAnn (_, _) | Syntax.SCase (_, _, _)
  | Syntax.SMatch (_, _, _) ->
      None

let var_name (s : Syntax.t) : string option =
  match s with
  | Syntax.SVar x -> Some x
  | Syntax.SNat _ | Syntax.SProp | Syntax.SType _ | Syntax.SPrim _ | Syntax.SUnit
  | Syntax.SAuto | Syntax.SPair (_, _) | Syntax.STuple _ | Syntax.SSum _
  | Syntax.SProd _ | Syntax.SProj (_, _) | Syntax.SInj (_, _, _) | Syntax.SAbsurd _
  | Syntax.SFun (_, _) | Syntax.SApp (_, _) | Syntax.SArrow (_, _) | Syntax.SStar (_, _)
  | Syntax.SLet (_, _, _, _) | Syntax.SAnn (_, _) | Syntax.SCase (_, _, _)
  | Syntax.SMatch (_, _, _) ->
      None

(** The head of an application spine and its arguments, in the order
    they are written. *)
let rec spine_of (s : Syntax.t) (acc : Syntax.t list) : Syntax.t * Syntax.t list =
  app_split s
  |> Option.fold ~none:(s, acc) ~some:(fun ((f : Syntax.t), (a : Syntax.t)) ->
         spine_of f (a :: acc))

(** The first [n] items of a list and the rest, read by index, so the
    split needs no partial indexing. *)
let split_at (n : int) (xs : 'a list) : 'a list * 'a list =
  ( List.filteri (fun (i : int) (_x : 'a) -> i < n) xs,
    List.filteri (fun (i : int) (_x : 'a) -> i >= n) xs )

(** M1 Stage G:  what a name resolves to when the family table holds it.
    A type at a family is a left former at the mu shape and never a
    global name (shape.ml:42-49), and a constructor of a family is an
    introduction at that shape, so neither reaches [Term.Global]. *)
type mu_ref =
  | RFam of Positivity.family
  | RCtor of Positivity.family * Positivity.ctor

(** The family that declares a constructor name.  This file reads the
    table itself:  the one accessor of brief 3.3 is a rule about
    rules.ml and about the checking path (SG-D2, dev/r0-audit.sh:6-11),
    and the elaborator is neither. *)
let find_ctor (x : string) (g : Global.t) : (Positivity.family * Positivity.ctor) option =
  Global.StringMap.fold
    (fun (_n : string) (f : Positivity.family)
         (acc : (Positivity.family * Positivity.ctor) option) ->
      Option.fold
        ~none:(Option.map (fun (ct : Positivity.ctor) -> (f, ct)) (Positivity.ctor_of x f))
        ~some:Option.some acc)
    g.Global.families None

(** A local name wins over the family table, so a binder named after a
    family shadows it as every other binder does. *)
let mu_ref_of (c : Check.ctx) (x : string) : mu_ref option =
  match () with
  | () when Option.is_some (index_of x (Check.names_of c)) -> None
  | () ->
      Global.find_family x (globals_of c)
      |> Option.map (fun (f : Positivity.family) -> RFam f)
      |> Option.fold
           ~none:
             (Option.map
                (fun ((f : Positivity.family), (ct : Positivity.ctor)) -> RCtor (f, ct))
                (find_ctor x (globals_of c)))
           ~some:Option.some

(** The whole walk.  One arm per constructor of [Syntax.t], in the order
    syntax.ml declares them, and every arm names the sugar row of
    SPEC.md section 7 that it writes. *)
let rec elab (c : Check.ctx) ~(expected : Value.t option) (s : Syntax.t) :
    (Term.t, Error.t) result =
  match s with
  | Syntax.SVar x ->
      mu_ref_of c x
      |> Option.fold
           ~none:
             (Ok
                (index_of x (Check.names_of c)
                |> Option.fold ~none:(Term.Global x) ~some:(fun (i : int) -> Term.Var i)))
           ~some:(fun (r : mu_ref) -> elab_mu_ref c r [])
  | Syntax.SNat n -> Ok (Term.Lit (Literal.LInt n))
  | Syntax.SProp -> Ok (Term.Univ Level.zero)
  | Syntax.SType n -> univ_of_int (n + 1)
  | Syntax.SPrim p -> Ok (Term.Global (Syntax.prim_name p))
  | Syntax.SUnit -> Ok Rules.unit_val
  | Syntax.SAuto -> Ok Term.Auto
  | Syntax.SPair (a, b) -> elab_pair c ~expected a b
  | Syntax.STuple items ->
      let* legs = elab_items c ~expected items ~left:false in
      Ok (Term.Sec (Shape.SColl (List.length items), List.map Rules.leg_of legs))
  | Syntax.SSum items ->
      let* tys = Rules.all_ok (List.map (elab c ~expected:None) items) in
      Ok (Rules.sum_ty tys)
  | Syntax.SProd items ->
      let* tys = Rules.all_ok (List.map (elab c ~expected:None) items) in
      Ok (Rules.prod_ty tys)
  | Syntax.SProj (a, k) -> elab_proj c a k
  | Syntax.SInj (k, n, a) ->
      let* tys = leg_expectations c expected n ~left:true in
      let* payload = elab c ~expected:(Option.join (Rules.at k tys)) a in
      Ok (Term.In (Shape.SColl n, Term.ALeg k, [ payload ]))
  | Syntax.SAbsurd a ->
      let* scrut = elab c ~expected:None a in
      Ok
        (Term.Elim
           {
             Term.e_shape = Shape.SColl 0;
             e_scrut = scrut;
             e_scrut_q = Quantity.One;
             e_motive = None;
             e_branches = [];
           })
  | Syntax.SApp (f, a) -> elab_app c f a
  | Syntax.SFun (bs, body) -> elab_fun c ~expected bs body
  | Syntax.SArrow (b, cod) -> elab_group c b cod ~left:false
  | Syntax.SStar (b, cod) -> elab_group c b cod ~left:true
  | Syntax.SLet (x, ty, def, body) ->
      let* ty' = elab c ~expected:None ty in
      let* tyv = eval_in c ty' in
      let* def' = elab c ~expected:(Some tyv) def in
      let* defv = eval_in c def' in
      let c' = Check.define x Quantity.Many tyv defv c in
      let* body' = elab c' ~expected body in
      Ok (Term.Let (x, ty', def', body'))
  | Syntax.SAnn (a, ty) ->
      let* ty' = elab c ~expected:None ty in
      let* tyv = eval_in c ty' in
      let* a' = elab c ~expected:(Some tyv) a in
      Ok (Term.Ann (a', ty'))
  | Syntax.SCase (scrut, mo, brs) -> elab_case c ~expected scrut mo brs
  | Syntax.SMatch (scrut, mo, brs) -> elab_match c ~expected scrut mo brs

(** The items of a section, each at the leg type the expected type gives
    it when it gives one.  The two lists are paired by the total [zip] of
    rules.ml, so no length can surprise this row. *)
and elab_items (c : Check.ctx) ~(expected : Value.t option) (items : Syntax.t list)
    ~(left : bool) : (Term.t list, Error.t) result =
  let* tys = leg_expectations c expected (List.length items) ~left in
  let* pairs =
    Rules.zip items tys
    |> Option.to_result
         ~none:(Error.Mismatch "the item count and the leg count differ")
  in
  Rules.all_ok
    (List.map
       (fun ((it : Syntax.t), (ty : Value.t option)) -> elab c ~expected:ty it)
       pairs)

(** "(a, b)":  the pair of the sugar table.  The kernel refuses an
    injection in inference position, so the row needs the expected type
    and reads the point mark and the fibre from it. *)
and elab_pair (c : Check.ctx) ~(expected : Value.t option) (a : Syntax.t)
    (b : Syntax.t) : (Term.t, Error.t) result =
  let* ty = expected |> Option.to_result ~none:(no_expect "a pair") in
  let* w = whnf_in c ty in
  let* vs, dclo, _u =
    Value.as_lan w
    |> Option.to_result
         ~none:(Error.Mismatch "a pair needs a left former as its expected type")
  in
  let* q, x, dom_v =
    point_of vs
    |> Option.to_result ~none:(Error.Mismatch "a pair needs a point former")
  in
  let* point = elab c ~expected:(Some dom_v) a in
  let* point_v = eval_in c point in
  let* cod_v = Rules.open_closure (Eval.ev (globals_of c)) dclo [ point_v ] in
  let* fibre = elab c ~expected:(Some cod_v) b in
  let* dom_t = Eval.quote (globals_of c) (size_of c) dom_v in
  Ok (Term.In (Shape.SPi (q, x, dom_t), Term.APt (q, point), [ fibre ]))

(** The first answer of a list of candidates.  Two views on one value
    are exclusive here, so the list holds at most one [Some];  the
    thunk keeps the branch that did not fire from running, because
    [Option.fold] reads its [~none] argument eagerly. *)
and first_some (xs : 'a option list) : 'a option =
  List.fold_left
    (fun (acc : 'a option) (x : 'a option) ->
      Option.fold ~none:x ~some:Option.some acc)
    None xs

(** "p.1", "p.2" and "t.k" (SB-D14).  The scrutinee's type tells the two
    sugar rows apart:  a left former at the point shape is a pair and a
    right former at the collection shape is a tuple. *)
and elab_proj (c : Check.ctx) (a : Syntax.t) (k : int) : (Term.t, Error.t) result =
  let* scrut = elab c ~expected:None a in
  let* w = type_of c scrut in
  let candidates : (unit -> (Term.t, Error.t) result) option list =
    [
      Value.as_lan w
      |> Option.map
           (fun
             ( (vs : Value.t Shape.t),
               (dclo : Value.closure),
               (_u : Level.t option) )
           -> fun () -> elab_pair_proj c scrut vs dclo k);
      Value.as_ran w
      |> Option.map
           (fun
             ( (vs : Value.t Shape.t),
               (_dclo : Value.closure),
               (_u : Level.t option) )
           -> fun () -> elab_leg_proj c scrut vs k);
    ]
  in
  let* run =
    first_some candidates
    |> Option.to_result
         ~none:
           (Error.Mismatch
              "a projection reads a pair or a tuple, and this scrutinee is neither")
  in
  run ()

(** The two pair projections of D-M0-3:  one elimination at the left
    former of the point shape, with the projection motive and the branch
    that binds the point and the fibre element. *)
and elab_pair_proj (c : Check.ctx) (scrut : Term.t) (vs : Value.t Shape.t)
    (dclo : Value.closure) (k : int) : (Term.t, Error.t) result =
  let* q, x, dom_v =
    point_of vs
    |> Option.to_result ~none:(Error.Mismatch "a pair projection needs a point former")
  in
  let* which =
    (if Int.equal k 1 then Some 0 else if Int.equal k 2 then Some 1 else None)
    |> Option.to_result
         ~none:(Error.Wrong_leg "a pair carries the projections .1 and .2 only")
  in
  let size = size_of c in
  let ev = Eval.ev (globals_of c) in
  let* body_v =
    if Int.equal which 0 then Ok dom_v
    else
      let* point =
        Rules.elim_value ev vs q None (Rules.proj_branch q 0) (env_of c)
          (Value.var size)
      in
      Rules.open_closure ev dclo [ point ]
  in
  let* m_body = Eval.quote (globals_of c) (size + 1) body_v in
  let* dom_t = Eval.quote (globals_of c) size dom_v in
  Ok
    (Term.Elim
       {
         Term.e_shape = Shape.SPi (q, x, dom_t);
         e_scrut = scrut;
         e_scrut_q = Quantity.One;
         e_motive =
           Some { Term.m_ind = None; m_idx = []; m_self = "self"; m_body };
         e_branches = Rules.proj_branch q which;
       })

(** "t.k", the leg of a tuple, 0 based (SB-D14). *)
and elab_leg_proj (c : Check.ctx) (scrut : Term.t) (vs : Value.t Shape.t) (k : int) :
    (Term.t, Error.t) result =
  let _ = c in
  let* n =
    Rules.as_vcoll vs
    |> Option.to_result
         ~none:(Error.Mismatch "a leg projection needs a collection former")
  in
  Ok (Term.Out (Shape.SColl n, Term.ALeg k, scrut))

(** "f a" (SA-D1).  The head is inferred, so the argument is elaborated
    at the domain the head's type names and the address carries the mark
    that type declares. *)
and elab_app (c : Check.ctx) (f : Syntax.t) (a : Syntax.t) : (Term.t, Error.t) result =
  let head, args = spine_of (Syntax.SApp (f, a)) [] in
  Option.bind (var_name head) (mu_ref_of c)
  |> Option.fold
       ~none:(fun () -> elab_app_point c f a)
       ~some:(fun (r : mu_ref) -> fun () -> elab_mu_ref c r args)
  |> fun (k : unit -> (Term.t, Error.t) result) -> k ()

(** SL-D3: match selects the existing fibered elimination directly.
    Its scrutinee must have a mu family type even when the branch list
    is empty, so an empty collection cannot pass as a family. *)
and elab_match (c : Check.ctx) ~(expected : Value.t option) (scrut : Syntax.t)
    (mo : Syntax.motive option) (brs : Syntax.branch list) : (Term.t, Error.t) result =
  let wrong = Error.Mismatch "a match needs a mu family as the type of its scrutinee" in
  let* scrut' = elab c ~expected:None scrut in
  let* w = type_of c scrut' in
  let* vs, dclo, u = Value.as_lan w |> Option.to_result ~none:wrong in
  let* n, ixv = Rules.as_vmu vs |> Option.to_result ~none:wrong in
  elab_mu_case c ~expected scrut' n ixv dclo u mo brs

(** M1 Stage G, correction C7:  a family at its parameters and indices,
    or a constructor at its arguments.  The family reference is the left
    former at the mu shape over the parameter section, which is binder
    free (SG-D16);  the constructor is the introduction at the shape its
    own result indices name, read under the arguments given here. *)
and elab_mu_ref (c : Check.ctx) (r : mu_ref) (args : Syntax.t list) :
    (Term.t, Error.t) result =
  match r with
  | RFam f -> elab_fam_ref c f args
  | RCtor (f, ct) -> elab_ctor_ref c f ct args

and arity_is (what : string) (want : int) (got : int) : (unit, Error.t) result =
  if Int.equal want got then Ok ()
  else
    Error
      (Error.Mismatch
         (Printf.sprintf "%s takes %d arguments and the term gives %d" what want got))

and elab_fam_ref (c : Check.ctx) (f : Positivity.family) (args : Syntax.t list) :
    (Term.t, Error.t) result =
  let np = List.length f.Positivity.f_params in
  let* () =
    arity_is f.Positivity.f_name (np + List.length f.Positivity.f_indices)
      (List.length args)
  in
  let* ts = Rules.all_ok (List.map (elab c ~expected:None) args) in
  let params, indices = split_at np ts in
  Ok
    (Term.Lan
       ( Shape.SMu (f.Positivity.f_name, indices),
         Term.Sec (Shape.SColl np, List.map Rules.leg_of params) ))

(** The indices the introduction carries are the constructor's declared
    result indices, opened at the argument values (rules.ml
    [mu_indices]).  A family with parameters reads them off the expected
    type, which the introduction rule does and this row does not, so the
    row asks the writer for the type. *)
and elab_ctor_ref (c : Check.ctx) (f : Positivity.family) (ct : Positivity.ctor)
    (args : Syntax.t list) : (Term.t, Error.t) result =
  let* () =
    arity_is ct.Positivity.c_name (List.length ct.Positivity.c_args) (List.length args)
  in
  let* () =
    match f.Positivity.f_params with
    | [] -> Ok ()
    | (_e : Quantity.t * string * Term.t) :: (_rest : Positivity.telescope) ->
        Error (no_expect ("the constructor " ^ ct.Positivity.c_name))
  in
  let* ts = Rules.all_ok (List.map (elab c ~expected:None) args) in
  let* vs = Rules.all_ok (List.map (eval_in c) ts) in
  let* ixv =
    Rules.all_ok
      (List.map
         (fun (ri : Term.t) -> Eval.eval (globals_of c) (List.rev vs) ri)
         ct.Positivity.c_res_idx)
  in
  let* ix =
    Rules.all_ok
      (List.map (fun (v : Value.t) -> Eval.quote (globals_of c) (size_of c) v) ixv)
  in
  Ok
    (Term.In
       ( Shape.SMu (f.Positivity.f_name, ix),
         Term.ACtor ct.Positivity.c_name,
         ts ))

and elab_app_point (c : Check.ctx) (f : Syntax.t) (a : Syntax.t) :
    (Term.t, Error.t) result =
  let* head = elab c ~expected:None f in
  let* w = type_of c head in
  let* vs, _dclo, _u =
    Value.as_ran w
    |> Option.to_result
         ~none:(Error.Mismatch "the head of an application is not a function")
  in
  let* q, x, dom_v =
    point_of vs
    |> Option.to_result
         ~none:(Error.Mismatch "the head of an application is not a function")
  in
  let* arg = elab c ~expected:(Some dom_v) a in
  let* dom_t = Eval.quote (globals_of c) (size_of c) dom_v in
  Ok (Term.Out (Shape.SPi (q, x, dom_t), Term.APt (q, arg), head))

(** One binder:  its type is elaborated in the context it stands in, and
    the context the body reads holds the binder with its mark. *)
and elab_binder (c : Check.ctx) (b : Syntax.binder) :
    (Quantity.t * string * Term.t * Check.ctx, Error.t) result =
  let* ty = elab c ~expected:None b.Syntax.b_ty in
  let* tyv = eval_in c ty in
  Ok (b.Syntax.b_q, b.Syntax.b_name, ty, Check.bind b.Syntax.b_name b.Syntax.b_q tyv c)

(** The codomain the body of a lambda is elaborated at:  the expected
    type opened at the binder, when the expected type is a right former
    at the point shape.  A shape that does not match answers [None] and
    the checker reports it. *)
and cod_of (c : Check.ctx) ~(expected : Value.t option) :
    (Value.t option, Error.t) result =
  expected
  |> Option.fold ~none:(Ok None) ~some:(fun (ty : Value.t) ->
         let* w = whnf_in c ty in
         Value.as_ran w
         |> Option.fold ~none:(Ok None)
              ~some:(fun
                  ( (vs : Value.t Shape.t),
                    (dclo : Value.closure),
                    (_u : Level.t option) )
                ->
                point_of vs
                |> Option.fold ~none:(Ok None)
                     ~some:(fun
                         ( (_q : Quantity.t),
                           (_x : string),
                           (_dom : Value.t) )
                       ->
                       Result.map Option.some
                         (Rules.open_closure (Eval.ev (globals_of c)) dclo
                            [ Value.var (size_of c) ]))))

(** "fun (q x : A) => b", one section at the point shape per binder. *)
and elab_fun (c : Check.ctx) ~(expected : Value.t option) (bs : Syntax.binder list)
    (body : Syntax.t) : (Term.t, Error.t) result =
  match bs with
  | [] -> elab c ~expected body
  | b :: rest ->
      let* q, x, ty, c' = elab_binder c b in
      let* inner = cod_of c ~expected in
      let* body' = elab_fun c' ~expected:inner rest body in
      Ok
        (Term.Sec
           (Shape.SPi (q, x, ty), [ { Term.l_binders = [ (q, x) ]; l_body = body' } ]))

(** "(q x : A) -> B" is the right former and "(q x : A) * B" is the left
    one, both at the point shape. *)
and elab_group (c : Check.ctx) (b : Syntax.binder) (cod : Syntax.t) ~(left : bool) :
    (Term.t, Error.t) result =
  let* q, x, ty, c' = elab_binder c b in
  let* cod' = elab c' ~expected:None cod in
  let s : Term.t Shape.t = Shape.SPi (q, x, ty) in
  Ok (if left then Term.Lan (s, cod') else Term.Ran (s, cod'))

(** "case t [as x [in F i1 .. im] return M] with | k (y : T) => b" at a
    collection and "| c x1 .. xn => b" at a family.  The width comes from
    the scrutinee's type, so a case that misses a leg is the checker's
    [Missing_branch] and never a silent narrowing.  M1 Stage H, brief
    3.8:  a scrutinee at a mu shape takes the fibered row below and every
    M0 case keeps the collection row. *)
and elab_case (c : Check.ctx) ~(expected : Value.t option) (scrut : Syntax.t)
    (mo : Syntax.motive option) (brs : Syntax.branch list) : (Term.t, Error.t) result =
  let* scrut' = elab c ~expected:None scrut in
  let* w = type_of c scrut' in
  let* vs, dclo, u =
    Value.as_lan w
    |> Option.to_result
         ~none:(Error.Mismatch "a case needs a left former as the type of its scrutinee")
  in
  Rules.as_vmu vs
  |> Option.fold
       ~none:(fun () -> elab_coll_case c ~expected scrut' w vs dclo mo brs)
       ~some:(fun ((n : string), (ixv : Value.t list)) ->
         fun (_unit : unit) -> elab_mu_case c ~expected scrut' n ixv dclo u mo brs)
  |> fun (k : unit -> (Term.t, Error.t) result) -> k ()

(** The M0 row, unchanged from Stage B:  the scrutinee stands at a
    collection and every branch is keyed by its leg number (SB-D32). *)
and elab_coll_case (c : Check.ctx) ~(expected : Value.t option) (scrut' : Term.t)
    (w : Value.t) (vs : Value.t Shape.t) (dclo : Value.closure)
    (mo : Syntax.motive option) (brs : Syntax.branch list) : (Term.t, Error.t) result =
  let* n =
    Rules.as_vcoll vs
    |> Option.to_result ~none:(Error.Mismatch "a case eliminates a collection")
  in
  let* dlegs = Rules.coll_legs_of Check.ops c dclo in
  let* motive = elab_motive c mo w in
  let* branches =
    Rules.all_ok (List.map (elab_branch c vs dlegs motive expected) brs)
  in
  Ok
    (Term.Elim
       {
         Term.e_shape = Shape.SColl n;
         e_scrut = scrut';
         e_scrut_q = Quantity.One;
         e_motive = motive;
         e_branches = branches;
       })

(** The motive is a type under the scrutinee, so it is elaborated with
    the self name bound at the erased mark. *)
and elab_motive (c : Check.ctx) (mo : Syntax.motive option) (scrut_ty : Value.t) :
    (Term.motive option, Error.t) result =
  mo
  |> Option.fold ~none:(Ok None) ~some:(fun (m : Syntax.motive) ->
         let* () = coll_motive_plain m in
         let c' = Check.bind m.Syntax.mo_self Quantity.Zero scrut_ty c in
         let* body = elab c' ~expected:None m.Syntax.mo_body in
         Ok
           (Some
              {
                Term.m_ind = None;
                m_idx = [];
                m_self = m.Syntax.mo_self;
                m_body = body;
              }))

(** M1 Stage H, brief 3.8:  the index clause names a family and binds
    its index arguments, so a motive at a collection carries none and the
    M0 motive form is the only one this row reads. *)
and coll_motive_plain (m : Syntax.motive) : (unit, Error.t) result =
  m.Syntax.mo_ind
  |> Option.fold ~none:(Ok ()) ~some:(fun (n : string) ->
         Error
           (Error.Mismatch
              ("a case at a collection takes no index clause and its motive names " ^ n)))

(** One branch.  The payload's type is the diagram's leg, not the
    surface annotation (SB-D32), so the elaborator and the checker read
    the same type.  M1 Stage H:  a constructor keyed branch at a
    collection is refused here, because a leg address is not a
    constructor address (SH-D9). *)
and elab_branch (c : Check.ctx) (vs : Value.t Shape.t) (dlegs : Value.vleg list)
    (motive : Term.motive option) (expected : Value.t option) (br : Syntax.branch) :
    (Term.addr * Term.leg, Error.t) result =
  match br with
  | Syntax.BrCtor (cname, (_fs : Syntax.field list), (_body : Syntax.t)) ->
      Error
        (Error.Wrong_leg
           ("the branch at " ^ cname ^ " keys a constructor and a case at a collection keys a leg"))
  | Syntax.BrLeg (k, binders, br_body) ->
      let* b =
        Rules.one_of binders
        |> Option.to_result
             ~none:(Error.Missing_branch "each branch binds its payload once")
      in
      let* ty = Rules.coll_leg_ty Check.ops c dlegs k in
      let self = Value.VIn (vs, Value.VALeg k, [ Value.var (size_of c) ]) in
      let* target = branch_target c motive expected self in
      let c' = Check.bind b.Syntax.b_name b.Syntax.b_q ty c in
      let* body = elab c' ~expected:target br_body in
      Ok
        ( Term.ALeg k,
          { Term.l_binders = [ (b.Syntax.b_q, b.Syntax.b_name) ]; l_body = body } )

(** M1 Stage H, brief 3.8:  the fibered row.  The scrutinee stands at a
    family, the motive binds the index arguments beside the scrutinee
    binder, and every branch is keyed by a constructor name with one
    binder per field.  A dependent match elaborates to one fibered
    [Elim] and to no new kernel form (M1-PLAN.md:96). *)
and elab_mu_case (c : Check.ctx) ~(expected : Value.t option) (scrut' : Term.t)
    (n : string) (ixv : Value.t list) (dclo : Value.closure) (u : Level.t option)
    (mo : Syntax.motive option) (brs : Syntax.branch list) : (Term.t, Error.t) result =
  let* fam =
    Global.find_family n (globals_of c)
    |> Option.to_result ~none:(Error.Unbound ("the family " ^ n ^ " is not declared"))
  in
  let* penv = Rules.mu_param_env Check.ops c dclo in
  let* motive = elab_mu_motive c n fam dclo u penv mo in
  let* branches =
    Rules.all_ok (List.map (elab_mu_branch c n fam motive penv expected) brs)
  in
  let* ix =
    Rules.all_ok
      (List.map (fun (v : Value.t) -> Eval.quote (globals_of c) (size_of c) v) ixv)
  in
  Ok
    (Term.Elim
       {
         Term.e_shape = Shape.SMu (n, ix);
         e_scrut = scrut';
         e_scrut_q = Quantity.One;
         e_motive = motive;
         e_branches = branches;
       })

(** The fibered motive.  Each index binder is bound at the erased mark
    (A2) at the index type of the family, read under the parameters and
    under the index binders before it, and the scrutinee binder is bound
    at the family read at those binders.  [m_ind] is the family the
    surface names, which the kernel checks against the scrutinee
    (SH-D6), so a motive built for a sibling family reaches the checker
    and is refused there. *)
and elab_mu_motive (c : Check.ctx) (n : string) (fam : Positivity.family)
    (dclo : Value.closure) (u : Level.t option) (penv : Value.t list)
    (mo : Syntax.motive option) : (Term.motive option, Error.t) result =
  mo
  |> Option.fold ~none:(Ok None) ~some:(fun (m : Syntax.motive) ->
         let* pairs =
           Rules.zip fam.Positivity.f_indices m.Syntax.mo_idx
           |> Option.to_result
                ~none:
                  (Error.Mismatch
                     (Printf.sprintf
                        "the motive of %s binds %d index names and the family has %d" n
                        (List.length m.Syntax.mo_idx)
                        (List.length fam.Positivity.f_indices)))
         in
         let* ci, _ienv, vals = bind_indices c penv pairs in
         let self_ty = Value.VLan (Shape.SMu (n, List.rev vals), dclo, u) in
         let cs = Check.bind m.Syntax.mo_self Quantity.Zero self_ty ci in
         let* body = elab cs ~expected:None m.Syntax.mo_body in
         Ok
           (Some
              {
                Term.m_ind = m.Syntax.mo_ind;
                m_idx = m.Syntax.mo_idx;
                m_self = m.Syntax.mo_self;
                m_body = body;
              }))

(** The index binders of a motive, outermost first, exactly as the
    checker binds them (rules.ml [mu_motive_lvl]):  each index type is
    read in the values before it and the binder is erased. *)
and bind_indices (c : Check.ctx) (penv : Value.t list)
    (pairs : ((Quantity.t * string * Term.t) * string) list) :
    (Check.ctx * Value.t list * Value.t list, Error.t) result =
  List.fold_left
    (fun (acc : (Check.ctx * Value.t list * Value.t list, Error.t) result)
         ((((_q : Quantity.t), (_y : string), (ty : Term.t)), (x : string)) :
           (Quantity.t * string * Term.t) * string) ->
      let* c_acc, env_acc, vals_acc = acc in
      let* tyv = Eval.eval (globals_of c_acc) env_acc ty in
      let v = Value.var (size_of c_acc) in
      Ok (Check.bind x Quantity.Zero tyv c_acc, v :: env_acc, v :: vals_acc))
    (Ok (c, penv, []))
    pairs

(** SL-D4: an optional field annotation is checked in the context of
    preceding fields.  The family's field type remains authoritative;
    an annotation never changes the type supplied to the kernel. *)
and check_field_annotation (c : Check.ctx) (expected : Value.t) (f : Syntax.field) :
    (unit, Error.t) result =
  f.Syntax.fd_ty
  |> Option.fold ~none:(Ok ()) ~some:(fun (ty : Syntax.t) ->
         let* term = elab c ~expected:None ty in
         let* _level = Check.infer_univ c term in
         let* actual = eval_in c term in
         let* agrees = Conv.conv_type Check.ops c actual expected in
         if agrees then Ok ()
         else Error (Error.Mismatch ("the annotation of constructor field " ^ f.Syntax.fd_name ^
                                    " differs from its declared type")))

(** One constructor keyed branch.  The field binders take their types
    from the family record, each read under the fields before it, and the
    body is elaborated at the motive instantiated at that constructor's
    result indices and at its own introduction (SH-D7, SH-D9).  The
    branch binder keeps the mark the writer gave it, so the kernel row
    that compares it with the field mark stays the rule that decides
    (rules.ml [mu_branch]). *)
and elab_mu_branch (c : Check.ctx) (n : string) (fam : Positivity.family)
    (motive : Term.motive option) (penv : Value.t list) (expected : Value.t option)
    (br : Syntax.branch) : (Term.addr * Term.leg, Error.t) result =
  match br with
  | Syntax.BrLeg (k, (_bs : Syntax.binder list), (_body : Syntax.t)) ->
      Error
        (Error.Wrong_leg
           (Printf.sprintf "the branch %d keys a leg and a case at %s keys a constructor"
              k n))
  | Syntax.BrCtor (cname, fields, br_body) ->
      let* ct =
        Positivity.ctor_of cname fam
        |> Option.to_result ~none:(Error.Unbound (cname ^ " is not a constructor of " ^ n))
      in
      let* pairs =
        Rules.zip ct.Positivity.c_args fields
        |> Option.to_result
             ~none:
               (Error.Missing_branch
                  (Printf.sprintf "the branch at %s binds %d fields and %s takes %d" cname
                     (List.length fields) cname (List.length ct.Positivity.c_args)))
      in
      let* cf, env, vals = bind_fields c penv pairs in
      let* idx =
        Rules.all_ok
          (List.map
             (fun (r : Term.t) -> Eval.eval (globals_of c) env r)
             ct.Positivity.c_res_idx)
      in
      let self = Value.VIn (Shape.SMu (n, idx), Value.VACtor cname, List.rev vals) in
      let* target = mu_branch_target c motive expected idx self in
      let* body = elab cf ~expected:target br_body in
      Ok
        ( Term.ACtor cname,
          {
            Term.l_binders =
              List.map (fun (f : Syntax.field) -> (f.Syntax.fd_q, f.Syntax.fd_name)) fields;
            l_body = body;
          } )

(** The field binders of one branch, in declaration order, each type
    read in the values before it (rules.ml [mu_branch]). *)
and bind_fields (c : Check.ctx) (penv : Value.t list)
    (pairs : ((Quantity.t * string * Term.t) * Syntax.field) list) :
    (Check.ctx * Value.t list * Value.t list, Error.t) result =
  List.fold_left
    (fun (acc : (Check.ctx * Value.t list * Value.t list, Error.t) result)
         ((((_q : Quantity.t), (_y : string), (ty : Term.t)), (f : Syntax.field)) :
           (Quantity.t * string * Term.t) * Syntax.field) ->
      let* c_acc, env_acc, vals_acc = acc in
      let* tyv = Eval.eval (globals_of c_acc) env_acc ty in
      let* () = check_field_annotation c_acc tyv f in
      let v = Value.var (size_of c_acc) in
      Ok
        ( Check.bind f.Syntax.fd_name f.Syntax.fd_q tyv c_acc,
          v :: env_acc,
          v :: vals_acc ))
    (Ok (c, penv, []))
    pairs

(** The type a fibered branch body is elaborated at:  the motive read at
    the branch's own indices and introduction, or the caller's
    expectation when the surface gave no motive, which the kernel then
    refuses (SH-D5). *)
and mu_branch_target (c : Check.ctx) (motive : Term.motive option)
    (expected : Value.t option) (idx : Value.t list) (self : Value.t) :
    (Value.t option, Error.t) result =
  motive
  |> Option.fold ~none:(Ok expected) ~some:(fun (m : Term.motive) ->
         Result.map Option.some (Rules.mu_result Check.ops c m idx self))

(** The type a branch body is elaborated at:  the motive read at the
    branch's own value, or the caller's expectation as the constant
    cocone when there is no motive. *)
and branch_target (c : Check.ctx) (motive : Term.motive option)
    (expected : Value.t option) (self : Value.t) : (Value.t option, Error.t) result =
  motive
  |> Option.fold ~none:(Ok expected) ~some:(fun (_m : Term.motive) ->
         Result.map Option.some (Rules.elim_result Check.ops c motive expected self))

(** M1 Stage G, correction C7:  a binder list as a telescope, each type
    read under the binders before it (pin check.ml:1804-1810). *)
and elab_telescope (c : Check.ctx) (bs : Syntax.binder list) :
    (Positivity.telescope * Check.ctx, Error.t) result =
  List.fold_left
    (fun (acc : (Positivity.telescope * Check.ctx, Error.t) result) (b : Syntax.binder) ->
      let* tele, c' = acc in
      let* q, x, ty, c'' = elab_binder c' b in
      Ok (tele @ [ (q, x, ty) ], c''))
    (Ok ([], c)) bs

(** The arrow chain of a family header or of a constructor type:  its
    binders are a telescope and its result goes back to the caller with
    the context that result stands in. *)
and elab_chain (c : Check.ctx) (acc : Positivity.telescope) (s : Syntax.t) :
    (Positivity.telescope * Syntax.t * Check.ctx, Error.t) result =
  arrow_split s
  |> Option.fold
       ~none:(Ok (acc, s, c))
       ~some:(fun ((b : Syntax.binder), (cod : Syntax.t)) ->
         let* q, x, ty, c' = elab_binder c b in
         elab_chain c' (acc @ [ (q, x, ty) ]) cod)

(** The declared universe of a family header.  Formation answers this
    level and never computes a max (A5, SG-D8). *)
and elab_univ (c : Check.ctx) (s : Syntax.t) : (Level.t, Error.t) result =
  let* t = elab c ~expected:None s in
  match t with
  | Term.Univ l -> Ok l
  | Term.Var _ | Term.Global _ | Term.Lan (_, _) | Term.Ran (_, _) | Term.In (_, _, _)
  | Term.Sec (_, _) | Term.Out (_, _, _) | Term.Elim _ | Term.Let (_, _, _, _)
  | Term.Ann (_, _) | Term.Lit _ | Term.Auto ->
      Error (Error.Universe "the header of a family ends in a universe")

(** M1 Stage G, brief 3.9:  the header of one member.  The binders after
    the name are the parameter telescope and the arrow chain after the
    colon is the index telescope, which check.ml holds to quantity zero
    and to the declared level (A2, A5). *)
and elab_fam_decl (c : Check.ctx) (fm : Syntax.fam) : (Check.family_decl, Error.t) result =
  let* params, cp = elab_telescope c fm.Syntax.fm_params in
  let* indices, res, ci = elab_chain cp [] fm.Syntax.fm_ty in
  let* level = elab_univ ci res in
  Ok
    {
      Check.fam_name = fm.Syntax.fm_name;
      fam_params = params;
      fam_indices = indices;
      fam_level = level;
    }

(** One constructor:  the binders of its type are the argument telescope,
    one quantity per field, and its result names the member at the result
    index expressions (A14). *)
and elab_ctor_decl (c : Check.ctx) (name : string) (fc : Syntax.fam_ctor) :
    (Check.ctor_decl, Error.t) result =
  let* args, res, cr = elab_chain c [] fc.Syntax.fc_ty in
  let* res_t = elab cr ~expected:None res in
  let* params, ix = mu_result name res_t in
  Ok
    { Check.ct_name = fc.Syntax.fc_name; ct_args = args;
      ct_res_params = params; ct_res_idx = ix }

(** The result of a constructor type is the member itself at its result
    indices.  Any other result names a type the family record cannot
    hold, so the row refuses it here and not at the introduction. *)
and mu_result (name : string) (t : Term.t) : (Term.t list * Term.t list, Error.t) result =
  let wrong : (Term.t list * Term.t list, Error.t) result =
    Error (Error.Mismatch ("a constructor of " ^ name ^ " ends at another type"))
  in
  match t with
  | Term.Lan (Shape.SMu (n, ix), d) ->
      if String.equal n name then
        Result.map (fun params -> (params, ix)) (Rules.mu_params_of d)
      else wrong
  | Term.Lan
      ((Shape.SPi (_, _, _) | Shape.SColl _ | Shape.SPar (_, _) | Shape.SNu (_, _)), _)
  | Term.Var _ | Term.Global _ | Term.Univ _ | Term.Ran (_, _) | Term.In (_, _, _)
  | Term.Sec (_, _) | Term.Out (_, _, _) | Term.Elim _ | Term.Let (_, _, _, _)
  | Term.Ann (_, _) | Term.Lit _ | Term.Auto ->
      wrong

(** M1 Stage G, brief 3.9:  one mu group.  Every member is declared
    before the first constructor of the group is installed, so a field
    type of the first member names the last (A4, M1-PLAN.md:95, SG-D17),
    and the group of the positivity walk is every member name. *)
let elab_mu_group ?(budget : Budget.t = Budget.unlimited) (globals : Global.t)
    (fams : Syntax.fam list) : (Global.t, Error.t) result =
  let group = List.map (fun (fm : Syntax.fam) -> fm.Syntax.fm_name) fams in
  let* declared =
    List.fold_left
      (fun (acc : (Global.t, Error.t) result) (fm : Syntax.fam) ->
        let* g = acc in
        let* d = elab_fam_decl (Check.make g budget) fm in
        Check.declare_family ~budget g d)
      (Ok globals) fams
  in
  List.fold_left
    (fun (acc : (Global.t, Error.t) result) (fm : Syntax.fam) ->
      let* g = acc in
      let* _params, cp = elab_telescope (Check.make g budget) fm.Syntax.fm_params in
      let* cds =
        Rules.all_ok (List.map (elab_ctor_decl cp fm.Syntax.fm_name) fm.Syntax.fm_ctors)
      in
      Check.define_ctors ~budget g ~group ~name:fm.Syntax.fm_name cds)
    (Ok declared) fams

(** One declaration, elaborated into the row [Check.check_decls] reads.
    A definition's body is elaborated at its declared type, which is what
    gives every checking position form its expectation. *)
let elab_decl (c : Check.ctx) (d : Syntax.decl) : (Check.decl, Error.t) result =
  match d with
  | Syntax.DDef (name, ty, body) ->
      let* ty' = elab c ~expected:None ty in
      let* tyv = eval_in c ty' in
      let* body' = elab c ~expected:(Some tyv) body in
      Ok
        {
          Check.d_name = name;
          d_kind = Check.Definition;
          d_ty = ty';
          d_body = Some body';
        }
  | Syntax.DAxiom (name, ty) ->
      let* ty' = elab c ~expected:None ty in
      Ok { Check.d_name = name; d_kind = Check.Postulate; d_ty = ty'; d_body = None }
  (* M1 Stage G:  a mu group is a table of families and no entry, so
     [elab_program] installs it and this row is never asked for one. *)
  | Syntax.DMu (_fams : Syntax.fam list) ->
      Error (Error.Mismatch "a mu group declares no entry of its own")
  (* M1 Stage I, SI-D9:  a recursive group is guarded and translated as
     a group, so [elab_rec_group] below owns the row and this one is
     never asked for a member. *)
  | Syntax.DRec (_ms : Syntax.rec_def list) ->
      Error (Error.Mismatch "a recursive group is elaborated as a group")

(** M1 Stage I, brief 3.7 and SI-D9:  one recursive definition group,
    in the shape of the pin install site at
    kan-lang-tot-pin/lib/check.ml:1558.  The order is one order and not
    two:  every member type is checked, every member enters the
    environment at that type so that a self reference and a sibling
    reference resolve, every body is elaborated at its type, then
    [Totality.guard_group] (lib/totality.ml:127) runs over the whole
    group, and only a certificate reaches [Order.translate]
    (lib/order.ml:538).  An unguarded definition therefore never
    reaches the kernel:  the guard answers the termination error of
    SI-D6 and no elimination is built, which gate SI-G6 reads and
    mutation SI-M1 kills.

    The provisional entry of a member is a postulate at its declared
    type, which is what makes the recursive occurrence checkable
    without a new kernel form (D-M0-2, and lib/global.ml:51 takes no
    third constructor).  The entry the group answers is a definition,
    so the file discloses no axiom (R-Q3) and the checked row of a
    member is the row an M0 definition writes.  A recursive definition
    unfolds only on a constructor at [rec_arg], the guarded position
    of the certificate.  A helper with no group calls is reducible normally
    (lib/global.ml:17-26).

    A group that calls no member of itself answers [Ok None] at the
    guard, which is the pin test at
    kan-lang-tot-pin/lib/totality.ml:57.  That group is a list of
    ordinary definitions and it takes the M0 row of
    [Check.check_decls] unchanged. *)
let elab_rec_group ?(budget : Budget.t = Budget.unlimited) (globals : Global.t)
    (ms : Syntax.rec_def list) :
    (Global.t * (string * Global.entry) list, Error.t) result =
  let* typed =
    List.fold_left
      (fun (acc : ((Syntax.rec_def * Term.t) list, Error.t) result)
           (m : Syntax.rec_def) ->
        let* rows = acc in
        let* ty = elab (Check.make globals budget) ~expected:None m.Syntax.rd_ty in
        Ok (rows @ [ (m, ty) ]))
      (Ok []) ms
  in
  let* declared =
    Check.check_decls ~budget globals
      (List.map
         (fun (((m : Syntax.rec_def), (ty : Term.t)) : Syntax.rec_def * Term.t) ->
           {
             Check.d_name = m.Syntax.rd_name;
             d_kind = Check.Postulate;
             d_ty = ty;
             d_body = None;
           })
         typed)
  in
  let provisional : Global.t =
    List.fold_left
      (fun (g : Global.t) (((n : string), (e : Global.entry)) : string * Global.entry) ->
        Global.add n e g)
      globals declared
  in
  let* bodies =
    List.fold_left
      (fun (acc : ((string * Term.t * Value.t * Term.t) list, Error.t) result)
           (((m : Syntax.rec_def), (ty : Term.t)) : Syntax.rec_def * Term.t) ->
        let* rows = acc in
        let c = Check.make provisional budget in
        let* tyv = eval_in c ty in
        let* body = elab c ~expected:(Some tyv) m.Syntax.rd_body in
        Ok (rows @ [ (m.Syntax.rd_name, ty, tyv, body) ]))
      (Ok []) typed
  in
  let* cert =
    Totality.guard_group ~budget provisional
      (List.map
         (fun (((n : string), (_ty : Term.t), (_tyv : Value.t), (body : Term.t)) :
                string * Term.t * Value.t * Term.t) -> (n, body))
         bodies)
  in
  let plain (_u : unit) : ((string * Global.entry) list, Error.t) result =
    Check.check_decls ~budget globals
      (List.map
         (fun (((n : string), (ty : Term.t), (_tyv : Value.t), (body : Term.t)) :
                string * Term.t * Value.t * Term.t) ->
           {
             Check.d_name = n;
             d_kind = Check.Definition;
             d_ty = ty;
             d_body = Some body;
           })
         bodies)
  in
  let guarded (c : Order.t) (_u : unit) : ((string * Global.entry) list, Error.t) result =
    List.fold_left
      (fun (acc : ((string * Global.entry) list, Error.t) result)
           (((n : string), (ty : Term.t), (tyv : Value.t), (body : Term.t)) :
             string * Term.t * Value.t * Term.t) ->
        let* rows = acc in
        let* tm = Order.translate c body in
        let* () = Check.check_term ~budget provisional tm tyv in
        Ok
          (rows
          @ [
              ( n,
                Global.Def
                  {
                    Global.ty;
                    def = tm;
                    reducible = true;
                    rec_arg =
                      (if Order.mentions c.Order.o_group body then Some c.Order.o_arg
                       else None);
                    partial = false;
                  } );
            ]))
      (Ok []) bodies
  in
  let* out =
    cert |> Option.fold ~none:plain ~some:guarded
    |> fun (k : unit -> ((string * Global.entry) list, Error.t) result) -> k ()
  in
  Ok
    ( List.fold_left
        (fun (g : Global.t) (((n : string), (e : Global.entry)) : string * Global.entry) ->
          Global.add n e g)
        globals out,
      out )

(** The whole file, with the globals the last declaration was checked
    in.  Each declaration is elaborated against the entries checked
    before it and then checked, so a self reference finds no entry and
    the checker answers [Unbound] (plan section 6).  M1 Stage G: a mu
    group moves the family table and adds no entry row, so a caller
    that erases the file reads these globals and not the rows alone,
    which carry no family (brief 3.8). *)
let elab_program_in ?(budget : Budget.t = Budget.unlimited) (globals : Global.t)
    (ds : Syntax.decl list) :
    (Global.t * (string * Global.entry) list, Error.t) result =
  List.fold_left
    (fun
      (acc : (Global.t * (string * Global.entry) list, Error.t) result)
      (d : Syntax.decl)
    ->
      let* g, rows = acc in
      match d with
      (* M1 Stage G:  a mu group moves the family table and adds no
         entry row, so the checked form and the erased form of a file
         that only declares families are both empty. *)
      | Syntax.DMu fams ->
          Result.map
            (fun (g' : Global.t) -> (g', rows))
            (elab_mu_group ~budget g fams)
      (* M1 Stage I, SI-D9:  the group is guarded before it is
         translated, and its members join the rows in declaration
         order. *)
      | Syntax.DRec ms ->
          Result.map
            (fun (((g' : Global.t), (out : (string * Global.entry) list)) :
                   Global.t * (string * Global.entry) list) ->
              (g', List.rev_append out rows))
            (elab_rec_group ~budget g ms)
      | Syntax.DDef (_, _, _) | Syntax.DAxiom (_, _) ->
          let* row = elab_decl (Check.make g budget) d in
          let* checked = Check.check_decls ~budget g [ row ] in
          let* name, entry =
            Rules.one_of checked
            |> Option.to_result
                 ~none:
                   (Error.Cannot_infer "the checker answered no entry for a declaration")
          in
          Ok (Global.add name entry g, (name, entry) :: rows))
    (Ok (globals, []))
    ds
  |> Result.map
       (fun ((g : Global.t), (rows : (string * Global.entry) list)) ->
         (g, List.rev rows))

(** The entry rows alone, for a caller that reads no family. *)
let elab_program ?(budget : Budget.t = Budget.unlimited) (globals : Global.t)
    (ds : Syntax.decl list) : ((string * Global.entry) list, Error.t) result =
  Result.map snd (elab_program_in ~budget globals ds)

(** The checked form of one entry, the text "kanon check --print" writes
    and the suite compares against a golden file.  It is the kernel term,
    printed by pp.ml, so the golden shows what the checker accepted and
    not what the file said. *)
let entry_text ((name : string), (e : Global.entry)) : string =
  match e with
  | Global.Def d ->
      Printf.sprintf "def %s : %s := %s\n" name (Pp.term [] d.Global.ty)
        (Pp.term [] d.Global.def)
  | Global.Axiom a -> Printf.sprintf "axiom %s : %s\n" name (Pp.term [] a.Global.ax_ty)
  | Global.Prim p -> Printf.sprintf "prim %s : %s\n" name (Pp.term [] p.Global.p_ty)

let checked_form (rows : (string * Global.entry) list) : string =
  String.concat "" (List.map entry_text rows)

(** The axiom disclosure of R-Q3:  the postulates of the file, in
    declaration order. *)
let axiom_names (rows : (string * Global.entry) list) : string list =
  List.filter_map
    (fun ((name : string), (e : Global.entry)) ->
      Global.axiom_of e |> Option.map (fun (_a : Global.axiom_entry) -> name))
    rows

(** The whole surface pass over a file:  parse, elaborate and check,
    and answer the globals the file was checked in beside its entry
    rows (M1 Stage G, brief 3.8). *)
let check_in ?(budget : Budget.t = Budget.unlimited) (globals : Global.t)
    (src : string) : (Global.t * (string * Global.entry) list, Error.t) result =
  let* ds = Parser.parse src in
  elab_program_in ~budget globals ds

(** The same pass, for a caller that reads the entry rows alone. *)
let check_text ?(budget : Budget.t = Budget.unlimited) (globals : Global.t)
    (src : string) : ((string * Global.entry) list, Error.t) result =
  Result.map snd (check_in ~budget globals src)

(** Lanyard M0 lowers target declarations to the carried kernel here. *)
module Target = Lanyard_target.Target_generated

type operation = { op_name : string; op_args : Syntax.binder list; op_response : Syntax.t }
type lan_decl =
  | Core of Syntax.decl
  | Model of string * (string * Syntax.t) list
  | Signature of string * Syntax.t * operation list

type foreign_instance = {
  instance_name : string;
  schema : Target.entry;
  type_arguments : (string * Syntax.t) list;
}

type model_info = { model_name : string; fields : (string * Syntax.t) list }
type lan_program = {
  globals : Global.t;
  rows : (string * Global.entry) list;
  models : model_info list;
  instances : foreign_instance list;
}

let lan_error (message : string) : ('a, Error.t) result =
  Error (Error.Cannot_infer message)

let target_name (name : string) : string =
  String.split_on_char ':' name
  |> List.concat_map (String.split_on_char '.')
  |> List.filter (fun part -> not (String.equal part ""))
  |> String.concat "_"

(** Qualified foreign names use one flat kernel namespace. Numeric
    projections retain their tokens. The explicit w mark is Many. *)
let rec target_tokens (tokens : Token.t list) : Token.t list =
  match tokens with
  | { Token.kind = Token.Ident left; loc }
    :: { Token.kind = Token.Dot; loc = _ }
    :: { Token.kind = Token.Ident right; loc = _ } :: rest
  | { Token.kind = Token.Ident left; loc }
    :: { Token.kind = Token.Colon; loc = _ }
    :: { Token.kind = Token.Colon; loc = _ }
    :: { Token.kind = Token.Ident right; loc = _ } :: rest ->
      target_tokens ({ Token.kind = Token.Ident (left ^ "_" ^ right); loc } :: rest)
  | ({ Token.kind = Token.LParen; loc = _ } as first)
    :: { Token.kind = Token.Ident "w"; loc = _ }
    :: ({ Token.kind = Token.Ident _; loc = _ } as name)
    :: ({ Token.kind = Token.Colon; loc = _ } as colon) :: rest ->
      first :: name :: colon :: target_tokens rest
  | first :: rest -> first :: target_tokens rest
  | [] -> []

let target_type (source : string) : (Syntax.t, Error.t) result =
  let* tokens = Lexer.lex source in
  let* ty, rest = Parser.parse_term (target_tokens tokens) in
  match rest with
  | [ { Token.kind = Token.Eof; loc = _ } ] -> Ok ty
  | ({ Token.kind = _; loc = _ } :: _ | []) -> Parser.expected "end of type" rest

let name_taken (g : Global.t) (name : string) : bool =
  Option.is_some (Global.find name g) || Option.is_some (Global.find_family name g)
  || Option.is_some (find_ctor name g)

let fresh_names (g : Global.t) (names : string list) : (unit, Error.t) result =
  let* _seen = List.fold_left
    (fun acc name ->
      let* seen = acc in
      if name_taken g name || List.exists (String.equal name) seen then
        lan_error ("duplicate declaration " ^ name)
      else Ok (name :: seen))
    (Ok []) names in
  Ok ()

let decl_names (decl : Syntax.decl) : string list =
  match decl with
  | Syntax.DDef (name, _, _) | Syntax.DAxiom (name, _) -> [ name ]
  | Syntax.DRec members -> List.map (fun m -> m.Syntax.rd_name) members
  | Syntax.DMu families -> List.concat_map
      (fun f -> f.Syntax.fm_name :: List.map (fun c -> c.Syntax.fc_name) f.Syntax.fm_ctors)
      families

let add_lan_core (budget : Budget.t) (g : Global.t) (decls : Syntax.decl list) :
    (Global.t * (string * Global.entry) list, Error.t) result =
  let* () = fresh_names g (List.concat_map decl_names decls) in
  elab_program_in ~budget g decls

(** Peel the checked telescope, not the catalog's kind label or text. *)
let rec universe_result (g : Global.t) (depth : int) (ty : Value.t) :
    (bool, Error.t) result =
  match ty with
  | Value.VUniv _ -> Ok true
  | Value.VRan (shape, codomain, _) ->
      Rules.as_vpi shape |> Option.fold ~none:(Ok false)
        ~some:(fun (_q, _name, _domain) ->
          let* result = Rules.open_closure (Eval.ev g) codomain [ Value.var depth ] in
          universe_result g (depth + 1) result)
  | Value.VLan (_, _, _) | Value.VIn (_, _, _) | Value.VSec (_, _)
  | Value.VLit _ | Value.VNeutral (_, _) -> Ok false

let closed_atoms : string list =
  [ "Db"; "Cx"; "Uri"; "Response"; "SeeOther"; "Deferred"; "Form";
    "toasty::Error"; "topcoat::Error" ]

(** Install type rows first, because file order interleaves libraries.
    Every row is checked as an ordinary postulate before it joins globals. *)
let target_environment ?(budget : Budget.t = Budget.unlimited)
    ?(entries : Target.entry list = Target.entries) () :
    (Global.t * (string * Global.entry) list * string list, Error.t) result =
  let types, values = List.partition
    (fun (entry : Target.entry) -> match entry.kind with
      | Target.Type_constant -> true
      | Target.Constant | Target.Schema -> false) entries in
  let* g, rows, atoms = List.fold_left
    (fun acc (entry : Target.entry) ->
      let* g, rows, atoms = acc in
      let* ty = target_type entry.kernel_type in
      let name = target_name entry.name in
      let* next, out = add_lan_core budget g [ Syntax.DAxiom (name, ty) ] in
      let* installed = Global.find name next
        |> Option.to_result ~none:(Error.Unbound name) in
      let* value = Eval.eval g [] (Global.entry_ty installed) in
      let* is_type = universe_result g 0 value in
      let declared_type = match entry.kind with
        | Target.Type_constant -> true
        | Target.Constant | Target.Schema -> false in
      if not (Bool.equal is_type declared_type) then
        lan_error ("R0-TARGET: kind disagrees with checked type of " ^ entry.name)
      else if is_type && not (List.exists (String.equal entry.name) closed_atoms) then
        lan_error ("R0-TARGET: foreign type constant outside closed atom list: " ^ entry.name)
      else Ok (next, List.rev_append out rows,
               if is_type then entry.name :: atoms else atoms))
    (Ok (Global.initial, [], [])) (types @ values) in
  if List.sort String.compare atoms <> List.sort String.compare closed_atoms then
    lan_error "R0-TARGET: foreign atom inventory differs"
  else Ok (g, List.rev rows, List.rev atoms)

(** Normalize before rejecting exponents, including those inside products,
    sums, foreign arguments and closed inductive fields. The visited set
    closes cycles only for families without parameters or indices. *)
let rec first_order_in (g : Global.t) (seen : string list) (value : Value.t) :
    (bool, Error.t) result =
  match value with
  | Value.VRan (shape, diagram, _) | Value.VLan (shape, diagram, _) ->
      if Option.is_some (Shape.point_dom shape) then Ok false
      else if Option.is_some (Rules.as_vcoll shape) then
        let* legs = Rules.coll_legs_of Check.ops (Check.make g Budget.unlimited) diagram in
        let* results = Rules.all_ok (List.map (fun (leg : Value.vleg) ->
          let* field = Rules.open_closure (Eval.ev g) leg.Value.vl_clo [] in
          first_order_in g seen field) legs) in
        Ok (List.for_all Fun.id results)
      else Shape.family shape |> Option.fold ~none:(Ok false) ~some:(fun name ->
        Global.find_family name g |> Option.fold ~none:(Ok false) ~some:(fun family ->
          if not (List.is_empty family.Positivity.f_params
                  && List.is_empty family.Positivity.f_indices) then Ok false
          else if List.exists (String.equal name) seen then Ok true
          else
            let* constructors = Rules.all_ok (List.map (fun ctor ->
              let* _env, accepted = List.fold_left (fun acc (_q, _field, ty) ->
                let* env, accepted = acc in
                let* field = Eval.eval g env ty in
                let* ok = first_order_in g (name :: seen) field in
                Ok (Value.var (List.length env) :: env, accepted && ok))
                (Ok ([], true)) ctor.Positivity.c_args in
              Ok accepted) family.Positivity.f_ctors) in
            Ok (List.for_all Fun.id constructors)))
  | Value.VNeutral (Value.HGlobal name, spine) ->
      if not (String.equal name "Nat"
              || List.exists (fun atom -> String.equal name (target_name atom)) closed_atoms)
      then Ok false
      else
        let* args = Rules.all_ok (List.map (fun frame -> match frame with
          | Value.SOut (_shape, Value.VAPt (_q, arg)) -> first_order_in g seen arg
          | Value.SOut (_, Value.VALeg _) | Value.SOut (_, Value.VACtor _)
          | Value.SElim _ -> Ok false) spine) in
        Ok (List.for_all Fun.id args)
  | Value.VUniv _ | Value.VIn (_, _, _) | Value.VSec (_, _) | Value.VLit _
  | Value.VNeutral (Value.HLocal _, _) -> Ok false

let check_first_order_context (c : Check.ctx) (label : string)
    (ty : Syntax.t) : (unit, Error.t) result =
  let* term = elab c ~expected:None ty in
  let* _level = Check.infer_univ c term in
  let* value = eval_in c term in
  let* accepted = first_order_in (globals_of c) [] value in
  if accepted then Ok ()
  else lan_error (label ^ ": response must be first order through M2 (exponent or unsupported type)")

let check_first_order (budget : Budget.t) (g : Global.t) (label : string)
    (ty : Syntax.t) : (unit, Error.t) result =
  check_first_order_context (Check.make g budget) label ty

(** These declaration words are reserved only at the .lan entry point.
    Core spans retain their original tokens and locations. *)
let rec core_span (tokens : Token.t list) (acc : Token.t list) :
    Token.t list * Token.t list =
  match tokens with
  | ({ Token.kind = Token.Ident ("model" | "signature"); loc } :: _rest)
  | ({ Token.kind = Token.Eof; loc } :: _rest) ->
      (List.rev ({ Token.kind = Token.Eof; loc } :: acc), tokens)
  | first :: rest -> core_span rest (first :: acc)
  | [] -> (List.rev ({ Token.kind = Token.Eof; loc = Token.start } :: acc), [])

let rec model_fields (tokens : Token.t list) (acc : (string * Syntax.t) list) :
    ((string * Syntax.t) list * Token.t list, Error.t) result =
  match tokens with
  | { Token.kind = Token.KEnd; loc = _ } :: rest -> Ok (List.rev acc, rest)
  | { Token.kind = Token.Pipe; loc = _ }
    :: { Token.kind = Token.Ident name; loc = _ }
    :: { Token.kind = Token.Colon; loc = _ } :: rest ->
      let* ty, tail = Parser.parse_term rest in
      model_fields tail ((name, ty) :: acc)
  | ({ Token.kind = _; loc = _ } :: _ | []) ->
      Parser.expected "'| FIELD : TYPE' or 'end'" tokens

let rec signature_ops (tokens : Token.t list) (acc : operation list) :
    (operation list * Token.t list, Error.t) result =
  match tokens with
  | { Token.kind = Token.KEnd; loc = _ } :: rest -> Ok (List.rev acc, rest)
  | { Token.kind = Token.Pipe; loc = _ }
    :: { Token.kind = Token.Ident name; loc = _ } :: rest ->
      let* args, tail = Parser.parse_binders rest [] in
      (match tail with
       | { Token.kind = Token.Colon; loc = _ } :: body ->
           let* response, after = Parser.parse_term body in
           signature_ops after ({ op_name = name; op_args = args; op_response = response } :: acc)
       | ({ Token.kind = _; loc = _ } :: _ | []) -> Parser.expected "':'" tail)
  | ({ Token.kind = _; loc = _ } :: _ | []) ->
      Parser.expected "'| OPERATION (ARG : TYPE) : RESPONSE' or 'end'" tokens

let rec lan_decls (tokens : Token.t list) (acc : lan_decl list) :
    (lan_decl list, Error.t) result =
  match tokens with
  | [ { Token.kind = Token.Eof; loc = _ } ] | [] -> Ok (List.rev acc)
  | { Token.kind = Token.Ident "model"; loc = _ }
    :: { Token.kind = Token.Ident name; loc = _ }
    :: { Token.kind = Token.KWith; loc = _ } :: rest ->
      let* fields, tail = model_fields rest [] in
      lan_decls tail (Model (name, fields) :: acc)
  | { Token.kind = Token.Ident "signature"; loc = _ }
    :: { Token.kind = Token.Ident name; loc = _ }
    :: { Token.kind = Token.Colon; loc = _ } :: rest ->
      let* result, tail = Parser.parse_term rest in
      (match tail with
       | { Token.kind = Token.KWith; loc = _ } :: body ->
           let* ops, after = signature_ops body [] in
           lan_decls after (Signature (name, result, ops) :: acc)
       | ({ Token.kind = _; loc = _ } :: _ | []) -> Parser.expected "'with'" tail)
  | ({ Token.kind = Token.Ident ("model" | "signature"); loc = _ } :: _rest) ->
      Parser.expected "a model or signature declaration header" tokens
  | ({ Token.kind = _; loc = _ } :: _) ->
      let prefix, tail = core_span tokens [] in
      let* decls = Parser.parse_decls prefix [] in
      lan_decls tail (List.rev_append (List.map (fun d -> Core d) decls) acc)

let binder (name : string) (ty : Syntax.t) : Syntax.binder =
  { Syntax.b_name = name; b_q = Quantity.Many; b_ty = ty }

let arrows (args : Syntax.binder list) (result : Syntax.t) : Syntax.t =
  List.fold_right (fun arg body -> Syntax.SArrow (arg, body)) args result

let elab_signature (budget : Budget.t) (g : Global.t) (name : string)
    (result : Syntax.t) (operations : operation list) : (Global.t, Error.t) result =
  let* () = check_first_order budget g ("signature " ^ name) result in
  let* () = fresh_names Global.empty (List.map (fun op -> op.op_name) operations) in
  let* _checks = Rules.all_ok (List.map (fun op ->
    let* () = fresh_names Global.empty (List.map (fun arg -> arg.Syntax.b_name) op.op_args) in
    let* context = List.fold_left (fun acc arg ->
      let* c = acc in
      if String.equal arg.Syntax.b_name name then
        lan_error ("operation " ^ op.op_name ^ ": argument shadows signature " ^ name)
      else
        let* term = elab c ~expected:None arg.Syntax.b_ty in
        let* _level = Check.infer_univ c term in
        let* ty = eval_in c term in
        Ok (Check.bind arg.Syntax.b_name arg.Syntax.b_q ty c))
      (Ok (Check.make g budget)) op.op_args in
    check_first_order_context context ("operation " ^ op.op_name) op.op_response) operations) in
  let family = Syntax.SVar name in
  let pure = { Syntax.fc_name = name ^ "_pure";
               fc_ty = arrows [ binder "value" result ] family } in
  let ctors = List.map (fun op ->
    (* Anonymous continuation binders avoid capturing argument names. *)
    let resume = binder "_" (arrows [ binder "_" op.op_response ] family) in
    { Syntax.fc_name = name ^ "_" ^ op.op_name;
      fc_ty = arrows (op.op_args @ [ resume ]) family }) operations in
  let fm = { Syntax.fm_name = name; fm_params = []; fm_ty = Syntax.SType 0;
             fm_ctors = pure :: ctors } in
  let* () = fresh_names g (decl_names (Syntax.DMu [ fm ])) in
  elab_mu_group ~budget g [ fm ]

(** Specialization asks the kernel for the application type. The instance
    retains its source row and type arguments for print-rule selection. *)
let elab_model (budget : Budget.t) (g : Global.t) (name : string)
    (fields : (string * Syntax.t) list) :
    (Global.t * (string * Global.entry) list * foreign_instance list, Error.t) result =
  let* () = fresh_names Global.empty (List.map fst fields) in
  let* _checks = Rules.all_ok (List.map (fun (field, ty) ->
    check_first_order budget g ("model field " ^ name ^ "." ^ field) ty) fields) in
  let* g, rows = add_lan_core budget g
    [ Syntax.DDef (name, Syntax.SType 0, Syntax.SProd (List.map snd fields)) ] in
  let schemas = List.filter (fun (row : Target.entry) ->
    String.starts_with ~prefix:"Model." row.name) Target.entries in
  List.fold_left (fun acc (schema : Target.entry) ->
    let* g, rows, instances = acc in
    let* ty = target_type schema.kernel_type in
    let rec arguments (body : Syntax.t) (acc : (string * Syntax.t) list) :
        ((string * Syntax.t) list, Error.t) result =
      match body with
      | Syntax.SArrow (arg, rest) when Quantity.equal arg.Syntax.b_q Quantity.Zero ->
          let* actual =
            if String.equal arg.Syntax.b_name "M" then Ok (Syntax.SVar name)
            else if String.equal arg.Syntax.b_name "Key" then
              List.assoc_opt "id" fields
              |> Option.to_result ~none:(Error.Cannot_infer ("model " ^ name ^ " needs an id field"))
            else lan_error ("unsupported model schema parameter " ^ arg.Syntax.b_name) in
          arguments rest ((arg.Syntax.b_name, actual) :: acc)
      | Syntax.SArrow (_, _) | Syntax.SVar _ | Syntax.SNat _ | Syntax.SProp | Syntax.SType _
      | Syntax.SPrim _ | Syntax.SUnit | Syntax.SAuto | Syntax.SPair (_, _) | Syntax.STuple _
      | Syntax.SSum _ | Syntax.SProd _ | Syntax.SProj (_, _) | Syntax.SInj (_, _, _)
      | Syntax.SAbsurd _ | Syntax.SApp (_, _) | Syntax.SFun (_, _) | Syntax.SStar (_, _)
      | Syntax.SLet (_, _, _, _) | Syntax.SAnn (_, _) | Syntax.SCase (_, _, _)
      | Syntax.SMatch (_, _, _) -> Ok (List.rev acc) in
    let* args = arguments ty [] in
    let application = List.fold_left (fun fn (_param, arg) -> Syntax.SApp (fn, arg))
      (Syntax.SVar (target_name schema.name)) args in
    let c = Check.make g budget in
    let* term = elab c ~expected:None application in
    let* instance_ty = Check.infer c Quantity.Zero term in
    let* closed_ty = Eval.quote g 0 instance_ty in
    let suffix = schema.name |> String.to_seq |> Seq.drop 6 |> String.of_seq in
    let instance_name = name ^ "_" ^ target_name suffix in
    let* () = fresh_names g [ instance_name ] in
    let declaration = { Check.d_name = instance_name; d_kind = Check.Postulate;
                        d_ty = closed_ty; d_body = None } in
    let* entry = Check.check_decl g budget declaration in
    Ok (Global.add instance_name entry g, rows @ [ (instance_name, entry) ],
        instances @ [ { instance_name; schema; type_arguments = args } ]))
    (Ok (g, rows, [])) schemas

let check_lanyard ?(budget : Budget.t = Budget.unlimited) (source : string) :
    (lan_program, Error.t) result =
  let* globals, rows, _atoms = target_environment ~budget () in
  let* tokens = Lexer.lex source in
  let* decls = lan_decls (target_tokens tokens) [] in
  List.fold_left (fun acc decl ->
    let* program = acc in
    match decl with
    | Core core ->
        let* globals, rows = add_lan_core budget program.globals [ core ] in
        Ok { program with globals; rows = program.rows @ rows }
    | Signature (name, result, operations) ->
        let* globals = elab_signature budget program.globals name result operations in
        Ok { program with globals }
    | Model (name, fields) ->
        let* globals, rows, instances = elab_model budget program.globals name fields in
        Ok { globals; rows = program.rows @ rows;
             models = program.models @ [ { model_name = name; fields } ];
             instances = program.instances @ instances })
    (Ok { globals; rows; models = []; instances = [] }) decls

let check_lanyard_in ?(budget : Budget.t = Budget.unlimited) (source : string) :
    (Global.t * (string * Global.entry) list, Error.t) result =
  check_lanyard ~budget source |> Result.map (fun p -> (p.globals, p.rows))
