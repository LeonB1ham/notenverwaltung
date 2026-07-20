"""Application bootstrap: paths, sample data, GradeBook factory."""

from __future__ import annotations

from pathlib import Path

from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.course import Course
from notenverwaltung.models.student import Student
from notenverwaltung.storage.sqlite_store import SqliteGradeStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "grades.db"
EXPORT_DIR = PROJECT_ROOT / "exports"


def seed_sample_data(gradebook: GradeBook) -> None:
    gradebook.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gradebook.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gradebook.add_course(Course("CS101", "Intro to Programming"))
    gradebook.add_course(Course("CS102", "Data Structures"))
    gradebook.record_grade("S001", "CS101", 85, "2026-01-15")
    gradebook.record_grade("S001", "CS102", 92, "2026-01-20")
    gradebook.record_grade("S002", "CS101", 45, "2026-01-15")


def create_gradebook(db_path: Path | str | None = None) -> GradeBook:
    path = Path(db_path) if db_path is not None else DB_PATH
    store = SqliteGradeStore(str(path))
    gradebook = GradeBook(_store=store)
    if not gradebook.list_students() and not gradebook.list_courses():
        seed_sample_data(gradebook)
    return gradebook
