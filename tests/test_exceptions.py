from notenverwaltung.exceptions import (
    CourseNotFoundError,
    DuplicateEntryError,
    NotenverwaltungError,
    PersistenceError,
    StudentNotFoundError,
)


def test_exception_hierarchy() -> None:
    assert issubclass(StudentNotFoundError, NotenverwaltungError)
    assert issubclass(CourseNotFoundError, NotenverwaltungError)
    assert issubclass(DuplicateEntryError, NotenverwaltungError)
    assert issubclass(PersistenceError, NotenverwaltungError)
