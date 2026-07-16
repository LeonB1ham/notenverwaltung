import sqlite3
from sqlite3 import Connection, Row

from notenverwaltung.models.course import Course
from notenverwaltung.models.grade import Grade
from notenverwaltung.models.student import Student

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    max_grade REAL NOT NULL DEFAULT 100.0,
    passing_grade REAL NOT NULL DEFAULT 50.0
);

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    score REAL NOT NULL,
    date TEXT NOT NULL,
    notes TEXT DEFAULT '',
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
"""


class GradeDatabase:
    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn: Connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        if db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_schema()

    def close(self) -> None:
        self._conn.close()

    def clear_all(self) -> None:
        self._conn.execute("DELETE FROM grades")
        self._conn.execute("DELETE FROM courses")
        self._conn.execute("DELETE FROM students")
        self._conn.commit()

    def _create_schema(self) -> None:
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def add_student(self, student: Student) -> None:
        self._conn.execute(
            """
            INSERT INTO students (student_id, first_name, last_name, email)
            VALUES (?, ?, ?, ?)
            """,
            (
                student.student_id,
                student.first_name,
                student.last_name,
                student.email,
            ),
        )
        self._conn.commit()

    def get_student(self, student_id: str) -> Student | None:
        row = self._conn.execute(
            """
            SELECT student_id, first_name, last_name, email
            FROM students
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_student(row)

    def list_students(self) -> list[Student]:
        rows = self._conn.execute(
            """
            SELECT student_id, first_name, last_name, email
            FROM students
            ORDER BY student_id
            """
        ).fetchall()
        return [self._row_to_student(row) for row in rows]

    def add_course(self, course: Course) -> None:
        self._conn.execute(
            """
            INSERT INTO courses (course_id, name, max_grade, passing_grade)
            VALUES (?, ?, ?, ?)
            """,
            (
                course.course_id,
                course.name,
                course.max_grade,
                course.passing_grade,
            ),
        )
        self._conn.commit()

    def get_course(self, course_id: str) -> Course | None:
        row = self._conn.execute(
            """
            SELECT course_id, name, max_grade, passing_grade
            FROM courses
            WHERE course_id = ?
            """,
            (course_id,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_course(row)

    def list_courses(self) -> list[Course]:
        rows = self._conn.execute(
            """
            SELECT course_id, name, max_grade, passing_grade
            FROM courses
            ORDER BY course_id
            """
        ).fetchall()
        return [self._row_to_course(row) for row in rows]

    def add_grade(self, grade: Grade) -> None:
        self._conn.execute(
            """
            INSERT INTO grades (student_id, course_id, score, date, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                grade.student.student_id,
                grade.course.course_id,
                grade.score,
                grade.date,
                grade.notes,
            ),
        )
        self._conn.commit()

    def get_student_grades(self, student_id: str) -> list[Grade]:
        rows = self._conn.execute(
            """
            SELECT
                g.score,
                g.date,
                g.notes,
                s.student_id,
                s.first_name,
                s.last_name,
                s.email,
                c.course_id,
                c.name,
                c.max_grade,
                c.passing_grade
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            JOIN courses c ON g.course_id = c.course_id
            WHERE g.student_id = ?
            ORDER BY g.date, g.id
            """,
            (student_id,),
        ).fetchall()
        return [self._row_to_grade(row) for row in rows]

    def get_course_grades(self, course_id: str) -> list[Grade]:
        rows = self._conn.execute(
            """
            SELECT
                g.score,
                g.date,
                g.notes,
                s.student_id,
                s.first_name,
                s.last_name,
                s.email,
                c.course_id,
                c.name,
                c.max_grade,
                c.passing_grade
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            JOIN courses c ON g.course_id = c.course_id
            WHERE g.course_id = ?
            ORDER BY g.date, g.id
            """,
            (course_id,),
        ).fetchall()
        return [self._row_to_grade(row) for row in rows]

    def list_grades(self) -> list[Grade]:
        rows = self._conn.execute(
            """
            SELECT
                g.score,
                g.date,
                g.notes,
                s.student_id,
                s.first_name,
                s.last_name,
                s.email,
                c.course_id,
                c.name,
                c.max_grade,
                c.passing_grade
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            JOIN courses c ON g.course_id = c.course_id
            ORDER BY g.date, g.id
            """
        ).fetchall()
        return [self._row_to_grade(row) for row in rows]

    def student_average_sql(self, student_id: str) -> float:
        row = self._conn.execute(
            """
            SELECT AVG(g.score * 100.0 / c.max_grade) AS average_percentage
            FROM grades g
            JOIN courses c ON g.course_id = c.course_id
            WHERE g.student_id = ?
            """,
            (student_id,),
        ).fetchone()
        if row is None or row["average_percentage"] is None:
            raise ValueError(f"No grades recorded for student {student_id}")
        return float(row["average_percentage"])

    def course_average_sql(self, course_id: str) -> float:
        row = self._conn.execute(
            """
            SELECT AVG(score) AS average_score
            FROM grades
            WHERE course_id = ?
            """,
            (course_id,),
        ).fetchone()
        if row is None or row["average_score"] is None:
            raise ValueError(f"No grades recorded for course {course_id}")
        return float(row["average_score"])

    def course_pass_rate_sql(self, course_id: str) -> float:
        row = self._conn.execute(
            """
            SELECT
                CAST(
                    SUM(CASE WHEN g.score >= c.passing_grade THEN 1 ELSE 0 END)
                    AS REAL
                ) / COUNT(*) * 100 AS pass_rate
            FROM grades g
            JOIN courses c ON g.course_id = c.course_id
            WHERE g.course_id = ?
            """,
            (course_id,),
        ).fetchone()
        if row is None or row["pass_rate"] is None:
            raise ValueError(f"No grades recorded for course {course_id}")
        return float(row["pass_rate"])

    @staticmethod
    def _row_to_student(row: Row) -> Student:
        return Student(
            row["student_id"],
            row["first_name"],
            row["last_name"],
            row["email"],
        )

    @staticmethod
    def _row_to_course(row: Row) -> Course:
        return Course(
            row["course_id"],
            row["name"],
            row["max_grade"],
            row["passing_grade"],
        )

    @classmethod
    def _row_to_grade(cls, row: Row) -> Grade:
        return Grade(
            cls._row_to_student(row),
            cls._row_to_course(row),
            row["score"],
            row["date"],
            row["notes"] or "",
        )
