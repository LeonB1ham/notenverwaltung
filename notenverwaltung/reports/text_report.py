from notenverwaltung.gradebook import GradeBook
from notenverwaltung.reports.base import ReportGenerator


class TextReportGenerator(ReportGenerator):
    def generate_student_report(self, student_id: str, gradebook: GradeBook) -> str:
        student = gradebook.store.get_student(student_id)
        grades = gradebook.get_student_grades(student_id)

        lines = [
            f"Student Report: {student.full_name}",
            f"ID: {student.student_id} | Email: {student.email}",
            "=" * 50,
        ]

        if not grades:
            lines.append("No grades recorded.")
            return "\n".join(lines)

        lines.append(f"{'Course':<30} {'Score':>6} {'Letter':>6} {'Status':>8}")
        lines.append("-" * 50)
        for grade in grades:
            status = "PASS" if grade.is_passing else "FAIL"
            lines.append(
                f"{grade.course.name:<30} {grade.score:>6.1f} "
                f"{grade.letter_grade:>6} {status:>8}"
            )

        average = gradebook.student_average(student_id)
        lines.append("-" * 50)
        lines.append(f"Overall Average: {average:.1f}%")
        return "\n".join(lines)

    def generate_course_report(self, course_id: str, gradebook: GradeBook) -> str:
        course = gradebook.store.get_course(course_id)
        grades = gradebook.get_course_grades(course_id)

        lines = [
            f"Course Report: {course.name}",
            f"ID: {course.course_id}",
            "=" * 50,
        ]

        if not grades:
            lines.append("No grades recorded.")
            return "\n".join(lines)

        lines.append(f"{'Student':<30} {'Score':>6} {'Letter':>6} {'Status':>8}")
        lines.append("-" * 50)
        for grade in grades:
            status = "PASS" if grade.is_passing else "FAIL"
            lines.append(
                f"{grade.student.full_name:<30} {grade.score:>6.1f} "
                f"{grade.letter_grade:>6} {status:>8}"
            )

        average = gradebook.course_average(course_id)
        pass_rate = gradebook.course_pass_rate(course_id)
        distribution = gradebook.grade_distribution()

        lines.append("-" * 50)
        lines.append(f"Class Average: {average:.1f}")
        lines.append(f"Pass Rate: {pass_rate:.1f}%")
        lines.append("Grade Distribution:")
        for letter in ("A", "B", "C", "D", "F"):
            lines.append(f"  {letter}: {distribution.get(letter, 0)}")
        return "\n".join(lines)

    def generate_summary_report(self, gradebook: GradeBook) -> str:
        students = gradebook.store.list_students()
        courses = gradebook.store.list_courses()
        grades = gradebook.store.list_grades()

        lines = [
            "Grade Book Summary Report",
            "=" * 50,
            f"Total Students: {len(students)}",
            f"Total Courses: {len(courses)}",
            f"Total Grades: {len(grades)}",
        ]

        if grades:
            distribution = gradebook.grade_distribution()
            lines.append("")
            lines.append("Overall Grade Distribution:")
            for letter in ("A", "B", "C", "D", "F"):
                lines.append(f"  {letter}: {distribution.get(letter, 0)}")

        top_students = gradebook.top_students(n=5)
        if top_students:
            lines.append("")
            lines.append("Top Students:")
            for student, average in top_students:
                lines.append(f"  {student.full_name}: {average:.1f}%")

        at_risk = gradebook.students_at_risk()
        lines.append("")
        lines.append("Students at Risk (< 60%):")
        if at_risk:
            for student in at_risk:
                average = gradebook.student_average(student.student_id)
                lines.append(f"  {student.full_name}: {average:.1f}%")
        else:
            lines.append("  None")

        return "\n".join(lines)

