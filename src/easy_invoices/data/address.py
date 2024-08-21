"""address dataclass"""

from dataclasses import dataclass


@dataclass
class Address:
    street_address: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    post_code: str = ""
