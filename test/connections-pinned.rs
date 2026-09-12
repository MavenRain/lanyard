include!("golden.rs");
include!("text-oracle.rs");

fn assert_send<F: std::future::Future + Send>(future: F) -> F { future }
fn report(name: &str, passed: bool) -> Result<(), Error> {
    if passed { println!("{name} OK"); Ok(()) }
    else { eprintln!("{name} FAIL"); Err(Error::Arithmetic) }
}
#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Error> {
    let url = text_input("sqlite::memory:");
    let db = Arc::new(assert_send(f_636f6e6e656374(Arc::clone(&url))).await?);
    assert_send(f_696e697469616c697a65(Arc::clone(&db))).await?;
    let created = assert_send(f_637265617465(Arc::clone(&db))).await?;
    report("create", lan_model_to_i64(&created.f0)? == 7 && lan_model_to_i64(&created.f1)? == 42)?;
    let found = assert_send(f_6c6f6f6b7570(Arc::clone(&db))).await?;
    report("lookup", found == created)?;
    let audit = assert_send(f_6175646974(Arc::clone(&db))).await?;
    report("second-model", lan_model_to_i64(&audit.f0)? == 99 && lan_model_to_i64(&audit.f1)? == 8)?;
    let mut direct = (*db).clone();
    let stored = LanModel4175646974::get_by_id(&mut direct, &8_i64).await?;
    report("stored-model", stored.id == 8 && stored.f_76616c7565 == 99)?;
    report("duplicate", matches!(f_637265617465(Arc::clone(&db)).await, Err(Error::Database(_))))?;
    let single = Arc::new(assert_send(f_73696e676c65(Arc::clone(&url))).await?);
    assert_send(f_696e697469616c697a65(Arc::clone(&single))).await?;
    report("single-model", f_637265617465(single).await? == created)?;
    report("whole-program", assert_send(f_72756e(Arc::clone(&url))).await? == created)?;
    report("independent-connections", assert_send(f_72756e(Arc::clone(&url))).await? == created)?;
    report("shared-url", Arc::strong_count(&url) == 1 && text_is(&url, "sqlite::memory:"))?;
    report("invalid-scheme", matches!(assert_send(f_636f6e6e656374(text_input("unknown:lanyard"))).await, Err(Error::Database(_))))?;
    report("caller-error", matches!(assert_send(f_72756e(text_input("unknown:lanyard"))).await, Err(Error::Database(_))))?;
    report("byte-range", matches!(f_6f70656e(byte_input(&[256])?).await, Err(Error::ModelByteRange)))?;
    report("utf8", matches!(f_6f70656e(byte_input(&[255])?).await, Err(Error::ModelUtf8)))?;
    report("database-sharing", Arc::strong_count(&db) == 1)?;
    Ok(())
}
