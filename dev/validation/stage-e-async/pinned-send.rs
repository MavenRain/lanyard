include!("lib.rs");

fn assert_send<F: std::future::Future + Send>(_future: F) {}

fn prove(db: Arc<toasty::Db>, uri: Arc<topcoat::router::Uri>) {
    assert_send(f_70757368(Arc::clone(&db)));
    assert_send(f_666f7277617264(Arc::clone(&db)));
    assert_send(f_7477696365(Arc::clone(&db)));
    assert_send(f_73657175656e7469616c(Arc::clone(&db), Arc::clone(&db)));
    assert_send(f_6b656570(Arc::clone(&db), uri));
    assert_send(f_63686f6f7365(Arc::new(T73756d28756e69742c756e697429::V0(())), db));
}
