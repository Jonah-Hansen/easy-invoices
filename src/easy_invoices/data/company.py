"""company (you) info"""

from dataclasses import dataclass
from .contact import Contact


@dataclass
class Company(Contact):
    tax_id: str = ""
