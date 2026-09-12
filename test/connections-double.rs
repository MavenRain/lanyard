use std::future::Future;
#[macro_export]
macro_rules! models { ($($model:ident),*) => { vec![$(stringify!($model)),*] }; }
#[macro_export]
macro_rules! create {
    ($model:ident { $($field:ident: $value:expr),* }) => {
        toasty::Pending::new($model { $($field: $value),* })
    };
}
mod toasty {
    pub use model_derive::Model;
    pub use crate::{create, models};
    use std::sync::atomic::{AtomicUsize, Ordering};
    static STARTS: AtomicUsize = AtomicUsize::new(0);
    static FINISHES: AtomicUsize = AtomicUsize::new(0);
    static PUSHES: AtomicUsize = AtomicUsize::new(0);
    pub fn counts() -> (usize, usize, usize) {
        (STARTS.load(Ordering::SeqCst), FINISHES.load(Ordering::SeqCst), PUSHES.load(Ordering::SeqCst))
    }
    #[derive(Clone)]
    pub struct Db { models: Vec<&'static str>, url: String }
    impl Db {
        pub fn builder() -> Builder { Builder { models: Vec::new() } }
        pub fn registered(&self) -> &[&'static str] { &self.models }
        pub fn url(&self) -> &str { &self.url }
        pub async fn push_schema(&self) -> Result<(), Error> {
            PUSHES.fetch_add(1, Ordering::SeqCst); Ok(())
        }
    }
    pub struct Builder { models: Vec<&'static str> }
    impl Builder {
        pub fn models(&mut self, models: Vec<&'static str>) -> &mut Self { self.models = models; self }
        pub async fn connect(&mut self, url: &str) -> Result<Db, Error> {
            enum Step { Start, Finish }
            STARTS.fetch_add(1, Ordering::SeqCst);
            let mut step = Step::Start;
            std::future::poll_fn(move |cx| match step {
                Step::Start => { step = Step::Finish; cx.waker().wake_by_ref(); std::task::Poll::Pending }
                Step::Finish => std::task::Poll::Ready(()),
            }).await;
            FINISHES.fetch_add(1, Ordering::SeqCst);
            if url == "fail" { Err(Error) }
            else { Ok(Db { models: self.models.clone(), url: url.to_owned() }) }
        }
    }
    #[derive(Debug)]
    pub struct Error;
    impl std::fmt::Display for Error {
        fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { f.write_str("connection failed") }
    }
    impl std::error::Error for Error {}
    pub struct Pending<T>(T);
    impl<T> Pending<T> {
        pub fn new(value: T) -> Self { Self(value) }
        pub async fn exec(self, _db: &mut Db) -> Result<T, Error> { Ok(self.0) }
    }
}
impl LanModel436f756e746572 {
    async fn get_by_id(_db: &mut toasty::Db, id: &i64) -> Result<Self, toasty::Error> {
        Ok(Self { id: *id, f_76616c7565: 42 })
    }
}
struct Wake;
impl std::task::Wake for Wake { fn wake(self: Arc<Self>) {} }
fn execute<F: Future + Send>(future: F) -> Result<F::Output, Error> {
    let mut future = std::pin::pin!(future);
    let waker = std::task::Waker::from(Arc::new(Wake));
    let mut context = std::task::Context::from_waker(&waker);
    (0..8).find_map(|_poll| match future.as_mut().poll(&mut context) {
        std::task::Poll::Ready(value) => Some(value),
        std::task::Poll::Pending => None,
    }).ok_or_else(|| {
        eprintln!("poll-budget FAIL: future still pending after 8 polls");
        Error::Arithmetic
    })
}
fn report(name: &str, passed: bool) -> Result<(), Error> {
    if passed { println!("{name} OK"); Ok(()) }
    else { eprintln!("{name} FAIL"); Err(Error::Arithmetic) }
}
fn main() -> Result<(), Error> {
    let url = text_input("sqlite::memory:");
    let future = f_636f6e6e656374(Arc::clone(&url));
    report("lazy", toasty::counts() == (0, 0, 0))?;
    let mut future = std::pin::pin!(future);
    let waker = std::task::Waker::from(Arc::new(Wake));
    let mut context = std::task::Context::from_waker(&waker);
    report("suspension", matches!(future.as_mut().poll(&mut context), std::task::Poll::Pending)
        && toasty::counts() == (1, 0, 0))?;
    let db = execute(future)??;
    report("completion", toasty::counts() == (1, 1, 0))?;
    report("models", db.registered() == ["LanModel436f756e746572", "LanModel4175646974"])?;
    report("url", db.url() == "sqlite::memory:")?;
    report("shared-url", text_is(&url, "sqlite::memory:"))?;
    let single = execute(f_73696e676c65(text_input("one")))??;
    report("single-model", single.registered() == ["LanModel436f756e746572"] && single.url() == "one")?;
    let unicode = execute(f_6f70656e(text_input("héllo🦀\0")))??;
    report("unicode-zero", unicode.url() == "héllo🦀\0")?;
    report("empty", execute(f_6f70656e(text_input("")))??.url().is_empty())?;
    report("database-error", matches!(execute(f_636f6e6e656374(text_input("fail")))?, Err(Error::Database(_))))?;
    let before = toasty::counts();
    report("byte-range", matches!(execute(f_6f70656e(byte_input(&[256])?))?, Err(Error::ModelByteRange)))?;
    report("large-byte", matches!(execute(f_6f70656e(byte_input(&[65535])?))?, Err(Error::ModelByteRange)))?;
    report("utf8", matches!(execute(f_6f70656e(byte_input(&[255])?))?, Err(Error::ModelUtf8)))?;
    report("invalid-no-connect", toasty::counts() == before)?;
    let row = execute(f_72756e(text_input("sqlite::memory:")))??;
    report("program", lan_model_to_i64(&row.f0)? == 7 && lan_model_to_i64(&row.f1)? == 42)?;
    report("schema-effect", toasty::counts().2 == before.2 + 1)?;
    report("caller-error", matches!(execute(f_72756e(text_input("fail")))?, Err(Error::Database(_))))?;
    report("error-no-schema", toasty::counts().2 == before.2 + 1)?;
    let before = toasty::counts();
    {
        let mut canceled = std::pin::pin!(f_6f70656e(text_input("cancel")));
        report("cancel-pending", matches!(canceled.as_mut().poll(&mut context), std::task::Poll::Pending)
            && toasty::counts() == (before.0 + 1, before.1, before.2))?;
    }
    report("canceled", toasty::counts() == (before.0 + 1, before.1, before.2))?;
    Ok(())
}
