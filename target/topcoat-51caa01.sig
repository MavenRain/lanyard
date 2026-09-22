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
{"name":"Text.trim_start","type":"(0 Text : Type 0) -> (text : Text) -> Text","quantities":["0","w"],"effects":[],"print":"#{text}.trim_start().to_owned()","kind":"schema","status":"PROPOSED"}
{"name":"Text.trim_end","type":"(0 Text : Type 0) -> (text : Text) -> Text","quantities":["0","w"],"effects":[],"print":"#{text}.trim_end().to_owned()","kind":"schema","status":"PROPOSED"}
{"name":"Text.is_empty","type":"(0 Text : Type 0) -> (text : Text) -> sum ((prod () : Type 0), (prod () : Type 0))","quantities":["0","w"],"effects":[],"print":"#{text}.is_empty()","kind":"schema","status":"PROPOSED"}
{"name":"Text.equal","type":"(0 Text : Type 0) -> (left : Text) -> (right : Text) -> sum ((prod () : Type 0), (prod () : Type 0))","quantities":["0","w","w"],"effects":[],"print":"#{left} == #{right}","kind":"schema","status":"PROPOSED"}
{"name":"Text.contains","type":"(0 Text : Type 0) -> (text : Text) -> (needle : Text) -> sum ((prod () : Type 0), (prod () : Type 0))","quantities":["0","w","w"],"effects":[],"print":"#{text}.contains(#{needle}.as_str())","kind":"schema","status":"PROPOSED"}
{"name":"Text.starts_with","type":"(0 Text : Type 0) -> (text : Text) -> (needle : Text) -> sum ((prod () : Type 0), (prod () : Type 0))","quantities":["0","w","w"],"effects":[],"print":"#{text}.starts_with(#{needle}.as_str())","kind":"schema","status":"PROPOSED"}
{"name":"Text.ends_with","type":"(0 Text : Type 0) -> (text : Text) -> (needle : Text) -> sum ((prod () : Type 0), (prod () : Type 0))","quantities":["0","w","w"],"effects":[],"print":"#{text}.ends_with(#{needle}.as_str())","kind":"schema","status":"PROPOSED"}
{"name":"Text.replace","type":"(0 Text : Type 0) -> (text : Text) -> (needle : Text) -> (replacement : Text) -> Text","quantities":["0","w","w","w"],"effects":[],"print":"#{text}.replace(#{needle}.as_str(), #{replacement}.as_str())","kind":"schema","status":"PROPOSED"}
{"name":"Text.repeat","type":"(0 Text : Type 0) -> (text : Text) -> (count : Nat) -> Text","quantities":["0","w","w"],"effects":["topcoat::Error"],"print":"lan_text_repeat(&#{text}, &#{count})?","kind":"schema","status":"PROPOSED"}
{"name":"Text.length","type":"(0 Text : Type 0) -> (text : Text) -> Nat","quantities":["0","w"],"effects":[],"print":"Nat::canonical(#{text}.len().to_le_bytes().to_vec())","kind":"schema","status":"PROPOSED"}
{"name":"Text.concat","type":"(0 Text : Type 0) -> (left : Text) -> (right : Text) -> Text","quantities":["0","w","w"],"effects":[],"print":"#{left} + &#{right}","kind":"schema","status":"PROPOSED"}
{"name":"Text.from_nat","type":"(0 Text : Type 0) -> (value : Nat) -> Text","quantities":["0","w"],"effects":[],"print":"lan_text_from_nat(&#{value})","kind":"schema","status":"PROPOSED"}
{"name":"Text.to_nat","type":"(0 Text : Type 0) -> (text : Text) -> Nat","quantities":["0","w"],"effects":["topcoat::Error"],"print":"lan_text_to_nat(&#{text})?","kind":"schema","status":"PROPOSED"}
{"name":"Uri.from_text","type":"(0 Text : Type 0) -> (text : Text) -> Uri","quantities":["0","w"],"effects":["topcoat::Error"],"print":"#{text}.parse::<topcoat::router::Uri>().map_err(|_error| Error::InvalidUri)?","kind":"schema","status":"PROPOSED"}
{"name":"Uri.to_text","type":"(0 Text : Type 0) -> (uri : Uri) -> Text","quantities":["0","w"],"effects":[],"print":"#{uri}.to_string()","kind":"schema","status":"PROPOSED"}
{"name":"Uri.path","type":"(0 Text : Type 0) -> (uri : Uri) -> Text","quantities":["0","w"],"effects":[],"print":"#{uri}.path().to_owned()","kind":"schema","status":"PROPOSED"}
{"name":"Uri.query","type":"(0 Text : Type 0) -> (uri : Uri) -> Text","quantities":["0","w"],"effects":[],"print":"#{uri}.query().map(str::to_owned).unwrap_or_default()","kind":"schema","status":"PROPOSED"}
{"name":"Form.field","type":"(0 Text : Type 0) -> (text : Text) -> (field : Text) -> Text","quantities":["0","w","w"],"effects":["topcoat::Error"],"print":"lan_form_field(&#{text}, &#{field})?","kind":"schema","status":"PROPOSED"}
{"name":"Form.has","type":"(0 Text : Type 0) -> (text : Text) -> (field : Text) -> sum ((prod () : Type 0), (prod () : Type 0))","quantities":["0","w","w"],"effects":["topcoat::Error"],"print":"lan_form_has(&#{text}, &#{field})?","kind":"schema","status":"PROPOSED"}
{"name":"Response.text","type":"(0 Text : Type 0) -> (text : Text) -> Response","quantities":["0","w"],"effects":[],"print":"{ let mut response = topcoat::router::response::Response::new(topcoat::router::Body::from(#{text})); response.headers_mut().insert(topcoat::router::header::CONTENT_TYPE, topcoat::router::HeaderValue::from_static(\"text/plain; charset=utf-8\")); response }","kind":"schema","status":"PROPOSED"}
{"name":"Html.text","type":"(0 Text : Type 0) -> (text : Text) -> Text","quantities":["0","w"],"effects":[],"print":"#{text}.replace('&', \"&amp;\").replace('<', \"&lt;\").replace('>', \"&gt;\")","kind":"schema","status":"PROPOSED"}
{"name":"Response.html","type":"(0 Text : Type 0) -> (text : Text) -> Response","quantities":["0","w"],"effects":[],"print":"{ let mut response = topcoat::router::response::Response::new(topcoat::router::Body::from(#{text})); response.headers_mut().insert(topcoat::router::header::CONTENT_TYPE, topcoat::router::HeaderValue::from_static(\"text/html; charset=utf-8\")); response }","kind":"schema","status":"PROPOSED"}
