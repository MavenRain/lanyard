type Bytes = T6e6f6d696e616c28353a427974657329;

fn text_input(value: &str) -> Arc<Bytes> {
    Arc::new(value.bytes().rev().fold(Bytes::V0, |tail, byte| {
        Bytes::V1(Box::new((Nat::canonical(vec![byte]), tail)))
    }))
}

fn byte_input(values: &[u16]) -> Result<Arc<Bytes>, Error> {
    values.iter().rev().try_fold(Bytes::V0, |tail, byte| {
        Nat::decimal(&byte.to_string()).map(|head| Bytes::V1(Box::new((head, tail))))
    }).map(Arc::new)
}

fn text_is(value: &Bytes, expected: &str) -> bool {
    std::iter::successors(Some(value), |node| match node {
        Bytes::V0 => None,
        Bytes::V1(fields) => Some(&fields.1),
    }).filter_map(|node| match node {
        Bytes::V0 => None,
        Bytes::V1(fields) => Some(fields.0.clone()),
    }).eq(expected.bytes().map(|byte| Nat::canonical(vec![byte])))
}
