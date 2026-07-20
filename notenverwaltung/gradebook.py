import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from notenverwaltung.models.course import Course
from notenverwaltung.exceptions import (
    CourseNotFoundError,
    DuplicateEntryError,
    PersistenceError,
    StudentNotFoundError,
)
from notenverwaltung.models.grade import Grade
from notenverwaltung.storage.base import GradeStore
from notenverwaltung.storage.memory_store import InMemoryGradeStore
from notenverwaltung.models.student import Student
from notenverwaltung import csv_io

GRADE_CSV_LINE_PATTERN = re.compile(
    r"^(?P<student_id>[^,]+),(?P<course_id>[^,]+),"
    r"(?P<score>-?\d+(?:\.\d+)?),(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:,(?P<notes>.*))?$"
)

STUDENT_CSV_LINE_PATTERN = re.compile(
    r"^(?P<student_id>[^,]+),(?P<first_name>[^,]+),"
    r"(?P<last_name>[^,]+),(?P<email>[^,]+)$"
)

COURSE_CSV_LINE_PATTERN = re.compile(
    r"^(?P<course_id>[^,]+),(?P<name>[^,]+)"
    r"(?:,(?P<max_grade>\d+(?:\.\d+)?))?"
    r"(?:,(?P<passing_grade>\d+(?:\.\d+)?))?$"
)


@dataclass
class CsvImportReport:
    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class GradeBook:
    _store: GradeStore = field(default_factory=InMemoryGradeStore)

    @property
    def store(self) -> GradeStore:
        return self._store

    @property
    def students(self) -> dict[str, Student]:
        return {
            student.student_id: student for student in self._store.list_students()
        }

    @property
    def courses(self) -> dict[str, Course]:
        return {course.course_id: course for course in self._store.list_courses()}

    @property
    def grades(self) -> list[Grade]:
        return self._store.list_grades()

    def list_students(self) -> list[Student]:
        return self._store.list_students()

    def get_student(self, student_id: str) -> Student:
        return self._store.get_student(student_id)

    def add_student(self, student: Student) -> None:
        self._store.add_student(student)

    def update_student(self, student: Student) -> None:
        self._store.update_student(student)

    def list_courses(self) -> list[Course]:
        return self._store.list_courses()

    def get_course(self, course_id: str) -> Course:
        return self._store.get_course(course_id)

    def add_course(self, course: Course) -> None:
        self._store.add_course(course)

    def update_course(self, course: Course) -> None:
        self._store.update_course(course)

    def list_grades(self) -> list[Grade]:
        return self._store.list_grades()

    def clear_all(self) -> None:
        self._store.clear_all()

    def record_grade(
        self,
        student_id: str,
        course_id: str,
        score: float,
        date: str,
        notes: str = "",
    ) -> Grade:
        student = self._store.get_student(student_id)
        course = self._store.get_course(course_id)
        grade = Grade(student, course, score, date, notes)
        self._store.record_grade(grade)
        return grade

    def get_student_grades(self, student_id: str) -> list[Grade]:
        return self._store.get_student_grades(student_id)

    def get_course_grades(self, course_id: str) -> list[Grade]:
        return self._store.get_course_grades(course_id)

    def student_average(self, student_id: str) -> float:
        grades = self.get_student_grades(student_id)
        if not grades:
            raise ValueError(f"No grades recorded for student {student_id}")
        return sum(grade.percentage for grade in grades) / len(grades)

    def course_average(self, course_id: str) -> float:
        grades = self.get_course_grades(course_id)
        if not grades:
            raise ValueError(f"No grades recorded for course {course_id}")
        return sum(grade.score for grade in grades) / len(grades)

    def course_pass_rate(self, course_id: str) -> float:
        grades = self.get_course_grades(course_id)
        if not grades:
            raise ValueError(f"No grades recorded for course {course_id}")
        passing = sum(1 for grade in grades if grade.is_passing)
        return passing / len(grades) * 100

    def top_students(self, n: int = 5) -> list[tuple[Student, float]]:
        averages = [
            (student, self.student_average(student.student_id))
            for student in self._store.list_students()
            if self.get_student_grades(student.student_id)
        ]
        averages.sort(key=lambda item: item[1], reverse=True)
        return averages[:n]

    def grade_distribution(self) -> dict[str, int]:
        """Return count of grades per letter (A–F) across all grades."""
        distribution: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for grade in self._store.list_grades():
            distribution[grade.letter_grade] += 1
        return distribution

    def grades_by_letter(self, letter: str) -> list[Grade]:
        """Return all grades that match the given letter grade."""
        return [
            grade
            for grade in self._store.list_grades()
            if grade.letter_grade == letter.upper()
        ]

    def students_at_risk(self, threshold: float = 60.0) -> list[Student]:
        at_risk = []
        for student in self._store.list_students():
            if not self.get_student_grades(student.student_id):
                continue
            if self.student_average(student.student_id) < threshold:
                at_risk.append(student)
        return at_risk

    def search_students(self, query: str) -> list[Student]:
        pattern = re.compile(query, re.IGNORECASE)
        return [
            student
            for student in self._store.list_students()
            if pattern.search(student.full_name)
            or pattern.search(student.email)
        ]

    def search_courses(self, query: str) -> list[Course]:
        pattern = re.compile(query, re.IGNORECASE)
        return [
            course
            for course in self._store.list_courses()
            if pattern.search(course.name)
        ]

    def to_dict(self) -> dict:
        return {
            "students": [
                {
                    "student_id": student.student_id,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email,
                }
                for student in self._store.list_students()
            ],
            "courses": [
                {
                    "course_id": course.course_id,
                    "name": course.name,
                    "max_grade": course.max_grade,
                    "passing_grade": course.passing_grade,
                }
                for course in self._store.list_courses()
            ],
            "grades": [
                {
                    "student_id": grade.student.student_id,
                    "course_id": grade.course.course_id,
                    "score": float(grade.score),
                    "date": grade.date,
                    "notes": grade.notes,
                }
                for grade in self._store.list_grades()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict, store: GradeStore | None = None) -> "GradeBook":
        gradebook = cls(_store=store) if store is not None else cls()

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

    def save_json(self, path: Path | str) -> None:
        file_path = Path(path)
        try:
            file_path.write_text(
                json.dumps(self.to_dict(), indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise PersistenceError(
                f"Failed to save grade book to {file_path}: {exc}"
            ) from exc

    @classmethod
    def load_json(
        cls, path: Path | str, store: GradeStore | None = None
    ) -> "GradeBook":
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

        return cls.from_dict(data, store=store)

    def export_students_csv(self, path: Path | str) -> None:
        csv_io.export_students_csv(self, path)

    def export_courses_csv(self, path: Path | str) -> None:
        csv_io.export_courses_csv(self, path)

    def export_grades_csv(self, path: Path | str) -> None:
        csv_io.export_grades_csv(self, path)

    def import_students_csv(self, path: Path | str) -> CsvImportReport:
        file_path = Path(path)
        report = CsvImportReport()

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise PersistenceError(
                f"Failed to read students from {file_path}: {exc}"
            ) from exc

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if line_number == 1 and stripped.lower().startswith("student_id"):
                continue

            match = STUDENT_CSV_LINE_PATTERN.match(stripped)
            if not match:
                report.skipped += 1
                report.errors.append(f"Line {line_number}: invalid format")
                continue

            student_id = match.group("student_id").strip()
            first_name = match.group("first_name").strip()
            last_name = match.group("last_name").strip()
            email = match.group("email").strip()

            try:
                self.add_student(Student(student_id, first_name, last_name, email))
            except DuplicateEntryError:
                report.skipped += 1
                report.errors.append(
                    f"Line {line_number}: duplicate student {student_id} skipped"
                )
                continue
            except ValueError as exc:
                report.skipped += 1
                report.errors.append(f"Line {line_number}: {exc}")
                continue

            report.imported += 1

        return report

    def import_courses_csv(self, path: Path | str) -> CsvImportReport:
        file_path = Path(path)
        report = CsvImportReport()

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise PersistenceError(
                f"Failed to read courses from {file_path}: {exc}"
            ) from exc

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if line_number == 1 and stripped.lower().startswith("course_id"):
                continue

            match = COURSE_CSV_LINE_PATTERN.match(stripped)
            if not match:
                report.skipped += 1
                report.errors.append(f"Line {line_number}: invalid format")
                continue

            course_id = match.group("course_id").strip()
            name = match.group("name").strip()
            max_grade = (
                float(match.group("max_grade"))
                if match.group("max_grade")
                else 100.0
            )
            passing_grade = (
                float(match.group("passing_grade"))
                if match.group("passing_grade")
                else 50.0
            )

            try:
                self.add_course(
                    Course(
                        course_id,
                        name,
                        max_grade=max_grade,
                        passing_grade=passing_grade,
                    )
                )
            except DuplicateEntryError:
                report.skipped += 1
                report.errors.append(
                    f"Line {line_number}: duplicate course {course_id} skipped"
                )
                continue
            except ValueError as exc:
                report.skipped += 1
                report.errors.append(f"Line {line_number}: {exc}")
                continue

            report.imported += 1

        return report

    def import_grades_csv(self, path: Path | str) -> CsvImportReport:
        file_path = Path(path)
        report = CsvImportReport()

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise PersistenceError(
                f"Failed to read grades from {file_path}: {exc}"
            ) from exc

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if line_number == 1 and stripped.lower().startswith("student_id"):
                continue

            match = GRADE_CSV_LINE_PATTERN.match(stripped)
            if not match:
                report.skipped += 1
                report.errors.append(f"Line {line_number}: invalid format")
                continue

            student_id = match.group("student_id")
            course_id = match.group("course_id")
            score = float(match.group("score"))
            date = match.group("date")
            notes = match.group("notes") or ""

            try:
                self._store.get_student(student_id)
            except StudentNotFoundError:
                report.skipped += 1
                report.errors.append(
                    f"Line {line_number}: student {student_id} not found"
                )
                continue

            try:
                self._store.get_course(course_id)
            except CourseNotFoundError:
                report.skipped += 1
                report.errors.append(
                    f"Line {line_number}: course {course_id} not found"
                )
                continue

            if self._grade_exists(student_id, course_id, score, date, notes):
                report.skipped += 1
                report.errors.append(f"Line {line_number}: duplicate grade skipped")
                continue

            try:
                self.record_grade(student_id, course_id, score, date, notes)
            except ValueError as exc:
                report.skipped += 1
                report.errors.append(f"Line {line_number}: {exc}")
                continue

            report.imported += 1

        return report

    def _grade_exists(
        self,
        student_id: str,
        course_id: str,
        score: float,
        date: str,
        notes: str = "",
    ) -> bool:
        return any(
            grade.student.student_id == student_id
            and grade.course.course_id == course_id
            and float(grade.score) == float(score)
            and grade.date == date
            and (grade.notes or "") == (notes or "")
            for grade in self._store.list_grades()
        )
