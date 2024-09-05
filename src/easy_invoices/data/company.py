"""company (you) info"""

from dataclasses import dataclass
from .contact import Contact


@dataclass
class Company(Contact):
    business_number: str = ""
