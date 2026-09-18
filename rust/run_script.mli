(** A validated, bounded sequence of scripted requests. *)
type request = { uri : string; form : string option }
type t
val max_bytes : int
val max_requests : int
val parse : string -> (t, Kanon_kernel.Error.t) result
val requests : t -> request list
