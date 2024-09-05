"""preset class to save a configuration preset"""

from dataclasses import dataclass
from .serializable_data import SerializableData


@dataclass
class Preset(SerializableData):
    company: str = "default"
    contact: str = "default"
    options: str = "default"
