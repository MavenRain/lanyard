(** A UTF-8 file path anchored to the invocation directory, without opening it. *)
type t
val parse : directory:string -> string -> (t, Kanon_kernel.Error.t) result
val rust_string : t -> string
