"""Gradio dashboard for the grade management system."""

from __future__ import annotations

from pathlib import Path

import gradio as gr
import pandas as pd

from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.course import Course
from notenverwaltung.models.student import Student
from notenverwaltung.reports.csv_report import CsvReportGenerator
from notenverwaltung.reports.text_report import TextReportGenerator
from notenverwaltung.storage.sqlite_store import SqliteGradeStore

DB_PATH = Path(__file__).resolve().parent.parent / "grades.db"
EXPORT_DIR = Path(__file__).resolve().parent.parent / "exports"
TEXT_REPORTS = TextReportGenerator()
CSV_REPORTS = CsvReportGenerator()


def seed_sample_data(gradebook: GradeBook) -> None:
    gradebook.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    gradebook.add_student(Student("S002", "Ben", "Mueller", "ben@example.com"))
    gradebook.add_course(Course("CS101", "Intro to Programming"))
    gradebook.add_course(Course("CS102", "Data Structures"))
    gradebook.record_grade("S001", "CS101", 85, "2026-01-15")
    gradebook.record_grade("S001", "CS102", 92, "2026-01-20")
    gradebook.record_grade("S002", "CS101", 45, "2026-01-15")


def create_gradebook() -> GradeBook:
    store = SqliteGradeStore(str(DB_PATH))
    gradebook = GradeBook(_store=store)
    if not gradebook.store.list_students() and not gradebook.store.list_courses():
        seed_sample_data(gradebook)
    return gradebook


GRADE_BOOK = create_gradebook()


def student_ids() -> list[str]:
    return [student.student_id for student in GRADE_BOOK.store.list_students()]


def course_ids() -> list[str]:
    return [course.course_id for course in GRADE_BOOK.store.list_courses()]


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
        if not student_id or not course_id:
            return "Error: student and course must be selected."
        date_value = _normalize_date(date)
        GRADE_BOOK.record_grade(student_id, course_id, score, date_value, notes or "")
        return f"Recorded grade {score} for {student_id} in {course_id}."
    except Exception as exc:
        return f"Error: {exc}"


def _normalize_date(date: str | float | int | None) -> str:
    """Convert Gradio DateTime values to ISO date strings (YYYY-MM-DD)."""
    if date is None or date == "":
        raise ValueError("Date is required")

    if isinstance(date, (int, float)):
        from datetime import datetime, timezone

        return datetime.fromtimestamp(float(date), tz=timezone.utc).strftime("%Y-%m-%d")

    text = str(date).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]

    # Numeric timestamp coming through as string
    try:
        from datetime import datetime, timezone

        return datetime.fromtimestamp(float(text), tz=timezone.utc).strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date: {date}") from exc


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


def csv_report(report_type: str, entity_id: str) -> str:
    try:
        if report_type == "Student":
            return CSV_REPORTS.generate_student_report(entity_id, GRADE_BOOK)
        if report_type == "Course":
            return CSV_REPORTS.generate_course_report(entity_id, GRADE_BOOK)
        return CSV_REPORTS.generate_summary_report(GRADE_BOOK)
    except Exception as exc:
        return f"Error: {exc}"


CSV_FORMAT_HELP = {
    "Students": (
        "### Students CSV format\n"
        "`student_id,first_name,last_name,email`\n\n"
        "Duplicates (same student_id) are skipped."
    ),
    "Courses": (
        "### Courses CSV format\n"
        "`course_id,name,max_grade,passing_grade`\n\n"
        "`max_grade` and `passing_grade` are optional "
        "(defaults: 100 and 50). Duplicates are skipped."
    ),
    "Grades": (
        "### Grades CSV format\n"
        "`student_id,course_id,score,date` (optional `notes`)\n\n"
        "Students and courses must already exist. Duplicate grades are skipped."
    ),
}


def csv_format_help(entity: str) -> str:
    return CSV_FORMAT_HELP.get(entity, CSV_FORMAT_HELP["Grades"])


def _format_import_report(report) -> str:
    lines = [
        f"Imported: {report.imported}",
        f"Skipped: {report.skipped}",
    ]
    if report.errors:
        lines.append("Errors:")
        lines.extend(f"  - {error}" for error in report.errors)
    return "\n".join(lines)


def export_csv(entity: str) -> tuple[str | None, str]:
    try:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        if entity == "Students":
            export_path = EXPORT_DIR / "students_export.csv"
            GRADE_BOOK.export_students_csv(export_path)
            count = len(GRADE_BOOK.store.list_students())
            label = "student(s)"
        elif entity == "Courses":
            export_path = EXPORT_DIR / "courses_export.csv"
            GRADE_BOOK.export_courses_csv(export_path)
            count = len(GRADE_BOOK.store.list_courses())
            label = "course(s)"
        else:
            export_path = EXPORT_DIR / "grades_export.csv"
            GRADE_BOOK.export_grades_csv(export_path)
            count = len(GRADE_BOOK.store.list_grades())
            label = "grade(s)"
        return str(export_path), f"Exported {count} {label} to {export_path.name}."
    except Exception as exc:
        return None, f"Error: {exc}"


def import_csv(entity: str, file_path: str | None) -> str:
    if not file_path:
        return "Error: please upload a CSV file first."
    try:
        if entity == "Students":
            report = GRADE_BOOK.import_students_csv(file_path)
        elif entity == "Courses":
            report = GRADE_BOOK.import_courses_csv(file_path)
        else:
            report = GRADE_BOOK.import_grades_csv(file_path)
        return _format_import_report(report)
    except Exception as exc:
        return f"Error: {exc}"


def clear_database(confirmed: bool, reload_sample: bool) -> str:
    if not confirmed:
        return "Error: confirm the action first (check the box)."
    try:
        GRADE_BOOK.store.clear_all()
        if reload_sample:
            seed_sample_data(GRADE_BOOK)
            return "Database cleared and sample data reloaded."
        return "Database cleared. All students, courses, and grades removed."
    except Exception as exc:
        return f"Error: {exc}"


def refresh_all_lists_and_dropdowns() -> tuple:
    students = student_ids()
    courses = course_ids()
    student_update = gr.update(
        choices=students, value=students[0] if students else None
    )
    course_update = gr.update(
        choices=courses, value=courses[0] if courses else None
    )
    return (
        list_students(),
        list_courses(),
        student_update,
        student_update,
        course_update,
        course_update,
    )


def dashboard_stats() -> tuple[str, dict[str, int]]:
    grades = GRADE_BOOK.store.list_grades()
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for grade in grades:
        distribution[grade.letter_grade] += 1

    summary = TEXT_REPORTS.generate_summary_report(GRADE_BOOK)
    return summary, distribution


def updated_student_dropdowns() -> tuple:
    ids = student_ids()
    update = gr.update(choices=ids, value=ids[-1] if ids else None)
    return update, update


def updated_course_dropdowns() -> tuple:
    ids = course_ids()
    update = gr.update(choices=ids, value=ids[-1] if ids else None)
    return update, update


def update_report_entity_dropdown(report_type: str):
    if report_type == "Student":
        ids = student_ids()
        return gr.update(
            choices=ids,
            value=ids[0] if ids else None,
            visible=True,
            label="Student ID",
        )
    if report_type == "Course":
        ids = course_ids()
        return gr.update(
            choices=ids,
            value=ids[0] if ids else None,
            visible=True,
            label="Course ID",
        )
    return gr.update(choices=[], value=None, visible=False, label="Student/Course ID")


def build_app() -> gr.Blocks:
    initial_students = student_ids()
    initial_courses = course_ids()

    with gr.Blocks(title="Notenverwaltung", theme=gr.Theme.from_hub("VikramSingh178/Webui-Theme")) as app:
        gr.Markdown("# Student Grade Tracker (Notenverwaltung)")
        gr.Markdown(f"Database: `{DB_PATH}`")

        with gr.Tab("Students"):
            gr.Markdown("### Current Students")
            students_list = gr.Textbox(value=list_students(), lines=5, max_lines=10, label="Students")
            with gr.Row():
                new_student_id = gr.Textbox(label="Student ID")
                first_name = gr.Textbox(label="First Name")
                last_name = gr.Textbox(label="Last Name")
                email = gr.Textbox(label="Email")
            add_student_btn = gr.Button("Add Student")
            add_student_result = gr.Textbox(label="Result")
            student_report_id = gr.Dropdown(
                choices=initial_students,
                label="Student for Report",
                value=initial_students[0] if initial_students else None,
            )
            student_report_btn = gr.Button("View Student Report")
            student_report_output = gr.Textbox(label="Student Report", lines=12)

        with gr.Tab("Courses"):
            gr.Markdown("### Current Courses")
            courses_list = gr.Textbox(value=list_courses(), lines=6, max_lines=10, label="Courses")
            with gr.Row():
                new_course_id = gr.Textbox(label="Course ID")
                course_name = gr.Textbox(label="Course Name")
            add_course_btn = gr.Button("Add Course")
            add_course_result = gr.Textbox(label="Result")
            course_report_id = gr.Dropdown(
                choices=initial_courses,
                label="Course for Report",
                value=initial_courses[0] if initial_courses else None,
            )
            course_report_btn = gr.Button("View Course Statistics")
            course_report_output = gr.Textbox(label="Course Report", lines=12)

        with gr.Tab("Grades"):
            grade_student = gr.Dropdown(
                choices=initial_students,
                label="Student",
                value=initial_students[0] if initial_students else None,
            )
            grade_course = gr.Dropdown(
                choices=initial_courses,
                label="Course",
                value=initial_courses[0] if initial_courses else None,
            )
            grade_score = gr.Slider(minimum=0, maximum=100, label="Score", value=75)
            grade_date = gr.DateTime(label="Date (YYYY-MM-DD)", type="string", include_time=False, interactive=True)
            grade_notes = gr.Textbox(label="Notes")
            record_grade_btn = gr.Button("Record Grade")
            record_grade_result = gr.Textbox(label="Result")

        with gr.Tab("Reports"):
            report_type = gr.Radio(
                ["Student", "Course", "Summary"], value="Summary", label="Report Type"
            )
            report_entity = gr.Dropdown(
                choices=[],
                label="Student/Course ID",
                value=None,
                visible=False,
            )
            generate_csv_btn = gr.Button("Generate CSV Report")
            csv_output = gr.Textbox(label="CSV Output", lines=12)

        with gr.Tab("Import / Export"):
            csv_entity = gr.Radio(
                ["Students", "Courses", "Grades"],
                value="Grades",
                label="Data type",
            )
            csv_help = gr.Markdown(csv_format_help("Grades"))
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Export")
                    export_btn = gr.Button("Export to CSV")
                    export_file = gr.File(label="Download exported CSV")
                    export_result = gr.Textbox(label="Export result")
                with gr.Column():
                    gr.Markdown("#### Import")
                    import_file = gr.File(
                        label="Upload CSV file",
                        file_types=[".csv"],
                        type="filepath",
                    )
                    import_btn = gr.Button("Import from CSV")
                    import_result = gr.Textbox(label="Import report", lines=10)

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

        with gr.Tab("Extra"):
            gr.Markdown(
                "### Database maintenance\n"
                "Clear all students, courses, and grades from the SQLite database.\n\n"
                "**Warning:** this cannot be undone."
            )
            confirm_clear = gr.Checkbox(
                label="I understand this will permanently delete all data",
                value=False,
            )
            reload_sample = gr.Checkbox(
                label="Reload sample data after clearing",
                value=False,
            )
            clear_btn = gr.Button("Clear Database", variant="stop")
            clear_result = gr.Textbox(label="Result")

        add_student_btn.click(
            add_student,
            inputs=[new_student_id, first_name, last_name, email],
            outputs=add_student_result,
        ).then(list_students, outputs=students_list).then(
            updated_student_dropdowns,
            outputs=[student_report_id, grade_student],
        )

        student_report_btn.click(
            student_report, inputs=student_report_id, outputs=student_report_output
        )

        add_course_btn.click(
            add_course,
            inputs=[new_course_id, course_name],
            outputs=add_course_result,
        ).then(list_courses, outputs=courses_list).then(
            updated_course_dropdowns,
            outputs=[course_report_id, grade_course],
        )

        course_report_btn.click(
            course_report, inputs=course_report_id, outputs=course_report_output
        )

        record_grade_btn.click(
            record_grade,
            inputs=[grade_student, grade_course, grade_score, grade_date, grade_notes],
            outputs=record_grade_result,
        )

        generate_csv_btn.click(
            csv_report, inputs=[report_type, report_entity], outputs=csv_output
        )

        report_type.change(
            update_report_entity_dropdown,
            inputs=report_type,
            outputs=report_entity,
        )

        export_btn.click(
            export_csv,
            inputs=csv_entity,
            outputs=[export_file, export_result],
        )

        import_btn.click(
            import_csv,
            inputs=[csv_entity, import_file],
            outputs=import_result,
        ).then(
            refresh_all_lists_and_dropdowns,
            outputs=[
                students_list,
                courses_list,
                student_report_id,
                grade_student,
                course_report_id,
                grade_course,
            ],
        )

        csv_entity.change(
            csv_format_help,
            inputs=csv_entity,
            outputs=csv_help,
        )

        clear_btn.click(
            clear_database,
            inputs=[confirm_clear, reload_sample],
            outputs=clear_result,
        ).then(
            refresh_all_lists_and_dropdowns,
            outputs=[
                students_list,
                courses_list,
                student_report_id,
                grade_student,
                course_report_id,
                grade_course,
            ],
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
    build_app().launch()#(share=True)


if __name__ == "__main__":
    main()
