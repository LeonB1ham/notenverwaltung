"""CSV export helpers for GradeBook (GRASP Pure Fabrication)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

from notenverwaltung.exceptions import PersistenceError

if TYPE_CHECKING:
    from notenverwaltung.gradebook import GradeBook


def export_students_csv(gradebook: GradeBook, path: Path | str) -> None:
    file_path = Path(path)
    try:
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["student_id", "first_name", "last_name", "email"])
            for student in gradebook.list_students():
                writer.writerow(
                    [
                        student.student_id,
                        student.first_name,
                        student.last_name,
                        student.email,
                    ]
                )
    except OSError as exc:
        raise PersistenceError(
            f"Failed to export students to {file_path}: {exc}"
        ) from exc


def export_courses_csv(gradebook: GradeBook, path: Path | str) -> None:
    file_path = Path(path)
    try:
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["course_id", "name", "max_grade", "passing_grade"])
            for course in gradebook.list_courses():
                writer.writerow(
                    [
                        course.course_id,
                        course.name,
                        course.max_grade,
                        course.passing_grade,
                    ]
                )
    except OSError as exc:
        raise PersistenceError(
            f"Failed to export courses to {file_path}: {exc}"
        ) from exc


def export_grades_csv(gradebook: GradeBook, path: Path | str) -> None:
    file_path = Path(path)
    try:
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["student_id", "course_id", "score", "date", "notes"])
            for grade in gradebook.list_grades():
                writer.writerow(
                    [
                        grade.student.student_id,
                        grade.course.course_id,
                        grade.score,
                        grade.date,
                        grade.notes,
                    ]
                )
    except OSError as exc:
        raise PersistenceError(
            f"Failed to export grades to {file_path}: {exc}"
        ) from exc
