include!("golden.rs");

fn assert_send<F: std::future::Future + Send>(future: F) -> F { future }

fn report(name: &str, passed: bool) -> Result<(), Error> {
    if passed { println!("{name} OK"); Ok(()) }
    else { eprintln!("{name} FAIL"); Err(Error::Arithmetic) }
}

fn nat(number: &str) -> Result<Arc<Nat>, Error> { Nat::decimal(number).map(Arc::new) }

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Error> {
    report("zero", lan_model_to_i64(&lan_model_from_i64(0)?)? == 0)?;
    report("maximum", lan_model_to_i64(&Nat::decimal("9223372036854775807")?)? == i64::MAX)?;
    report("maximum-roundtrip", lan_model_from_i64(i64::MAX)? == Nat::decimal("9223372036854775807")?)?;
    report("overflow", matches!(lan_model_to_i64(&Nat::decimal("9223372036854775808")?), Err(Error::ModelRange)))?;
    report("large-overflow", matches!(lan_model_to_i64(&Nat::decimal("340282366920938463463374607431768211455")?), Err(Error::ModelRange)))?;
    report("negative", matches!(lan_model_from_i64(-1), Err(Error::ModelRange)))?;
    let mut db = toasty::Db::builder()
        .models(toasty::models!(LanModel436f756e746572, LanModel53696e676c65))
        .connect("sqlite::memory:").await?;
    db.push_schema().await?;
    let db = Arc::new(db);
    let created = assert_send(f_726f756e6474726970(Arc::clone(&db))).await?;
    report("create-lookup", lan_model_to_i64(&created.f0)? == 7 && lan_model_to_i64(&created.f1)? == 42)?;
    let found = assert_send(f_6c6f6f6b7570(nat("7")?, Arc::clone(&db))).await?;
    report("lookup", lan_model_to_i64(&found.f1)? == 42)?;
    report("duplicate", matches!(assert_send(f_637265617465(Arc::clone(&db))).await, Err(Error::Database(_))))?;
    report("missing", matches!(f_6c6f6f6b7570(nat("8")?, Arc::clone(&db)).await, Err(Error::Database(_))))?;
    report("key-overflow", matches!(f_6c6f6f6b7570(nat("9223372036854775808")?, Arc::clone(&db)).await, Err(Error::ModelRange)))?;
    let row = Arc::new(T70726f64756374286e61742c6e617429 {
        f0: Nat::decimal("99")?, f1: Nat::decimal("7")?,
    });
    let created = assert_send(f_63726561746553696e676c65(Arc::clone(&row), Arc::clone(&db))).await?;
    report("field-order", lan_model_to_i64(&created.f0)? == 99 && lan_model_to_i64(&created.f1)? == 7)?;
    let found = assert_send(f_6c6f6f6b757053696e676c65(nat("7")?, Arc::clone(&db))).await?;
    report("model-isolation", lan_model_to_i64(&found.f0)? == 99)?;
    report("shared-row", Arc::strong_count(&row) == 1 && lan_model_to_i64(&row.f0)? == 99)?;
    let excessive = Arc::new(T70726f64756374286e61742c6e617429 {
        f0: Nat::decimal("9223372036854775808")?, f1: Nat::decimal("9")?,
    });
    report("field-overflow", matches!(f_63726561746553696e676c65(excessive, Arc::clone(&db)).await, Err(Error::ModelRange)))?;
    report("overflow-no-insert", matches!(f_6c6f6f6b757053696e676c65(nat("9")?, Arc::clone(&db)).await, Err(Error::Database(_))))?;
    let mut direct = (*db).clone();
    toasty::create!(LanModel53696e676c65 { id: 10_i64, f_76616c7565: -1_i64 }).exec(&mut direct).await?;
    report("negative-database-field", matches!(f_6c6f6f6b757053696e676c65(nat("10")?, Arc::clone(&db)).await, Err(Error::ModelRange)))?;
    report("database-sharing", Arc::strong_count(&db) == 1)?;
    Ok(())
}
