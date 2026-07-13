class NotenverwaltungError(Exception):
    """Base exception for the grade management system."""


class StudentNotFoundError(NotenverwaltungError):
    """Raised when a student ID does not exist."""


class CourseNotFoundError(NotenverwaltungError):
    """Raised when a course ID does not exist."""


class DuplicateEntryError(NotenverwaltungError):
    """Raised when adding a student or course that already exists."""


class PersistenceError(NotenverwaltungError):
    """Raised when file read/write operations fail."""
