from notenverwaltung.course import Course
from notenverwaltung.exceptions import (
    CourseNotFoundError,
    DuplicateEntryError,
    StudentNotFoundError,
)
from notenverwaltung.grade import Grade
from notenverwaltung.storage.base import GradeStore
from notenverwaltung.student import Student


class InMemoryGradeStore(GradeStore):
    def __init__(self) -> None:
        self._students: dict[str, Student] = {}
        self._courses: dict[str, Course] = {}
        self._grades: list[Grade] = []

    def add_student(self, student: Student) -> None:
        if student.student_id in self._students:
            raise DuplicateEntryError(f"Student {student.student_id} already exists")
        self._students[student.student_id] = student

    def get_student(self, student_id: str) -> Student:
        if student_id not in self._students:
            raise StudentNotFoundError(f"Student {student_id} not found")
        return self._students[student_id]

    def list_students(self) -> list[Student]:
        return list(self._students.values())

    def add_course(self, course: Course) -> None:
        if course.course_id in self._courses:
            raise DuplicateEntryError(f"Course {course.course_id} already exists")
        self._courses[course.course_id] = course

    def get_course(self, course_id: str) -> Course:
        if course_id not in self._courses:
            raise CourseNotFoundError(f"Course {course_id} not found")
        return self._courses[course_id]

    def list_courses(self) -> list[Course]:
        return list(self._courses.values())

    def record_grade(self, grade: Grade) -> None:
        self._grades.append(grade)

    def get_student_grades(self, student_id: str) -> list[Grade]:
        return [
            grade
            for grade in self._grades
            if grade.student.student_id == student_id
        ]

    def get_course_grades(self, course_id: str) -> list[Grade]:
        return [
            grade for grade in self._grades if grade.course.course_id == course_id
        ]

    def list_grades(self) -> list[Grade]:
        return list(self._grades)
