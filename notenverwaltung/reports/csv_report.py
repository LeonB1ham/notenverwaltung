import csv
import io

from notenverwaltung.gradebook import GradeBook
from notenverwaltung.reports.base import ReportGenerator


class CsvReportGenerator(ReportGenerator):
    def generate_student_report(self, student_id: str, gradebook: GradeBook) -> str:
        student = gradebook.get_student(student_id)
        grades = gradebook.get_student_grades(student_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["student_id", "student_name", "email"])
        writer.writerow([student.student_id, student.full_name, student.email])
        writer.writerow([])
        writer.writerow(
            [
                "course_id",
                "course_name",
                "score",
                "letter_grade",
                "status",
                "date",
                "notes",
            ]
        )
        for grade in grades:
            writer.writerow(
                [
                    grade.course.course_id,
                    grade.course.name,
                    grade.score,
                    grade.letter_grade,
                    "PASS" if grade.is_passing else "FAIL",
                    grade.date,
                    grade.notes,
                ]
            )
        if grades:
            writer.writerow([])
            writer.writerow(
                ["overall_average", f"{gradebook.student_average(student_id):.1f}"]
            )
        return output.getvalue()

    def generate_course_report(self, course_id: str, gradebook: GradeBook) -> str:
        course = gradebook.get_course(course_id)
        grades = gradebook.get_course_grades(course_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["course_id", "course_name"])
        writer.writerow([course.course_id, course.name])
        writer.writerow([])
        writer.writerow(
            [
                "student_id",
                "student_name",
                "score",
                "letter_grade",
                "status",
                "date",
                "notes",
            ]
        )
        for grade in grades:
            writer.writerow(
                [
                    grade.student.student_id,
                    grade.student.full_name,
                    grade.score,
                    grade.letter_grade,
                    "PASS" if grade.is_passing else "FAIL",
                    grade.date,
                    grade.notes,
                ]
            )
        if grades:
            distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
            for grade in grades:
                distribution[grade.letter_grade] += 1
            writer.writerow([])
            writer.writerow(["class_average", f"{gradebook.course_average(course_id):.1f}"])
            writer.writerow(["pass_rate", f"{gradebook.course_pass_rate(course_id):.1f}"])
            writer.writerow([])
            writer.writerow(["letter_grade", "count"])
            for letter in ("A", "B", "C", "D", "F"):
                writer.writerow([letter, distribution.get(letter, 0)])
        return output.getvalue()

    def generate_summary_report(self, gradebook: GradeBook) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric", "value"])
        writer.writerow(["total_students", len(gradebook.list_students())])
        writer.writerow(["total_courses", len(gradebook.list_courses())])
        writer.writerow(["total_grades", len(gradebook.list_grades())])

        grades = gradebook.list_grades()
        if grades:
            distribution = gradebook.grade_distribution()
            writer.writerow([])
            writer.writerow(["letter_grade", "count"])
            for letter in ("A", "B", "C", "D", "F"):
                writer.writerow([letter, distribution.get(letter, 0)])

        top_students = gradebook.top_students(n=5)
        if top_students:
            writer.writerow([])
            writer.writerow(["top_student", "average"])
            for student, average in top_students:
                writer.writerow([student.full_name, f"{average:.1f}"])

        at_risk = gradebook.students_at_risk()
        writer.writerow([])
        writer.writerow(["at_risk_student", "average"])
        for student in at_risk:
            writer.writerow(
                [
                    student.full_name,
                    f"{gradebook.student_average(student.student_id):.1f}",
                ]
            )
        if not at_risk:
            writer.writerow(["None", ""])

        return output.getvalue()

