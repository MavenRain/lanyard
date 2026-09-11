include!("golden.rs");

fn assert_send<F: std::future::Future + Send>(future: F) -> F { future }

fn check_futures(
    db: Arc<toasty::Db>,
    shared: Arc<topcoat::router::content::Form<topcoat::router::Uri>>,
    owned: toasty::Deferred<topcoat::router::Uri>,
) {
    drop(assert_send(f_6b656570(Arc::clone(&db), shared)));
    drop(assert_send(f_6b6565704f776e6564(db, owned)));
}

fn main() -> Result<(), Error> {
    let form = topcoat::router::content::Form::from(topcoat::router::Uri::from_static("/pinned"));
    println!("{}", &*f_6d6f7665466f726d(form)?);
    let deferred = toasty::Deferred::from(topcoat::router::Uri::from_static("/deferred"));
    println!("{}", f_6d6f76654465666572726564(deferred)?.is_unloaded());
    println!("{}", f_6d6f76654465666572726564(toasty::Deferred::default())?.is_unloaded());
    let nested = topcoat::router::content::Form::from(toasty::Deferred::from(topcoat::router::Uri::from_static("/nested")));
    println!("{}", f_6d6f76654e6573746564(nested)?.is_unloaded());
    let reverse = toasty::Deferred::from(topcoat::router::content::Form::from(topcoat::router::Uri::from_static("/reverse")));
    println!("{}", f_6d6f766552657665727365(reverse)?.is_unloaded());
    let pair = T70726f64756374286e61742c6e617429 { f0: Nat::decimal("7")?, f1: Nat::decimal("11")? };
    let pair = f_6d6f766550616972(topcoat::router::content::Form::from(pair))?;
    println!("{:?} {:?}", pair.f0, pair.f1);
    let bytes = T6e6f6d696e616c28353a427974657329::V1(Box::new((Nat::decimal("65")?, T6e6f6d696e616c28353a427974657329::V0)));
    println!("{}", f_6d6f76654279746573(toasty::Deferred::from(bytes))?.is_unloaded());
    Ok(())
}
