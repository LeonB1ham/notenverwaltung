import pytest

from notenverwaltung.course import Course
from notenverwaltung.grade import Grade
from notenverwaltung.student import Student


@pytest.fixture
def student() -> Student:
    return Student("S001", "Anna", "Schmidt", "anna@example.com")


@pytest.fixture
def course() -> Course:
    return Course("CS101", "Intro to Programming")


@pytest.fixture
def grade(student: Student, course: Course) -> Grade:
    return Grade(student, course, 85.0, "2026-01-15")


def test_grade_creation(grade: Grade) -> None:
    assert grade.score == 85.0
    assert grade.date == "2026-01-15"
    assert grade.notes == ""


def test_is_passing(grade: Grade) -> None:
    assert grade.is_passing is True


def test_is_failing(student: Student, course: Course) -> None:
    failing = Grade(student, course, 45.0, "2026-01-15")
    assert failing.is_passing is False


def test_percentage(grade: Grade) -> None:
    assert grade.percentage == pytest.approx(85.0)


def test_percentage_custom_max_grade(student: Student) -> None:
    course = Course("MATH201", "Calculus", max_grade=20.0, passing_grade=10.0)
    grade = Grade(student, course, 18.0, "2026-01-15")
    assert grade.percentage == pytest.approx(90.0)


@pytest.mark.parametrize(
    ("score", "expected_letter"),
    [
        (90, "A"),
        (89.9, "B"),
        (80, "B"),
        (79.9, "C"),
        (70, "C"),
        (69.9, "D"),
        (60, "D"),
        (59.9, "F"),
        (0, "F"),
    ],
)
def test_letter_grade_boundaries(
    student: Student, course: Course, score: float, expected_letter: str
) -> None:
    grade = Grade(student, course, score, "2026-01-15")
    assert grade.letter_grade == expected_letter


@pytest.mark.parametrize("score", [-1, 101, 150])
def test_grade_score_validation_raises(
    student: Student, course: Course, score: float
) -> None:
    with pytest.raises(ValueError):
        Grade(student, course, score, "2026-01-15")


def test_str_representation(grade: Grade) -> None:
    assert str(grade) == "Anna Schmidt - Intro to Programming: 85.0 (B) on 2026-01-15"
