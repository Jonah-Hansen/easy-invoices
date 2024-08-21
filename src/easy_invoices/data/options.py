"""invoice options"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List
from .serializable_data import SerializableData


class PaymentTerms(Enum):
    PIA = "PIA"
    NET7 = "NET7"
    NET10 = "NET10"
    NET30 = "NET30"
    NET60 = "NET60"
    NET90 = "NET90"
    EOM = "EOM"
    MFI21 = "21MFI"


def payment_term_from_string(string: str) -> PaymentTerms:
    """returns the enum that corresponds to the string"""
    for item in PaymentTerms:
        if item.value == string:
            return item
    raise ValueError(f"No PaymentTerm found with value '{string}'")


@dataclass
class Taxes:
    type: str = ""
    percent: int = 0


@dataclass
class Options(SerializableData):
    payment_terms: str = PaymentTerms.NET30.value
    rate: float = 0.00
    taxes: List[Taxes] = field(default_factory=list)
