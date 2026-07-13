from dataclasses import dataclass


@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    email: str

    def __post_init__(self) -> None:
        if not self.first_name.strip():
            raise ValueError("First name must not be empty")
        if not self.last_name.strip():
            raise ValueError("Last name must not be empty")
        if "@" not in self.email:
            raise ValueError(f"Invalid email address: {self.email}")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return f"{self.full_name} ({self.student_id}, {self.email})"
