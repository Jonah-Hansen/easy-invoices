"""base class for dataclasses that can be serialized to json.
also acts as the crud api for dataclass files
"""

from abc import ABC
from importlib.metadata import PackageNotFoundError, metadata
import tomllib
from dataclasses import asdict, dataclass
import json
import os
from typing import Any, List, Self
from platformdirs import user_data_dir


@dataclass
class SerializableData(ABC):
    id: str = "default"

    @property
    def exists(self) -> bool:
        """returns true if the corresponding json file exists"""
        return os.path.exists(self._file_path)

    @property
    def _file_path(self) -> str:
        """path to the file that would correspond with this object's id"""
        return os.path.join(self._data_dir, f"{self.id}.json")

    @property
    def _data_dir(self) -> str:
        """path to the directory where files for this object type should be saved"""
        return os.path.join(
            user_data_dir(_get_app_name()),
            _pluralize(self.__class__.__name__),
        )

    def save(self: Self, overwrite: bool = False) -> bool:
        """attempts to save the file. returns true if successful"""
        # Ensure the directory exists
        os.makedirs(self._data_dir, exist_ok=True)
        # Check if the file already exists
        if self.exists and not overwrite:
            return False

        # Serialize the instance to JSON
        with open(self._file_path, "w", encoding="utf8") as json_file:
            json.dump(asdict(self), json_file, indent=4)

        return True

    def list(self) -> List[str]:
        """lists all ids of saved instances of this type"""
        files: List[str] = []
        try:
            # List all files and directories in the given directory
            for filename in os.listdir(self._data_dir):
                file_path: str = os.path.join(self._data_dir, filename)
                # Check if it is a file (not a directory)
                if os.path.isfile(file_path):
                    files.append(os.path.splitext(filename)[0])
        except FileNotFoundError:
            # if the folder is not found, return empty list
            pass
        except PermissionError:
            print(
                f"Permission denied to access the directory {self._data_dir}."
            )
        return files

    @staticmethod
    def load():
        pass

    # === private functions ===


def _pluralize(word: str) -> str:
    if word.endswith("s"):
        return word
    if word.endswith("y"):
        return word[:-1] + "ies"
    return word + "s"


def _find_pyproject_toml() -> str | None:
    """returns the path to the pyproject toml file. for use in develoment with get_app_name()"""
    current_dir: str = os.path.abspath(os.path.dirname(__file__))

    while True:
        potential_path: str = os.path.join(current_dir, "pyproject.toml")
        if os.path.isfile(potential_path):
            return potential_path

        new_dir: str = os.path.abspath(os.path.join(current_dir, ".."))
        if new_dir == current_dir:
            break

        current_dir = new_dir

    return None


def _get_app_name() -> str:
    """returns the app name as specified in pyproject/in installation"""
    try:
        # Try to get metadata from installed package
        return metadata(__package__ or "easy_invoices")["Name"]
    except PackageNotFoundError as exc:
        # Fall back to reading from pyproject.toml in development
        pyproject_path: str | None = _find_pyproject_toml()
        if not pyproject_path:
            raise FileNotFoundError("pyproject.toml not found.") from exc

        with open(pyproject_path, "rb") as f:
            pyproject_data: dict[str, Any] = tomllib.load(f)

        return pyproject_data.get("project", {}).get("name")
