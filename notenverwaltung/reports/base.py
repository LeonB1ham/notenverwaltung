from abc import ABC, abstractmethod

from notenverwaltung.gradebook import GradeBook


class ReportGenerator(ABC):
    @abstractmethod
    def generate_student_report(self, student_id: str, gradebook: GradeBook) -> str:
        """Generate a report for a single student."""

    @abstractmethod
    def generate_course_report(self, course_id: str, gradebook: GradeBook) -> str:
        """Generate a report for a single course."""

    @abstractmethod
    def generate_summary_report(self, gradebook: GradeBook) -> str:
        """Generate an overall summary report."""
