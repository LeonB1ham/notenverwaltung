import pytest

from notenverwaltung.models.student import Student


@pytest.fixture
def sample_student() -> Student:
    return Student("S001", "Anna", "Schmidt", "anna@example.com")


def test_student_creation(sample_student: Student) -> None:
    assert sample_student.student_id == "S001"
    assert sample_student.first_name == "Anna"
    assert sample_student.last_name == "Schmidt"
    assert sample_student.email == "anna@example.com"


def test_full_name(sample_student: Student) -> None:
    assert sample_student.full_name == "Anna Schmidt"


def test_str_representation(sample_student: Student) -> None:
    assert str(sample_student) == "Anna Schmidt (S001, anna@example.com)"


@pytest.mark.parametrize(
    ("first_name", "last_name", "email"),
    [
        ("", "Schmidt", "anna@example.com"),
        ("Anna", "", "anna@example.com"),
        ("Anna", "Schmidt", "invalid-email"),
    ],
)
def test_student_validation_raises(
    first_name: str, last_name: str, email: str
) -> None:
    with pytest.raises(ValueError):
        Student("S001", first_name, last_name, email)
