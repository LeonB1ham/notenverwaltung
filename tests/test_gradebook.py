import pytest

from notenverwaltung.models.course import Course
from notenverwaltung.exceptions import (
    CourseNotFoundError,
    DuplicateEntryError,
    StudentNotFoundError,
)
from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.student import Student


@pytest.fixture
def sample_gradebook() -> GradeBook:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))
    gb.add_course(Course("CS102", "Data Structures"))
    gb.record_grade("S001", "CS101", 85, "2026-01-15")
    gb.record_grade("S001", "CS102", 92, "2026-01-20")
    gb.record_grade("S002", "CS101", 45, "2026-01-15")
    return gb


def test_add_student(sample_gradebook: GradeBook) -> None:
    student = Student("S003", "Clara", "Weber", "clara@example.com")
    sample_gradebook.add_student(student)
    assert sample_gradebook.students["S003"] == student


def test_add_duplicate_student_raises(sample_gradebook: GradeBook) -> None:
    duplicate = Student("S001", "Other", "Name", "other@example.com")
    with pytest.raises(DuplicateEntryError, match="already exists"):
        sample_gradebook.add_student(duplicate)


def test_add_course(sample_gradebook: GradeBook) -> None:
    course = Course("CS103", "Algorithms")
    sample_gradebook.add_course(course)
    assert sample_gradebook.courses["CS103"] == course


def test_add_duplicate_course_raises(sample_gradebook: GradeBook) -> None:
    duplicate = Course("CS101", "Duplicate Course")
    with pytest.raises(DuplicateEntryError, match="already exists"):
        sample_gradebook.add_course(duplicate)


def test_record_grade(sample_gradebook: GradeBook) -> None:
    grade = sample_gradebook.record_grade("S002", "CS102", 70, "2026-02-01", "good")
    assert grade.score == 70
    assert grade.notes == "good"
    assert len(sample_gradebook.grades) == 4


def test_record_grade_unknown_student_raises(sample_gradebook: GradeBook) -> None:
    with pytest.raises(StudentNotFoundError, match="Student S999 not found"):
        sample_gradebook.record_grade("S999", "CS101", 80, "2026-01-15")


def test_record_grade_unknown_course_raises(sample_gradebook: GradeBook) -> None:
    with pytest.raises(CourseNotFoundError, match="Course CS999 not found"):
        sample_gradebook.record_grade("S001", "CS999", 80, "2026-01-15")


def test_get_student_grades(sample_gradebook: GradeBook) -> None:
    grades = sample_gradebook.get_student_grades("S001")
    assert len(grades) == 2
    assert all(grade.student.student_id == "S001" for grade in grades)


def test_get_course_grades(sample_gradebook: GradeBook) -> None:
    grades = sample_gradebook.get_course_grades("CS101")
    assert len(grades) == 2
    assert all(grade.course.course_id == "CS101" for grade in grades)


def test_get_grades_returns_copy(sample_gradebook: GradeBook) -> None:
    grades = sample_gradebook.get_student_grades("S001")
    grades.clear()
    assert len(sample_gradebook.get_student_grades("S001")) == 2


def test_student_average(sample_gradebook: GradeBook) -> None:
    avg = sample_gradebook.student_average("S001")
    assert avg == pytest.approx(88.5)


def test_student_average_no_grades_raises() -> None:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    with pytest.raises(ValueError, match="No grades recorded"):
        gb.student_average("S001")


def test_course_average(sample_gradebook: GradeBook) -> None:
    avg = sample_gradebook.course_average("CS101")
    assert avg == pytest.approx(65.0)


def test_course_average_no_grades_raises() -> None:
    gb = GradeBook()
    gb.add_course(Course("CS101", "Intro to Programming"))
    with pytest.raises(ValueError, match="No grades recorded"):
        gb.course_average("CS101")


def test_course_pass_rate(sample_gradebook: GradeBook) -> None:
    rate = sample_gradebook.course_pass_rate("CS101")
    assert rate == pytest.approx(50.0)


def test_course_pass_rate_all_passing() -> None:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))
    gb.record_grade("S001", "CS101", 90, "2026-01-15")
    gb.record_grade("S001", "CS101", 80, "2026-01-20")
    assert gb.course_pass_rate("CS101") == pytest.approx(100.0)


def test_course_pass_rate_none_passing() -> None:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))
    gb.record_grade("S001", "CS101", 30, "2026-01-15")
    gb.record_grade("S002", "CS101", 20, "2026-01-15")
    assert gb.course_pass_rate("CS101") == pytest.approx(0.0)


def test_course_pass_rate_no_grades_raises() -> None:
    gb = GradeBook()
    gb.add_course(Course("CS101", "Intro to Programming"))
    with pytest.raises(ValueError, match="No grades recorded"):
        gb.course_pass_rate("CS101")


def test_top_students(sample_gradebook: GradeBook) -> None:
    top = sample_gradebook.top_students(n=2)
    assert len(top) == 2
    assert top[0][0].student_id == "S001"
    assert top[0][1] == pytest.approx(88.5)
    assert top[1][0].student_id == "S002"


def test_top_students_excludes_students_without_grades() -> None:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))
    gb.record_grade("S001", "CS101", 90, "2026-01-15")
    top = gb.top_students()
    assert len(top) == 1
    assert top[0][0].student_id == "S001"


def test_students_at_risk(sample_gradebook: GradeBook) -> None:
    at_risk = sample_gradebook.students_at_risk(threshold=60.0)
    assert len(at_risk) == 1
    assert at_risk[0].student_id == "S002"


def test_search_students_by_name(sample_gradebook: GradeBook) -> None:
    results = sample_gradebook.search_students("Schmidt")
    assert len(results) == 1
    assert results[0].student_id == "S001"


def test_search_students_by_email(sample_gradebook: GradeBook) -> None:
    results = sample_gradebook.search_students(r"ben@example\.com")
    assert len(results) == 1
    assert results[0].student_id == "S002"


def test_search_students_regex_pattern(sample_gradebook: GradeBook) -> None:
    results = sample_gradebook.search_students(r"^Anna")
    assert len(results) == 1
    assert results[0].first_name == "Anna"


def test_search_courses(sample_gradebook: GradeBook) -> None:
    results = sample_gradebook.search_courses("data")
    assert len(results) == 1
    assert results[0].course_id == "CS102"


def test_search_courses_regex_pattern(sample_gradebook: GradeBook) -> None:
    results = sample_gradebook.search_courses(r"Intro.*Programming")
    assert len(results) == 1
    assert results[0].course_id == "CS101"
