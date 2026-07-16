import json

import pytest

from notenverwaltung.models.course import Course
from notenverwaltung.exceptions import PersistenceError
from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.student import Student


@pytest.fixture
def sample_gradebook() -> GradeBook:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))
    gb.add_course(Course("CS102", "Data Structures"))
    gb.record_grade("S001", "CS101", 85, "2026-01-15", "solid work")
    gb.record_grade("S001", "CS102", 92, "2026-01-20")
    gb.record_grade("S002", "CS101", 45, "2026-01-15")
    return gb


def test_to_dict_contains_all_entities(sample_gradebook: GradeBook) -> None:
    data = sample_gradebook.to_dict()
    assert len(data["students"]) == 2
    assert len(data["courses"]) == 2
    assert len(data["grades"]) == 3
    assert data["grades"][0]["date"] == "2026-01-15"
    assert data["grades"][0]["notes"] == "solid work"


def test_from_dict_rebuilds_gradebook(sample_gradebook: GradeBook) -> None:
    restored = GradeBook.from_dict(sample_gradebook.to_dict())
    assert len(restored.students) == 2
    assert len(restored.courses) == 2
    assert len(restored.grades) == 3
    assert restored.student_average("S001") == pytest.approx(88.5)


def test_json_round_trip(tmp_path, sample_gradebook: GradeBook) -> None:
    file_path = tmp_path / "gradebook.json"
    sample_gradebook.save_json(file_path)

    loaded = GradeBook.load_json(file_path)
    assert loaded.to_dict() == sample_gradebook.to_dict()


def test_load_json_missing_file_raises(tmp_path) -> None:
    with pytest.raises(PersistenceError, match="file not found"):
        GradeBook.load_json(tmp_path / "missing.json")


def test_load_json_invalid_json_raises(tmp_path) -> None:
    file_path = tmp_path / "invalid.json"
    file_path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(PersistenceError, match="Invalid JSON"):
        GradeBook.load_json(file_path)


def test_export_grades_csv(tmp_path, sample_gradebook: GradeBook) -> None:
    file_path = tmp_path / "grades.csv"
    sample_gradebook.export_grades_csv(file_path)

    content = file_path.read_text(encoding="utf-8")
    assert "student_id,course_id,score,date,notes" in content
    assert "S001,CS101,85,2026-01-15,solid work" in content


def test_export_students_and_courses_csv(tmp_path, sample_gradebook: GradeBook) -> None:
    students_path = tmp_path / "students.csv"
    courses_path = tmp_path / "courses.csv"
    sample_gradebook.export_students_csv(students_path)
    sample_gradebook.export_courses_csv(courses_path)

    students = students_path.read_text(encoding="utf-8")
    courses = courses_path.read_text(encoding="utf-8")
    assert "student_id,first_name,last_name,email" in students
    assert "S001,Anna,Schmidt,anna@example.com" in students
    assert "course_id,name,max_grade,passing_grade" in courses
    assert "CS101,Intro to Programming,100.0,50.0" in courses


def test_csv_round_trip(tmp_path, sample_gradebook: GradeBook) -> None:
    csv_path = tmp_path / "grades.csv"
    sample_gradebook.export_grades_csv(csv_path)

    target = GradeBook()
    target.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    target.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    target.add_course(Course("CS101", "Intro to Programming"))
    target.add_course(Course("CS102", "Data Structures"))

    report = target.import_grades_csv(csv_path)
    assert report.imported == 3
    assert report.skipped == 0
    assert report.errors == []
    assert target.student_average("S001") == pytest.approx(88.5)


def test_import_grades_csv_skips_invalid_lines(tmp_path) -> None:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))

    csv_path = tmp_path / "grades.csv"
    csv_path.write_text(
        "\n".join(
            [
                "student_id,course_id,score,date",
                "S001,CS101,85,2026-01-15",
                "bad-line",
                "S001,CS101,150,2026-01-16",
                "S999,CS101,80,2026-01-17",
                "S001,CS999,80,2026-01-18",
                "S001,CS101,70,not-a-date",
            ]
        ),
        encoding="utf-8",
    )

    report = gb.import_grades_csv(csv_path)
    assert report.imported == 1
    assert report.skipped == 5
    assert len(report.errors) == 5
    assert len(gb.grades) == 1


def test_import_grades_csv_skips_duplicates(tmp_path) -> None:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))
    gb.record_grade("S001", "CS101", 85, "2026-01-15", "ok")

    csv_path = tmp_path / "grades.csv"
    csv_path.write_text(
        "\n".join(
            [
                "student_id,course_id,score,date,notes",
                "S001,CS101,85,2026-01-15,ok",
                "S001,CS101,85,2026-01-15,ok",
                "S001,CS101,90,2026-01-20,",
            ]
        ),
        encoding="utf-8",
    )

    report = gb.import_grades_csv(csv_path)
    assert report.imported == 1
    assert report.skipped == 2
    assert any("duplicate" in error for error in report.errors)
    assert len(gb.grades) == 2


def test_import_students_and_courses_csv(tmp_path) -> None:
    gb = GradeBook()
    students_path = tmp_path / "students.csv"
    courses_path = tmp_path / "courses.csv"
    students_path.write_text(
        "\n".join(
            [
                "student_id,first_name,last_name,email",
                "S001,Anna,Schmidt,anna@example.com",
                "S001,Anna,Schmidt,anna@example.com",
                "S002,Ben,Mueller,ben@example.com",
                "bad-line",
            ]
        ),
        encoding="utf-8",
    )
    courses_path.write_text(
        "\n".join(
            [
                "course_id,name,max_grade,passing_grade",
                "CS101,Intro to Programming,100,50",
                "CS101,Intro to Programming,100,50",
                "CS102,Data Structures",
            ]
        ),
        encoding="utf-8",
    )

    students_report = gb.import_students_csv(students_path)
    courses_report = gb.import_courses_csv(courses_path)

    assert students_report.imported == 2
    assert students_report.skipped == 2
    assert courses_report.imported == 2
    assert courses_report.skipped == 1
    assert len(gb.students) == 2
    assert len(gb.courses) == 2
    assert gb.courses["CS102"].max_grade == 100.0


def test_import_grades_csv_missing_file_raises(tmp_path) -> None:
    gb = GradeBook()
    with pytest.raises(PersistenceError, match="Failed to read grades"):
        gb.import_grades_csv(tmp_path / "missing.csv")


def test_save_json_write_error_raises(
    monkeypatch: pytest.MonkeyPatch, sample_gradebook: GradeBook
) -> None:
    def raise_os_error(*_args, **_kwargs) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("pathlib.Path.write_text", raise_os_error)
    with pytest.raises(PersistenceError, match="Failed to save grade book"):
        sample_gradebook.save_json("gradebook.json")
