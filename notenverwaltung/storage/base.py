from abc import ABC, abstractmethod

from notenverwaltung.models.course import Course
from notenverwaltung.models.grade import Grade
from notenverwaltung.models.student import Student


class GradeStore(ABC):
    @abstractmethod
    def add_student(self, student: Student) -> None:
        """Add a student to the store."""

    @abstractmethod
    def get_student(self, student_id: str) -> Student:
        """Return a student by ID."""

    @abstractmethod
    def list_students(self) -> list[Student]:
        """Return all students."""

    @abstractmethod
    def add_course(self, course: Course) -> None:
        """Add a course to the store."""

    @abstractmethod
    def get_course(self, course_id: str) -> Course:
        """Return a course by ID."""

    @abstractmethod
    def list_courses(self) -> list[Course]:
        """Return all courses."""

    @abstractmethod
    def record_grade(self, grade: Grade) -> None:
        """Persist a grade."""

    @abstractmethod
    def get_student_grades(self, student_id: str) -> list[Grade]:
        """Return all grades for a student."""

    @abstractmethod
    def get_course_grades(self, course_id: str) -> list[Grade]:
        """Return all grades for a course."""

    @abstractmethod
    def list_grades(self) -> list[Grade]:
        """Return all grades."""

    @abstractmethod
    def clear_all(self) -> None:
        """Remove all students, courses, and grades."""
