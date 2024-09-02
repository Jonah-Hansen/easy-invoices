"""
base class for dataclasses that can be serialized to json.
also acts as the crud api for dataclass files
"""

from abc import ABC
from importlib.metadata import PackageNotFoundError, metadata
import tomllib
from dataclasses import asdict, dataclass, fields, is_dataclass
import json
import os
from typing import Any, Dict, List, Self, Union
from platformdirs import user_data_dir


@dataclass
class SerializableData(ABC):
    id: str = "default"

    @property
    def exists(self) -> bool:
        """returns true if the corresponding json file exists"""
        return os.path.exists(self._file_path)

    @property
    def asdict(self) -> Dict[str, Any]:
        """
        returns this object and its fields as a full dictionary
        (recursive for nested classes and lists)
        """
        return {k: _serialize(v) for k, v in asdict(self).items()}

    @property
    def _file_path(self) -> str:
        """path to the file that would correspond with this object's id"""
        return os.path.join(self._data_dir, f"{self.id}.json")

    @property
    def _data_dir(self) -> str:
        """
        path to the directory where files for this object type should be saved
        """
        return os.path.join(
            user_data_dir(_get_app_name()),
            _pluralize(self.__class__.__name__),
        )

    def delete(self):
        if not self.exists:
            raise FileNotFoundError
        os.remove(self._file_path)

    def save(self: Self):
        # Ensure the directory exists
        os.makedirs(self._data_dir, exist_ok=True)
        # Serialize the instance to JSON
        with open(self._file_path, "w", encoding="utf8") as json_file:
            json.dump(asdict(self), json_file, indent=4)

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

    def load(self) -> Self:
        """
        populate this instance with data loaded from the corresponding file
        """
        try:
            with open(self._file_path, "r", encoding="utf8") as file:
                data: dict[str, Any] = json.load(file)
                self.populate_fields(data)
        except FileNotFoundError:
            print(f"Error: {self.__class__.__name__} '{self.id}' not found")
        except json.JSONDecodeError:
            print(f"Error: The file '{self._file_path}' contains invalid JSON.")
        return self

    def populate_fields(self, data: dict[str, Any]) -> None:
        """populates the fields of this instance from the provided data"""
        for field in fields(self):
            if not field.name in data:
                continue
            if is_dataclass(field.type):
                setattr(self, field.name, field.type(**data[field.name]))
            else:
                setattr(self, field.name, data[field.name])


# === private functions ===


def _serialize(obj: Any) -> Union[Dict[str, Any], List[Any], Any]:
    """returns the object, serialized to basic types"""
    if is_dataclass(type[obj]):  # recursively serialize class fields
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):  # recursively serialize list items
        return [_serialize(i) for i in obj]  # type: ignore
    if isinstance(obj, dict):  # recursively serialize dict values
        return {k: _serialize(v) for k, v in obj.items()}  # type: ignore
    return obj  # obj is not serializable or is already serialized


def _pluralize(word: str) -> str:
    if word.endswith("s"):
        return word
    if word.endswith("y"):
        return word[:-1] + "ies"
    return word + "s"


def _find_pyproject_toml() -> str | None:
    """
    returns the path to the pyproject toml file.
    for use in develoment with get_app_name()
    """
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
