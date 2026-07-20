"""Gradio dashboard for the grade management system."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import gradio as gr
import pandas as pd

from notenverwaltung.bootstrap import (
    DB_PATH,
    EXPORT_DIR,
    create_gradebook,
    seed_sample_data,
)
from notenverwaltung.models.course import Course
from notenverwaltung.models.student import Student
from notenverwaltung.reports.csv_report import CsvReportGenerator
from notenverwaltung.reports.text_report import TextReportGenerator

TEXT_REPORTS = TextReportGenerator()
CSV_REPORTS = CsvReportGenerator()

GRADE_BOOK = create_gradebook()


def student_ids() -> list[str]:
    return [student.student_id for student in GRADE_BOOK.list_students()]


def course_ids() -> list[str]:
    return [course.course_id for course in GRADE_BOOK.list_courses()]


def student_choices() -> list[str]:
    return [
        f"{student.student_id}: {student.full_name}"
        for student in GRADE_BOOK.list_students()
    ]


def course_choices() -> list[str]:
    return [
        f"{course.course_id}: {course.name}"
        for course in GRADE_BOOK.list_courses()
    ]


def _parse_choice_id(choice: str | None) -> str | None:
    if not choice:
        return None
    return choice.split(":", 1)[0].strip() or None


def save_student(
    selected: str | None,
    student_id: str,
    first_name: str,
    last_name: str,
    email: str,
) -> tuple:
    try:
        selected_id = _parse_choice_id(selected)
        if selected_id:
            GRADE_BOOK.update_student(
                Student(selected_id, first_name, last_name, email)
            )
            message = f"Updated student {first_name} {last_name}."
            current_id = selected_id
        else:
            GRADE_BOOK.add_student(Student(student_id, first_name, last_name, email))
            message = f"Added student {first_name} {last_name}."
            current_id = student_id

        choices = student_choices()
        selected_choice = next(
            (item for item in choices if item.startswith(f"{current_id}:")),
            None,
        )
        return (
            message,
            gr.update(choices=choices, value=selected_choice),
            gr.update(value="Update Student"),
            gr.update(value=current_id, interactive=False),
        )
    except Exception as exc:
        return f"Error: {exc}", gr.update(), gr.update(), gr.update()


def save_course(
    selected: str | None,
    course_id: str,
    name: str,
    passing_grade: float,
) -> tuple:
    try:
        selected_id = _parse_choice_id(selected)
        if selected_id:
            existing = GRADE_BOOK.get_course(selected_id)
            GRADE_BOOK.update_course(
                Course(
                    selected_id,
                    name,
                    max_grade=existing.max_grade,
                    passing_grade=float(passing_grade),
                )
            )
            message = f"Updated course {name}."
            current_id = selected_id
        else:
            GRADE_BOOK.add_course(
                Course(course_id, name, passing_grade=float(passing_grade))
            )
            message = f"Added course {name}."
            current_id = course_id

        choices = course_choices()
        selected_choice = next(
            (item for item in choices if item.startswith(f"{current_id}:")),
            None,
        )
        return (
            message,
            gr.update(choices=choices, value=selected_choice),
            gr.update(value="Update Course"),
            gr.update(value=current_id, interactive=False),
        )
    except Exception as exc:
        return f"Error: {exc}", gr.update(), gr.update(), gr.update()


def load_student_for_edit(selected: str | None):
    student_id = _parse_choice_id(selected)
    if not student_id:
        return (
            gr.update(value="", interactive=True),
            "",
            "",
            "",
            gr.update(value="Add Student"),
        )
    student = GRADE_BOOK.get_student(student_id)
    return (
        gr.update(value=student.student_id, interactive=False),
        student.first_name,
        student.last_name,
        student.email,
        gr.update(value="Update Student"),
    )


def load_course_for_edit(selected: str | None):
    course_id = _parse_choice_id(selected)
    if not course_id:
        return (
            gr.update(value="", interactive=True),
            "",
            50,
            gr.update(value="Add Course"),
        )
    course = GRADE_BOOK.get_course(course_id)
    return (
        gr.update(value=course.course_id, interactive=False),
        course.name,
        course.passing_grade,
        gr.update(value="Update Course"),
    )


def clear_student_form():
    return (
        None,
        gr.update(value="", interactive=True),
        "",
        "",
        "",
        gr.update(value="Add Student"),
        "",
    )


def clear_course_form():
    return (
        None,
        gr.update(value="", interactive=True),
        "",
        50,
        gr.update(value="Add Course"),
        "",
    )


def record_grade(
    student_choice: str, course_choice: str, score: float, date: str, notes: str
) -> str:
    try:
        student_id = _parse_choice_id(student_choice)
        course_id = _parse_choice_id(course_choice)
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


def student_report(student_choice: str) -> str:
    try:
        student_id = _parse_choice_id(student_choice)
        if not student_id:
            return "Error: please select a student."
        return TEXT_REPORTS.generate_student_report(student_id, GRADE_BOOK)
    except Exception as exc:
        return f"Error: {exc}"


def course_report(course_choice: str) -> str:
    try:
        course_id = _parse_choice_id(course_choice)
        if not course_id:
            return "Error: please select a course."
        return TEXT_REPORTS.generate_course_report(course_id, GRADE_BOOK)
    except Exception as exc:
        return f"Error: {exc}"


def csv_report(report_type: str, entity_choice: str) -> str:
    try:
        entity_id = _parse_choice_id(entity_choice)
        if report_type == "Student":
            if not entity_id:
                return "Error: please select a student."
            return CSV_REPORTS.generate_student_report(entity_id, GRADE_BOOK)
        if report_type == "Course":
            if not entity_id:
                return "Error: please select a course."
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
            count = len(GRADE_BOOK.list_students())
            label = "student(s)"
        elif entity == "Courses":
            export_path = EXPORT_DIR / "courses_export.csv"
            GRADE_BOOK.export_courses_csv(export_path)
            count = len(GRADE_BOOK.list_courses())
            label = "course(s)"
        else:
            export_path = EXPORT_DIR / "grades_export.csv"
            GRADE_BOOK.export_grades_csv(export_path)
            count = len(GRADE_BOOK.list_grades())
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
        GRADE_BOOK.clear_all()
        if reload_sample:
            seed_sample_data(GRADE_BOOK)
            return "Database cleared and sample data reloaded."
        return "Database cleared. All students, courses, and grades removed."
    except Exception as exc:
        return f"Error: {exc}"


def refresh_all_lists_and_dropdowns() -> tuple:
    student_pick_choices = student_choices()
    course_pick_choices = course_choices()
    student_update = gr.update(
        choices=student_pick_choices,
        value=student_pick_choices[0] if student_pick_choices else None,
    )
    course_update = gr.update(
        choices=course_pick_choices,
        value=course_pick_choices[0] if course_pick_choices else None,
    )
    return (
        gr.update(choices=student_pick_choices, value=None),
        gr.update(choices=course_pick_choices, value=None),
        student_update,
        student_update,
        course_update,
        course_update,
        gr.update(value="Add Student"),
        gr.update(value="Add Course"),
        gr.update(value="", interactive=True),
        "",
        "",
        "",
        gr.update(value="", interactive=True),
        "",
        50,
    )


def dashboard_stats() -> tuple[str, dict[str, int]]:
    summary = TEXT_REPORTS.generate_summary_report(GRADE_BOOK)
    distribution = GRADE_BOOK.grade_distribution()
    return summary, distribution


def grades_for_letter(letter: str | None) -> str:
    if not letter:
        return "Select a letter grade to see matching students and scores."

    letter = letter.strip().upper()
    if letter not in {"A", "B", "C", "D", "F"}:
        return f"Unknown letter grade: {letter}"

    matching = GRADE_BOOK.grades_by_letter(letter)
    if not matching:
        return f"Letter grade: {letter}\n\nNo grades in this category."

    average = sum(grade.score for grade in matching) / len(matching)
    lines = [
        f"Letter grade: {letter}",
        f"Count: {len(matching)}",
        f"Average score: {average:.1f}",
        "",
        f"{'Student':<28} {'Course':<28} {'Score':>6} {'Date':<12}",
        "-" * 78,
    ]
    for grade in matching:
        lines.append(
            f"{grade.student.full_name:<28} {grade.course.name:<28} "
            f"{grade.score:>6.1f} {grade.date:<12}"
        )
    return "\n".join(lines)


def _keep_choice(
    current: str | None,
    choices: list[str],
    *,
    fallback_first: bool = False,
) -> str | None:
    if current and current in choices:
        return current
    if fallback_first and choices:
        return choices[0]
    return None


def sync_entity_dropdowns(
    student_picker_val: str | None,
    course_picker_val: str | None,
    student_report_val: str | None,
    grade_student_val: str | None,
    course_report_val: str | None,
    grade_course_val: str | None,
    report_type: str,
    report_entity_val: str | None,
) -> tuple:
    """Reload student/course dropdowns from the database (multi-user / share safe)."""
    students = student_choices()
    courses = course_choices()

    if report_type == "Student":
        report_entity = gr.update(
            choices=students,
            value=_keep_choice(report_entity_val, students, fallback_first=True),
            visible=True,
            label="Student",
        )
    elif report_type == "Course":
        report_entity = gr.update(
            choices=courses,
            value=_keep_choice(report_entity_val, courses, fallback_first=True),
            visible=True,
            label="Course",
        )
    else:
        report_entity = gr.update(
            choices=[],
            value=None,
            visible=False,
            label="Student/Course",
        )

    return (
        gr.update(
            choices=students,
            value=_keep_choice(student_picker_val, students),
        ),
        gr.update(
            choices=courses,
            value=_keep_choice(course_picker_val, courses),
        ),
        gr.update(
            choices=students,
            value=_keep_choice(student_report_val, students, fallback_first=True),
        ),
        gr.update(
            choices=students,
            value=_keep_choice(grade_student_val, students, fallback_first=True),
        ),
        gr.update(
            choices=courses,
            value=_keep_choice(course_report_val, courses, fallback_first=True),
        ),
        gr.update(
            choices=courses,
            value=_keep_choice(grade_course_val, courses, fallback_first=True),
        ),
        report_entity,
    )


def update_report_entity_dropdown(report_type: str):
    if report_type == "Student":
        choices = student_choices()
        return gr.update(
            choices=choices,
            value=choices[0] if choices else None,
            visible=True,
            label="Student",
        )
    if report_type == "Course":
        choices = course_choices()
        return gr.update(
            choices=choices,
            value=choices[0] if choices else None,
            visible=True,
            label="Course",
        )
    return gr.update(choices=[], value=None, visible=False, label="Student/Course")


def build_app() -> gr.Blocks:
    initial_student_choices = student_choices()
    initial_course_choices = course_choices()

    with gr.Blocks(title="Notenverwaltung") as app:
        gr.Markdown("# Student Grade Tracker (Notenverwaltung)")
        gr.Markdown(f"Database: `{DB_PATH}`")
        with gr.Row():
            refresh_lists_btn = gr.Button("Refresh lists", variant="secondary")

        with gr.Tab("Students"):
            gr.Markdown("### Students")
            student_picker = gr.Dropdown(
                choices=initial_student_choices,
                label="Select student to edit (leave empty to add new)",
                info="Type to search by ID or name",
                value=None,
                allow_custom_value=False,
                filterable=True,
            )
            clear_student_btn = gr.Button("New Student / Clear Form")
            with gr.Row():
                new_student_id = gr.Textbox(label="Student ID", interactive=True)
                first_name = gr.Textbox(label="First Name")
                last_name = gr.Textbox(label="Last Name")
                email = gr.Textbox(label="Email")
            save_student_btn = gr.Button("Add Student")
            add_student_result = gr.Textbox(label="Result")
            student_report_id = gr.Dropdown(
                choices=initial_student_choices,
                label="Student for Report",
                info="Type to search by ID or name",
                value=initial_student_choices[0] if initial_student_choices else None,
                filterable=True,
            )
            student_report_btn = gr.Button("View Student Report")
            student_report_output = gr.Textbox(label="Student Report", lines=12)

        with gr.Tab("Courses"):
            gr.Markdown("### Courses")
            course_picker = gr.Dropdown(
                choices=initial_course_choices,
                label="Select course to edit (leave empty to add new)",
                info="Type to search by ID or title",
                value=None,
                allow_custom_value=False,
                filterable=True,
            )
            clear_course_btn = gr.Button("New Course / Clear Form")
            with gr.Row():
                new_course_id = gr.Textbox(label="Course ID", interactive=True)
                course_name = gr.Textbox(label="Course Name")
            course_passing_grade = gr.Slider(
                minimum=1,
                maximum=100,
                step=1,
                value=50,
                label="Passing grade",
            )
            save_course_btn = gr.Button("Add Course")
            add_course_result = gr.Textbox(label="Result")
            course_report_id = gr.Dropdown(
                choices=initial_course_choices,
                label="Course for Report",
                info="Type to search by ID or title",
                value=initial_course_choices[0] if initial_course_choices else None,
                filterable=True,
            )
            course_report_btn = gr.Button("View Course Statistics")
            course_report_output = gr.Textbox(label="Course Report", lines=12)

        with gr.Tab("Grades"):
            grade_student = gr.Dropdown(
                choices=initial_student_choices,
                label="Student",
                info="Type to search by ID or name",
                value=initial_student_choices[0] if initial_student_choices else None,
                filterable=True,
            )
            grade_course = gr.Dropdown(
                choices=initial_course_choices,
                label="Course",
                info="Type to search by ID or title",
                value=initial_course_choices[0] if initial_course_choices else None,
                filterable=True,
            )
            grade_score = gr.Slider(minimum=0, maximum=100, label="Score", value=75)
            grade_date = gr.DateTime(
                value=date.today().isoformat(),
                label="Date (YYYY-MM-DD)",
                type="string",
                include_time=False,
                interactive=True,
            )
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
                info="Type to search",
                value=None,
                visible=False,
                filterable=True,
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
            letter_filter = gr.Radio(
                choices=["A", "B", "C", "D", "F"],
                label="Letter grade details",
                info="Select a letter to list matching students and scores.",
                value=None,
            )
            grade_detail = gr.Textbox(
                label="Selected letter details",
                lines=12,
                value="Select a letter grade to see matching students and scores.",
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

        student_picker.change(
            load_student_for_edit,
            inputs=student_picker,
            outputs=[
                new_student_id,
                first_name,
                last_name,
                email,
                save_student_btn,
            ],
        )

        list_dropdown_inputs = [
            student_picker,
            course_picker,
            student_report_id,
            grade_student,
            course_report_id,
            grade_course,
            report_type,
            report_entity,
        ]
        list_dropdown_outputs = [
            student_picker,
            course_picker,
            student_report_id,
            grade_student,
            course_report_id,
            grade_course,
            report_entity,
        ]

        refresh_lists_btn.click(
            sync_entity_dropdowns,
            inputs=list_dropdown_inputs,
            outputs=list_dropdown_outputs,
        )
        app.load(
            sync_entity_dropdowns,
            inputs=list_dropdown_inputs,
            outputs=list_dropdown_outputs,
        )

        clear_student_btn.click(
            clear_student_form,
            outputs=[
                student_picker,
                new_student_id,
                first_name,
                last_name,
                email,
                save_student_btn,
                add_student_result,
            ],
        )

        save_student_btn.click(
            save_student,
            inputs=[student_picker, new_student_id, first_name, last_name, email],
            outputs=[
                add_student_result,
                student_picker,
                save_student_btn,
                new_student_id,
            ],
        ).then(
            sync_entity_dropdowns,
            inputs=list_dropdown_inputs,
            outputs=list_dropdown_outputs,
        )

        student_report_btn.click(
            student_report, inputs=student_report_id, outputs=student_report_output
        )

        course_picker.change(
            load_course_for_edit,
            inputs=course_picker,
            outputs=[
                new_course_id,
                course_name,
                course_passing_grade,
                save_course_btn,
            ],
        )

        clear_course_btn.click(
            clear_course_form,
            outputs=[
                course_picker,
                new_course_id,
                course_name,
                course_passing_grade,
                save_course_btn,
                add_course_result,
            ],
        )

        save_course_btn.click(
            save_course,
            inputs=[course_picker, new_course_id, course_name, course_passing_grade],
            outputs=[
                add_course_result,
                course_picker,
                save_course_btn,
                new_course_id,
            ],
        ).then(
            sync_entity_dropdowns,
            inputs=list_dropdown_inputs,
            outputs=list_dropdown_outputs,
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
                student_picker,
                course_picker,
                student_report_id,
                grade_student,
                course_report_id,
                grade_course,
                save_student_btn,
                save_course_btn,
                new_student_id,
                first_name,
                last_name,
                email,
                new_course_id,
                course_name,
                course_passing_grade,
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
                student_picker,
                course_picker,
                student_report_id,
                grade_student,
                course_report_id,
                grade_course,
                save_student_btn,
                save_course_btn,
                new_student_id,
                first_name,
                last_name,
                email,
                new_course_id,
                course_name,
                course_passing_grade,
            ],
        )

        def refresh_dashboard() -> tuple[str, pd.DataFrame, None, str]:
            summary, distribution = dashboard_stats()
            chart_data = pd.DataFrame(
                [
                    {"letter": letter, "count": count}
                    for letter, count in distribution.items()
                ]
            )
            return (
                summary,
                chart_data,
                None,
                "Select a letter grade to see matching students and scores.",
            )

        refresh_btn.click(
            refresh_dashboard,
            outputs=[dashboard_text, grade_chart, letter_filter, grade_detail],
        )
        app.load(
            refresh_dashboard,
            outputs=[dashboard_text, grade_chart, letter_filter, grade_detail],
        )
        letter_filter.change(grades_for_letter, inputs=letter_filter, outputs=grade_detail)

    return app


def main() -> None:
    build_app().launch(
        theme=gr.Theme.from_hub("VikramSingh178/Webui-Theme"),
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
