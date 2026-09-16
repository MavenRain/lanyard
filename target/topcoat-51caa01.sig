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
{"name":"Text.trim","type":"(0 Text : Type 0) -> (text : Text) -> Text","quantities":["0","w"],"effects":[],"print":"#{text}.trim().to_owned()","kind":"schema","status":"PROPOSED"}
{"name":"Text.is_empty","type":"(0 Text : Type 0) -> (text : Text) -> sum ((prod () : Type 0), (prod () : Type 0))","quantities":["0","w"],"effects":[],"print":"#{text}.is_empty()","kind":"schema","status":"PROPOSED"}
{"name":"Uri.from_text","type":"(0 Text : Type 0) -> (text : Text) -> Uri","quantities":["0","w"],"effects":["topcoat::Error"],"print":"#{text}.parse::<topcoat::router::Uri>().map_err(|_error| Error::InvalidUri)?","kind":"schema","status":"PROPOSED"}
{"name":"Form.field","type":"(0 Text : Type 0) -> (text : Text) -> (field : Text) -> Text","quantities":["0","w","w"],"effects":["topcoat::Error"],"print":"lan_form_field(&#{text}, &#{field})?","kind":"schema","status":"PROPOSED"}
{"name":"Response.text","type":"(0 Text : Type 0) -> (text : Text) -> Response","quantities":["0","w"],"effects":[],"print":"{ let mut response = topcoat::router::response::Response::new(topcoat::router::Body::from(#{text})); response.headers_mut().insert(topcoat::router::header::CONTENT_TYPE, topcoat::router::HeaderValue::from_static(\"text/plain; charset=utf-8\")); response }","kind":"schema","status":"PROPOSED"}
