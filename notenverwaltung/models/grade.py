from dataclasses import dataclass

from notenverwaltung.models.course import Course
from notenverwaltung.models.student import Student


@dataclass
class Grade:
    student: Student
    course: Course
    score: float
    date: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.score <= self.course.max_grade:
            raise ValueError(
                f"Score {self.score} out of range [0, {self.course.max_grade}]"
            )

    @property
    def is_passing(self) -> bool:
        return self.score >= self.course.passing_grade

    @property
    def percentage(self) -> float:
        return self.score / self.course.max_grade * 100

    @property
    def letter_grade(self) -> str:
        percentage = self.percentage
        if percentage >= 90:
            return "A"
        if percentage >= 80:
            return "B"
        if percentage >= 70:
            return "C"
        if percentage >= 60:
            return "D"
        return "F"

    def __str__(self) -> str:
        base = (
            f"{self.student.full_name} - {self.course.name}: "
            f"{self.score} ({self.letter_grade}) on {self.date}"
        )
        if self.notes:
            return f"{base} [{self.notes}]"
        return base
