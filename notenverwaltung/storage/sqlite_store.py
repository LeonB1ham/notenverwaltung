import sqlite3

from notenverwaltung.models.course import Course
from notenverwaltung.exceptions import (
    CourseNotFoundError,
    DuplicateEntryError,
    StudentNotFoundError,
)
from notenverwaltung.models.grade import Grade
from notenverwaltung.storage.base import GradeStore
from notenverwaltung.storage.database import GradeDatabase
from notenverwaltung.models.student import Student


class SqliteGradeStore(GradeStore):
    def __init__(self, db_path: str = ":memory:") -> None:
        self._database = GradeDatabase(db_path)

    @property
    def database(self) -> GradeDatabase:
        return self._database

    def close(self) -> None:
        self._database.close()

    def add_student(self, student: Student) -> None:
        try:
            self._database.add_student(student)
        except sqlite3.IntegrityError as exc:
            raise DuplicateEntryError(
                f"Student {student.student_id} already exists"
            ) from exc

    def get_student(self, student_id: str) -> Student:
        student = self._database.get_student(student_id)
        if student is None:
            raise StudentNotFoundError(f"Student {student_id} not found")
        return student

    def list_students(self) -> list[Student]:
        return self._database.list_students()

    def add_course(self, course: Course) -> None:
        try:
            self._database.add_course(course)
        except sqlite3.IntegrityError as exc:
            raise DuplicateEntryError(
                f"Course {course.course_id} already exists"
            ) from exc

    def get_course(self, course_id: str) -> Course:
        course = self._database.get_course(course_id)
        if course is None:
            raise CourseNotFoundError(f"Course {course_id} not found")
        return course

    def list_courses(self) -> list[Course]:
        return self._database.list_courses()

    def record_grade(self, grade: Grade) -> None:
        self._database.add_grade(grade)

    def get_student_grades(self, student_id: str) -> list[Grade]:
        return self._database.get_student_grades(student_id)

    def get_course_grades(self, course_id: str) -> list[Grade]:
        return self._database.get_course_grades(course_id)

    def list_grades(self) -> list[Grade]:
        return self._database.list_grades()
