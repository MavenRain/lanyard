# Six roadmap rows, deliberately comments: no generator or gate treats these as constants.
# PROPOSED forms_without_listing_fields: awaiting a pinned library idiom and printed fixture.
# PROPOSED validations: awaiting a pinned library idiom and printed fixture.
# PROPOSED streaming_ssr: awaiting a pinned library idiom and printed fixture.
# PROPOSED islands: awaiting a pinned library idiom and printed fixture.
# PROPOSED background_jobs: awaiting a pinned library idiom and printed fixture.
# PROPOSED authentication: awaiting a pinned library idiom and printed fixture.
{"name":"Cx","type":"Type 0","quantities":[],"effects":[],"print":"topcoat::context::Cx","kind":"type","status":"PROPOSED"}
{"name":"Uri","type":"Type 0","quantities":[],"effects":[],"print":"topcoat::router::Uri","kind":"type","status":"PROPOSED"}
{"name":"Response","type":"Type 0","quantities":[],"effects":[],"print":"topcoat::router::response::Response","kind":"type","status":"PROPOSED"}
{"name":"SeeOther","type":"Type 0","quantities":[],"effects":[],"print":"topcoat::router::error::SeeOther","kind":"type","status":"PROPOSED"}
{"name":"Form","type":"(0 T : Type 0) -> Type 0","quantities":["0"],"effects":[],"print":"topcoat::router::content::Form<#{T}>","kind":"type","status":"PROPOSED"}
{"name":"topcoat::Error","type":"Type 0","quantities":[],"effects":[],"print":"topcoat::Error","kind":"type","status":"PROPOSED"}
{"name":"topcoat.db","type":"(cx : Cx) -> Db","quantities":["w"],"effects":[],"print":"topcoat::context::app_context::<toasty::Db>(#{cx}).clone()","kind":"constant","status":"PROPOSED"}
{"name":"topcoat.see_other","type":"(uri : Uri) -> SeeOther","quantities":["w"],"effects":[],"print":"topcoat::router::error::see_other(#{uri}.to_string())","kind":"constant","status":"PROPOSED"}
