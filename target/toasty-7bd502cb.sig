# Stage B: five semantic fields plus kind and status metadata, one JSON object per row.
# PROPOSED becomes printed only with an emitted fixture in a later stage.
{"name":"Db","type":"Type 0","quantities":[],"effects":[],"print":"toasty::Db","kind":"type","status":"PROPOSED"}
{"name":"Deferred","type":"(0 T : Type 0) -> Type 0","quantities":["0"],"effects":[],"print":"toasty::Deferred<#{T}>","kind":"type","status":"PROPOSED"}
{"name":"toasty::Error","type":"Type 0","quantities":[],"effects":[],"print":"toasty::Error","kind":"type","status":"PROPOSED"}
{"name":"Db.connect","type":"(0 Models : Type 0) -> (0 Text : Type 0) -> (url : Text) -> Db","quantities":["0","0","w"],"effects":["DbExec","toasty::Error"],"print":"toasty::Db::builder().models(toasty::models!(#{Models})).connect(#{url}).await?","kind":"schema","status":"PROPOSED"}
{"name":"Db.push_schema","type":"(db : Db) -> prod ()","quantities":["w"],"effects":["DbExec","toasty::Error"],"print":"#{db}.push_schema().await?","kind":"constant","status":"PROPOSED"}
{"name":"Model.create","type":"(0 M : Type 0) -> (fields : M) -> (db : Db) -> M","quantities":["0","w","w"],"effects":["DbExec","toasty::Error"],"print":"toasty::create!(#{M} { #{fields} }).exec(&mut #{db}).await?","kind":"schema","status":"PROPOSED"}
{"name":"Model.get_by_id","type":"(0 M : Type 0) -> (0 Key : Type 0) -> (key : Key) -> (db : Db) -> M","quantities":["0","0","w","w"],"effects":["DbExec","toasty::Error"],"print":"#{M}::get_by_id(&mut #{db}, &#{key}).await?","kind":"schema","status":"PROPOSED"}
