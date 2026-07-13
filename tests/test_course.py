import pytest

from notenverwaltung.course import Course


@pytest.fixture
def sample_course() -> Course:
    return Course("CS101", "Intro to Programming")


def test_course_creation_defaults(sample_course: Course) -> None:
    assert sample_course.course_id == "CS101"
    assert sample_course.name == "Intro to Programming"
    assert sample_course.max_grade == 100.0
    assert sample_course.passing_grade == 50.0


def test_course_custom_grades() -> None:
    course = Course("MATH201", "Calculus", max_grade=20.0, passing_grade=10.0)
    assert course.max_grade == 20.0
    assert course.passing_grade == 10.0


def test_str_representation(sample_course: Course) -> None:
    assert str(sample_course) == "Intro to Programming (CS101)"


@pytest.mark.parametrize(
    ("max_grade", "passing_grade"),
    [
        (0, 50),
        (-10, 5),
        (100, 0),
        (100, 101),
        (100, -5),
    ],
)
def test_course_validation_raises(max_grade: float, passing_grade: float) -> None:
    with pytest.raises(ValueError):
        Course("CS101", "Intro", max_grade=max_grade, passing_grade=passing_grade)
