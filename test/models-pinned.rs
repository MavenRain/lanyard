include!("golden.rs");

fn assert_send<F: std::future::Future + Send>(future: F) -> F { future }

fn report(name: &str, passed: bool) -> Result<(), Error> {
    if passed { println!("{name} OK"); Ok(()) }
    else { eprintln!("{name} FAIL"); Err(Error::Arithmetic) }
}

fn nat(number: &str) -> Result<Arc<Nat>, Error> { Nat::decimal(number).map(Arc::new) }
fn is_true(value: &T73756d28756e69742c756e697429) -> bool {
    match value {
        T73756d28756e69742c756e697429::V0(()) => false,
        T73756d28756e69742c756e697429::V1(()) => true,
    }
}

#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Error> {
    report("zero", lan_model_to_i64(&lan_model_from_i64(0)?)? == 0)?;
    report("maximum", lan_model_to_i64(&Nat::decimal("9223372036854775807")?)? == i64::MAX)?;
    report("maximum-roundtrip", lan_model_from_i64(i64::MAX)? == Nat::decimal("9223372036854775807")?)?;
    report("overflow", matches!(lan_model_to_i64(&Nat::decimal("9223372036854775808")?), Err(Error::ModelRange)))?;
    report("large-overflow", matches!(lan_model_to_i64(&Nat::decimal("340282366920938463463374607431768211455")?), Err(Error::ModelRange)))?;
    report("negative", matches!(lan_model_from_i64(-1), Err(Error::ModelRange)))?;
    let mut db = toasty::Db::builder()
        .models(toasty::models!(LanModel436f756e746572, LanModel53696e676c65, LanModel466c6167))
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
    let true_row = Arc::new(f_666c6167(nat("31")?, nat("1")?)?);
    let made = assert_send(f_637265617465466c6167(Arc::clone(&true_row), Arc::clone(&db))).await?;
    report("bool-create-true", is_true(&made.f0) && !is_true(&made.f3)
        && lan_model_to_i64(&made.f1)? == 31 && lan_model_to_i64(&made.f2)? == 1)?;
    let made = assert_send(f_637265617465466c616756616c7565(nat("30")?, nat("0")?, Arc::clone(&db))).await?;
    report("bool-create-false", !is_true(&made.f0) && is_true(&made.f3)
        && lan_model_to_i64(&made.f1)? == 30 && lan_model_to_i64(&made.f2)? == 0)?;
    let stored = LanModel466c6167::get_by_id(&mut direct, &31_i64).await?;
    report("bool-stored-true", stored.f_656e61626c6564 && !stored.f_6172636869766564
        && stored.id == 31 && stored.f_636f756e74 == 1)?;
    let stored = LanModel466c6167::get_by_id(&mut direct, &30_i64).await?;
    report("bool-stored-false", !stored.f_656e61626c6564 && stored.f_6172636869766564
        && stored.id == 30 && stored.f_636f756e74 == 0)?;
    let found = assert_send(f_6c6f6f6b7570466c6167(nat("31")?, Arc::clone(&db))).await?;
    report("bool-lookup-true", is_true(&found.f0) && !is_true(&found.f3)
        && lan_model_to_i64(&found.f1)? == 31 && lan_model_to_i64(&found.f2)? == 1)?;
    let found = assert_send(f_6c6f6f6b7570466c6167(nat("30")?, Arc::clone(&db))).await?;
    report("bool-lookup-false", !is_true(&found.f0) && is_true(&found.f3)
        && lan_model_to_i64(&found.f1)? == 30 && lan_model_to_i64(&found.f2)? == 0)?;
    report("bool-shared", Arc::strong_count(&true_row) == 1)?;
    report("bool-duplicate", matches!(f_637265617465466c6167(true_row, Arc::clone(&db)).await, Err(Error::Database(_))))?;
    report("bool-overflow", matches!(f_637265617465466c616756616c7565(nat("32")?, nat("9223372036854775808")?, Arc::clone(&db)).await, Err(Error::ModelRange)))?;
    report("bool-overflow-no-insert", matches!(f_6c6f6f6b7570466c6167(nat("32")?, Arc::clone(&db)).await, Err(Error::Database(_))))?;
    report("database-sharing", Arc::strong_count(&db) == 1)?;
    Ok(())
}
