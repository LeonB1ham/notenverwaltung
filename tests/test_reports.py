import pytest

from notenverwaltung import (
    Course,
    CsvReportGenerator,
    Grade,
    GradeBook,
    Student,
    TextReportGenerator,
)
from notenverwaltung.models import Course as ModelCourse
from notenverwaltung.reports import ReportGenerator


@pytest.fixture
def sample_gradebook() -> GradeBook:
    gb = GradeBook()
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gb.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gb.add_course(Course("CS101", "Intro to Programming"))
    gb.add_course(Course("CS102", "Data Structures"))
    gb.record_grade("S001", "CS101", 85, "2026-01-15", "solid work")
    gb.record_grade("S001", "CS102", 92, "2026-01-20")
    gb.record_grade("S002", "CS101", 45, "2026-01-15", "needs practice")
    return gb


def test_package_imports() -> None:
    assert issubclass(TextReportGenerator, ReportGenerator)
    assert issubclass(CsvReportGenerator, ReportGenerator)
    assert ModelCourse is Course
    assert Grade is not None


def test_text_student_report(sample_gradebook: GradeBook) -> None:
    report = TextReportGenerator().generate_student_report("S001", sample_gradebook)
    assert "Anna Schmidt" in report
    assert "Intro to Programming" in report
    assert "PASS" in report
    assert "solid work" in report
    assert "Overall Average: 88.5%" in report


def test_text_course_report(sample_gradebook: GradeBook) -> None:
    report = TextReportGenerator().generate_course_report("CS101", sample_gradebook)
    assert "Intro to Programming" in report
    assert "Class Average: 65.0" in report
    assert "Pass Rate: 50.0%" in report
    assert "needs practice" in report
    assert "Grade Distribution:" in report
    assert "  B: 1" in report
    assert "  F: 1" in report


def test_text_summary_report(sample_gradebook: GradeBook) -> None:
    report = TextReportGenerator().generate_summary_report(sample_gradebook)
    assert "Total Students: 2" in report
    assert "Top Students:" in report
    assert "Anna Schmidt: 88.5%" in report
    assert "Students at Risk" in report
    assert "Ben Mueller: 45.0%" in report


def test_csv_student_report(sample_gradebook: GradeBook) -> None:
    report = CsvReportGenerator().generate_student_report("S001", sample_gradebook)
    assert "student_id,student_name,email" in report
    assert "S001,Anna Schmidt,anna@example.com" in report
    assert "notes" in report.splitlines()[3]
    assert "solid work" in report
    assert "overall_average,88.5" in report


def test_csv_course_report(sample_gradebook: GradeBook) -> None:
    report = CsvReportGenerator().generate_course_report("CS101", sample_gradebook)
    assert "course_id,course_name" in report
    assert "CS101,Intro to Programming" in report
    assert "needs practice" in report
    assert "pass_rate,50.0" in report
    assert "letter_grade,count" in report


def test_csv_summary_report(sample_gradebook: GradeBook) -> None:
    report = CsvReportGenerator().generate_summary_report(sample_gradebook)
    assert "metric,value" in report
    assert "total_students,2" in report
    assert "top_student,average" in report
    assert "at_risk_student,average" in report
