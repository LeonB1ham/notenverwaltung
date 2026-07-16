import pytest

from notenverwaltung.models.course import Course
from notenverwaltung.exceptions import (
    CourseNotFoundError,
    DuplicateEntryError,
    StudentNotFoundError,
)
from notenverwaltung.gradebook import GradeBook
from notenverwaltung.storage import GradeStore, InMemoryGradeStore, SqliteGradeStore
from notenverwaltung.models.student import Student


def populate_gradebook(gradebook: GradeBook) -> None:
    gradebook.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gradebook.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gradebook.add_course(Course("CS101", "Intro to Programming"))
    gradebook.add_course(Course("CS102", "Data Structures"))
    gradebook.record_grade("S001", "CS101", 85, "2026-01-15")
    gradebook.record_grade("S001", "CS102", 92, "2026-01-20")
    gradebook.record_grade("S002", "CS101", 45, "2026-01-15")


@pytest.fixture(params=["memory", "sqlite"])
def grade_store(request) -> GradeStore:
    if request.param == "memory":
        return InMemoryGradeStore()
    return SqliteGradeStore(":memory:")


@pytest.fixture
def populated_gradebook(grade_store: GradeStore) -> GradeBook:
    gradebook = GradeBook(_store=grade_store)
    populate_gradebook(gradebook)
    return gradebook


def test_store_add_and_get_student(grade_store: GradeStore) -> None:
    student = Student("S001", "Anna", "Schmidt", "anna@example.com")
    grade_store.add_student(student)
    assert grade_store.get_student("S001") == student


def test_store_duplicate_student_raises(grade_store: GradeStore) -> None:
    student = Student("S001", "Anna", "Schmidt", "anna@example.com")
    grade_store.add_student(student)
    with pytest.raises(DuplicateEntryError):
        grade_store.add_student(student)


def test_store_missing_student_raises(grade_store: GradeStore) -> None:
    with pytest.raises(StudentNotFoundError):
        grade_store.get_student("S001")


def test_store_record_and_list_grades(grade_store: GradeStore) -> None:
    from notenverwaltung.models.grade import Grade

    student = Student("S001", "Anna", "Schmidt", "anna@example.com")
    course = Course("CS101", "Intro to Programming")
    grade_store.add_student(student)
    grade_store.add_course(course)
    grade_store.record_grade(Grade(student, course, 85, "2026-01-15"))
    assert len(grade_store.list_grades()) == 1
    assert grade_store.get_student_grades("S001")[0].score == 85


def test_store_clear_all(grade_store: GradeStore) -> None:
    from notenverwaltung.models.grade import Grade

    student = Student("S001", "Anna", "Schmidt", "anna@example.com")
    course = Course("CS101", "Intro to Programming")
    grade_store.add_student(student)
    grade_store.add_course(course)
    grade_store.record_grade(Grade(student, course, 85, "2026-01-15"))

    grade_store.clear_all()
    assert grade_store.list_students() == []
    assert grade_store.list_courses() == []
    assert grade_store.list_grades() == []


def test_gradebook_with_sqlite_store_matches_memory() -> None:
    memory_book = GradeBook()
    sqlite_store = SqliteGradeStore(":memory:")
    sqlite_book = GradeBook(_store=sqlite_store)

    populate_gradebook(memory_book)
    populate_gradebook(sqlite_book)

    memory_data = memory_book.to_dict()
    sqlite_data = sqlite_book.to_dict()
    assert memory_data["students"] == sqlite_data["students"]
    assert memory_data["courses"] == sqlite_data["courses"]
    assert len(memory_data["grades"]) == len(sqlite_data["grades"])
    assert memory_book.student_average("S001") == pytest.approx(
        sqlite_book.student_average("S001")
    )
    assert memory_book.course_pass_rate("CS101") == pytest.approx(
        sqlite_book.course_pass_rate("CS101")
    )


def test_sqlite_json_round_trip(tmp_path) -> None:
    store = SqliteGradeStore(":memory:")
    gradebook = GradeBook(_store=store)
    populate_gradebook(gradebook)

    file_path = tmp_path / "gradebook.json"
    gradebook.save_json(file_path)

    restored = GradeBook.load_json(file_path, store=SqliteGradeStore(":memory:"))
    assert restored.to_dict() == gradebook.to_dict()


def test_sql_statistics_match_python(populated_gradebook: GradeBook) -> None:
    store = populated_gradebook.store
    if not isinstance(store, SqliteGradeStore):
        pytest.skip("SQL comparison only applies to SQLite store")

    database = store.database
    assert database.student_average_sql("S001") == pytest.approx(
        populated_gradebook.student_average("S001")
    )
    assert database.course_average_sql("CS101") == pytest.approx(
        populated_gradebook.course_average("CS101")
    )
    assert database.course_pass_rate_sql("CS101") == pytest.approx(
        populated_gradebook.course_pass_rate("CS101")
    )


def test_sqlite_store_missing_course_raises() -> None:
    store = SqliteGradeStore(":memory:")
    with pytest.raises(CourseNotFoundError):
        store.get_course("CS101")
