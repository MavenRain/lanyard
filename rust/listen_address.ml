type t = Port of int
let port (Port value) = value
let parse text =
  let invalid () = Error (Kanon_kernel.Error.Mismatch
    "listen address must be 127.0.0.1:PORT with a decimal port from 0 through 65535") in
  match String.split_on_char ':' text with
  | ["127.0.0.1"; value] when value <> "" && String.length value <= 5
      && String.for_all (fun c -> c >= '0' && c <= '9') value ->
      int_of_string_opt value |> Option.fold ~none:(invalid ()) ~some:(fun value ->
        if value <= 65535 then Ok (Port value) else invalid ())
  | [] | _ :: _ -> invalid ()
