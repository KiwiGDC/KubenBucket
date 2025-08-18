import enum

class FileStatus(enum.Enum):
    processing = "processing"
    done = "done"
    error = "error"