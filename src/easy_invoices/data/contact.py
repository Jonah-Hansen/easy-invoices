"""contact info for invoice parties (you or client)"""

from dataclasses import dataclass, field
from .address import Address
from .serializable_data import SerializableData


@dataclass
class Contact(SerializableData):
    name: str = ""
    company_name: str = ""
    email: str = ""
    phone: str = ""
    address: Address = field(default_factory=Address)
