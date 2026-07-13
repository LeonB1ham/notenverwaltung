"""Gradio dashboard for the grade management system."""

from __future__ import annotations

import gradio as gr
import pandas as pd

from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.course import Course
from notenverwaltung.models.student import Student
from notenverwaltung.reports.csv_report import CsvReportGenerator
from notenverwaltung.reports.text_report import TextReportGenerator


def create_sample_gradebook() -> GradeBook:
    gradebook = GradeBook()
    gradebook.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gradebook.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gradebook.add_course(Course("CS101", "Intro to Programming"))
    gradebook.add_course(Course("CS102", "Data Structures"))
    gradebook.record_grade("S001", "CS101", 85, "2026-01-15")
    gradebook.record_grade("S001", "CS102", 92, "2026-01-20")
    gradebook.record_grade("S002", "CS101", 45, "2026-01-15")
    return gradebook


GRADE_BOOK = create_sample_gradebook()
TEXT_REPORTS = TextReportGenerator()
CSV_REPORTS = CsvReportGenerator()


def list_students() -> str:
    lines = [
        f"{student.student_id}: {student.full_name} ({student.email})"
        for student in GRADE_BOOK.store.list_students()
    ]
    return "\n".join(lines) if lines else "No students yet."


def list_courses() -> str:
    lines = [
        f"{course.course_id}: {course.name}"
        for course in GRADE_BOOK.store.list_courses()
    ]
    return "\n".join(lines) if lines else "No courses yet."


def add_student(student_id: str, first_name: str, last_name: str, email: str) -> str:
    try:
        GRADE_BOOK.add_student(Student(student_id, first_name, last_name, email))
        return f"Added student {first_name} {last_name}."
    except Exception as exc:
        return f"Error: {exc}"


def add_course(course_id: str, name: str) -> str:
    try:
        GRADE_BOOK.add_course(Course(course_id, name))
        return f"Added course {name}."
    except Exception as exc:
        return f"Error: {exc}"


def record_grade(
    student_id: str, course_id: str, score: float, date: str, notes: str
) -> str:
    try:
        GRADE_BOOK.record_grade(student_id, course_id, score, date, notes)
        return f"Recorded grade {score} for {student_id} in {course_id}."
    except Exception as exc:
        return f"Error: {exc}"


def student_report(student_id: str) -> str:
    try:
        return TEXT_REPORTS.generate_student_report(student_id, GRADE_BOOK)
    except Exception as exc:
        return f"Error: {exc}"


def course_report(course_id: str) -> str:
    try:
        return TEXT_REPORTS.generate_course_report(course_id, GRADE_BOOK)
    except Exception as exc:
        return f"Error: {exc}"


def summary_report() -> str:
    return TEXT_REPORTS.generate_summary_report(GRADE_BOOK)


def csv_report(report_type: str, entity_id: str) -> str:
    try:
        if report_type == "Student":
            return CSV_REPORTS.generate_student_report(entity_id, GRADE_BOOK)
        if report_type == "Course":
            return CSV_REPORTS.generate_course_report(entity_id, GRADE_BOOK)
        return CSV_REPORTS.generate_summary_report(GRADE_BOOK)
    except Exception as exc:
        return f"Error: {exc}"


def dashboard_stats() -> tuple[str, dict[str, int]]:
    grades = GRADE_BOOK.store.list_grades()
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for grade in grades:
        distribution[grade.letter_grade] += 1

    summary = TEXT_REPORTS.generate_summary_report(GRADE_BOOK)
    return summary, distribution


def build_app() -> gr.Blocks:
    student_ids = [student.student_id for student in GRADE_BOOK.store.list_students()]
    course_ids = [course.course_id for course in GRADE_BOOK.store.list_courses()]

    with gr.Blocks(title="Notenverwaltung") as app:
        gr.Markdown("# Student Grade Tracker (Notenverwaltung)")

        with gr.Tab("Students"):
            gr.Markdown("### Current Students")
            students_list = gr.Textbox(value=list_students(), lines=6, label="Students")
            with gr.Row():
                student_id = gr.Textbox(label="Student ID")
                first_name = gr.Textbox(label="First Name")
                last_name = gr.Textbox(label="Last Name")
                email = gr.Textbox(label="Email")
            add_student_btn = gr.Button("Add Student")
            add_student_result = gr.Textbox(label="Result")
            student_report_id = gr.Dropdown(
                choices=student_ids, label="Student for Report", value=student_ids[0]
            )
            student_report_btn = gr.Button("View Student Report")
            student_report_output = gr.Textbox(label="Student Report", lines=12)

            add_student_btn.click(
                add_student,
                inputs=[student_id, first_name, last_name, email],
                outputs=add_student_result,
            ).then(list_students, outputs=students_list)
            student_report_btn.click(
                student_report, inputs=student_report_id, outputs=student_report_output
            )

        with gr.Tab("Courses"):
            gr.Markdown("### Current Courses")
            courses_list = gr.Textbox(value=list_courses(), lines=6, label="Courses")
            with gr.Row():
                course_id = gr.Textbox(label="Course ID")
                course_name = gr.Textbox(label="Course Name")
            add_course_btn = gr.Button("Add Course")
            add_course_result = gr.Textbox(label="Result")
            course_report_id = gr.Dropdown(
                choices=course_ids, label="Course for Report", value=course_ids[0]
            )
            course_report_btn = gr.Button("View Course Statistics")
            course_report_output = gr.Textbox(label="Course Report", lines=12)

            add_course_btn.click(
                add_course, inputs=[course_id, course_name], outputs=add_course_result
            ).then(list_courses, outputs=courses_list)
            course_report_btn.click(
                course_report, inputs=course_report_id, outputs=course_report_output
            )

        with gr.Tab("Grades"):
            grade_student = gr.Dropdown(choices=student_ids, label="Student")
            grade_course = gr.Dropdown(choices=course_ids, label="Course")
            grade_score = gr.Number(label="Score", value=75)
            grade_date = gr.Textbox(label="Date (YYYY-MM-DD)", value="2026-01-15")
            grade_notes = gr.Textbox(label="Notes")
            record_grade_btn = gr.Button("Record Grade")
            record_grade_result = gr.Textbox(label="Result")
            record_grade_btn.click(
                record_grade,
                inputs=[grade_student, grade_course, grade_score, grade_date, grade_notes],
                outputs=record_grade_result,
            )

        with gr.Tab("Reports"):
            report_type = gr.Radio(
                ["Student", "Course", "Summary"], value="Summary", label="Report Type"
            )
            report_entity = gr.Dropdown(
                choices=student_ids, label="Student/Course ID", value=student_ids[0]
            )
            generate_csv_btn = gr.Button("Generate CSV Report")
            csv_output = gr.Textbox(label="CSV Output", lines=12)
            generate_csv_btn.click(
                csv_report, inputs=[report_type, report_entity], outputs=csv_output
            )

        with gr.Tab("Dashboard"):
            refresh_btn = gr.Button("Refresh Dashboard")
            dashboard_text = gr.Textbox(label="Summary", lines=14)
            grade_chart = gr.BarPlot(
                x="letter",
                y="count",
                title="Grade Distribution",
                x_title="Letter Grade",
                y_title="Count",
            )

            def refresh_dashboard() -> tuple[str, pd.DataFrame]:
                summary, distribution = dashboard_stats()
                chart_data = pd.DataFrame(
                    [
                        {"letter": letter, "count": count}
                        for letter, count in distribution.items()
                    ]
                )
                return summary, chart_data

            refresh_btn.click(
                refresh_dashboard,
                outputs=[dashboard_text, grade_chart],
            )
            app.load(refresh_dashboard, outputs=[dashboard_text, grade_chart])

    return app


def main() -> None:
    build_app().launch()


if __name__ == "__main__":
    main()
