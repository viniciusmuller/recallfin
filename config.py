import os
from sys import platform
from pathlib import Path
from dataclasses import dataclass

def get_os_base_dir() -> str:
    if platform == "linux" or platform == "linux2":
        return "~/.local/share"
    elif platform == "darwin":
        return "~/Library"
    elif platform == "win32":
        return "%APPDATA%"

def get_directory() -> Path:
    return Path(get_os_base_dir() + "/recallfin")

def screenshots_directory(base_directory: Path) -> Path:
    return Path(os.path.join(base_directory, "screenshots"))

def db_path(base_directory: Path) -> Path:
    return Path(os.path.join(base_directory, "database.db"))

@dataclass
class Context:
    data_directory: str
    screenshots_directory: str
    database_path: str
    monitor_index: int

