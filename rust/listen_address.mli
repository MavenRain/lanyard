(** A numeric loopback endpoint, validated before program or output I/O. *)
type t
val parse : string -> (t, Kanon_kernel.Error.t) result
val port : t -> int
