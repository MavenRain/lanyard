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
    struct Connection { models: Vec<&'static str>, url: String }
    static TRACE: std::sync::Mutex<Vec<Connection>> = std::sync::Mutex::new(Vec::new());
    pub fn trace_ends_with(expected: &[(&[&str], &str)]) -> Result<bool, Error> {
        TRACE.lock().map_err(|_error| Error).map(|trace| {
            trace.len() >= expected.len() && trace.iter().rev().zip(expected.iter().rev())
                .all(|(connection, (models, url))| connection.models == *models && connection.url == *url)
        })
    }
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
            TRACE.lock().map_err(|_error| Error)?
                .push(Connection { models: self.models.clone(), url: url.to_owned() });
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
    let inline = execute(f_696e6c696e65(text_input("inline")))??;
    report("inline", inline.registered() == ["LanModel436f756e746572", "LanModel4175646974"]
        && inline.url() == "inline")?;
    let before = toasty::counts();
    let first = text_input("first");
    let second = text_input("second");
    let twice = f_7477696365(Arc::clone(&first), Arc::clone(&second));
    report("inline-lazy", toasty::counts() == before)?;
    let twice = execute(twice)??;
    report("inline-distinct", twice.registered() == ["LanModel4175646974"] && twice.url() == "second"
        && toasty::counts() == (before.0 + 2, before.1 + 2, before.2 + 1))?;
    report("inline-order", toasty::trace_ends_with(&[
        (&["LanModel436f756e746572"], "first"), (&["LanModel4175646974"], "second")])?)?;
    report("inline-sharing", Arc::strong_count(&first) == 1 && Arc::strong_count(&second) == 1)?;
    let before = toasty::counts();
    report("inline-first-error", matches!(execute(f_7477696365(text_input("fail"), text_input("unused")))?,
        Err(Error::Database(_))) && toasty::counts() == (before.0 + 1, before.1 + 1, before.2))?;
    let before = toasty::counts();
    report("inline-second-error", matches!(execute(f_7477696365(text_input("first"), text_input("fail")))?,
        Err(Error::Database(_))) && toasty::counts() == (before.0 + 2, before.1 + 2, before.2 + 1))?;
    let before = toasty::counts();
    report("inline-invalid-first", matches!(execute(f_7477696365(byte_input(&[256])?, text_input("unused")))?,
        Err(Error::ModelByteRange)) && toasty::counts() == before)?;
    report("inline-invalid-second", matches!(execute(f_7477696365(text_input("first"), byte_input(&[255])?))?,
        Err(Error::ModelUtf8)) && toasty::counts() == (before.0 + 1, before.1 + 1, before.2 + 1))?;
    let before = toasty::counts();
    let left = execute(f_63686f6f7365(Arc::new(T73756d28756e69742c756e697429::V0(())), text_input("left")))??;
    let right = execute(f_63686f6f7365(Arc::new(T73756d28756e69742c756e697429::V1(())), text_input("right")))??;
    report("inline-branches", left.registered() == ["LanModel436f756e746572"] && left.url() == "left"
        && right.registered() == ["LanModel4175646974"] && right.url() == "right"
        && toasty::counts() == (before.0 + 2, before.1 + 2, before.2))?;
    let before = toasty::counts();
    {
        let mut canceled = std::pin::pin!(f_7477696365(text_input("first"), text_input("second")));
        report("inline-first-suspension", matches!(canceled.as_mut().poll(&mut context), std::task::Poll::Pending)
            && toasty::counts() == (before.0 + 1, before.1, before.2))?;
        report("inline-second-suspension", matches!(canceled.as_mut().poll(&mut context), std::task::Poll::Pending)
            && toasty::counts() == (before.0 + 2, before.1 + 1, before.2 + 1))?;
    }
    report("inline-cancellation", toasty::counts() == (before.0 + 2, before.1 + 1, before.2 + 1))?;
    Ok(())
}
