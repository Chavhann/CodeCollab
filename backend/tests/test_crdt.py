from app.crdt import CRDTDocument


def test_insert():
    document = CRDTDocument("Hello")

    result = document.apply_insert(
        position=5,
        text=" World",
        operation_id="op-1",
    )

    assert result.content == "Hello World"
    assert result.revision == 1


def test_delete():
    document = CRDTDocument("Hello World")

    result = document.apply_delete(
        position=5,
        length=6,
        operation_id="op-1",
    )

    assert result.content == "Hello"
    assert result.revision == 1


def test_duplicate_operation_is_ignored():
    document = CRDTDocument("Hello")

    first = document.apply_insert(
        position=5,
        text="!",
        operation_id="op-1",
    )

    second = document.apply_insert(
        position=5,
        text="!",
        operation_id="op-1",
    )

    assert first.content == "Hello!"
    assert second.content == "Hello!"
    assert second.revision == 1


def test_revision_increments():
    document = CRDTDocument()

    document.apply_insert(
        position=0,
        text="A",
        operation_id="op-1",
    )

    document.apply_insert(
        position=1,
        text="B",
        operation_id="op-2",
    )

    document.apply_delete(
        position=0,
        length=1,
        operation_id="op-3",
    )

    assert document.content == "B"
    assert document.revision == 3


def test_snapshot():
    document = CRDTDocument("CodeCollab")

    snapshot = document.snapshot()

    assert snapshot.content == "CodeCollab"
    assert snapshot.revision == 0
