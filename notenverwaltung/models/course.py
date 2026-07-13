from dataclasses import dataclass


@dataclass
class Course:
    course_id: str
    name: str
    max_grade: float = 100.0
    passing_grade: float = 50.0

    def __post_init__(self) -> None:
        if self.max_grade <= 0:
            raise ValueError(f"max_grade must be positive, got {self.max_grade}")
        if not 0 < self.passing_grade <= self.max_grade:
            raise ValueError(
                f"passing_grade must be in (0, {self.max_grade}], "
                f"got {self.passing_grade}"
            )

    def __str__(self) -> str:
        return f"{self.name} ({self.course_id})"
