"""base class for dataclasses that can be serialized to json"""

from importlib.metadata import PackageNotFoundError, metadata
import tomllib
from dataclasses import asdict, dataclass
import json
import os
from typing import List, Self
from platformdirs import user_data_dir


@dataclass
class SerializableData:
    id: str = "default"

    @staticmethod
    def _pluralize(word: str) -> str:
        if word.endswith("s"):
            return word
        if word.endswith("y"):
            return word[:-1] + "ies"
        return word + "s"

    @property
    def _file_path(self):
        return os.path.join(self._data_dir, f"{self.id}.json")

    @property
    def _data_dir(self):
        return os.path.join(
            user_data_dir(_get_app_name()),
            self._pluralize(self.__class__.__name__),
        )

    @property
    def exists(self) -> bool:
        """returns true if the corresponding json file exists"""
        return os.path.exists(self._file_path)

    def save(self: Self, overwrite: bool = False) -> bool:

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
        files: List[str] = []
        try:
            # List all files and directories in the given directory
            for filename in os.listdir(self._data_dir):
                file_path = os.path.join(self._data_dir, filename)
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


def _find_pyproject_toml():
    current_dir = os.path.abspath(os.path.dirname(__file__))

    while True:
        potential_path = os.path.join(current_dir, "pyproject.toml")
        if os.path.isfile(potential_path):
            return potential_path

        new_dir = os.path.abspath(os.path.join(current_dir, ".."))
        if new_dir == current_dir:
            break

        current_dir = new_dir

    return None


def _get_app_name():
    try:
        # Try to get metadata from installed package
        return metadata(__package__ or "easy_invoices")["Name"]
    except PackageNotFoundError as exc:
        # Fall back to reading from pyproject.toml in development
        pyproject_path = _find_pyproject_toml()
        if not pyproject_path:
            raise FileNotFoundError("pyproject.toml not found.") from exc

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        return pyproject_data.get("project", {}).get("name")
