"""JSON persistence helpers for GradeBook (GRASP Pure Fabrication)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from notenverwaltung.exceptions import PersistenceError
from notenverwaltung.models.course import Course
from notenverwaltung.models.student import Student
from notenverwaltung.storage.base import GradeStore

if TYPE_CHECKING:
    from notenverwaltung.gradebook import GradeBook


def to_dict(gradebook: GradeBook) -> dict:
    return {
        "students": [
            {
                "student_id": student.student_id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "email": student.email,
            }
            for student in gradebook.list_students()
        ],
        "courses": [
            {
                "course_id": course.course_id,
                "name": course.name,
                "max_grade": course.max_grade,
                "passing_grade": course.passing_grade,
            }
            for course in gradebook.list_courses()
        ],
        "grades": [
            {
                "student_id": grade.student.student_id,
                "course_id": grade.course.course_id,
                "score": float(grade.score),
                "date": grade.date,
                "notes": grade.notes,
            }
            for grade in gradebook.list_grades()
        ],
    }


def from_dict(data: dict, store: GradeStore | None = None) -> GradeBook:
    from notenverwaltung.gradebook import GradeBook

    gradebook = GradeBook(_store=store) if store is not None else GradeBook()

    for student_data in data.get("students", []):
        gradebook.add_student(Student(**student_data))

    for course_data in data.get("courses", []):
        gradebook.add_course(Course(**course_data))

    for grade_data in data.get("grades", []):
        gradebook.record_grade(
            grade_data["student_id"],
            grade_data["course_id"],
            grade_data["score"],
            grade_data["date"],
            grade_data.get("notes", ""),
        )

    return gradebook


def save_json(gradebook: GradeBook, path: Path | str) -> None:
    file_path = Path(path)
    try:
        file_path.write_text(
            json.dumps(to_dict(gradebook), indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise PersistenceError(
            f"Failed to save grade book to {file_path}: {exc}"
        ) from exc


def load_json(path: Path | str, store: GradeStore | None = None) -> GradeBook:
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PersistenceError(f"Grade book file not found: {file_path}") from exc
    except OSError as exc:
        raise PersistenceError(
            f"Failed to read grade book from {file_path}: {exc}"
        ) from exc

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise PersistenceError(f"Invalid JSON in {file_path}: {exc}") from exc

    return from_dict(data, store=store)
