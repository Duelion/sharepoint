import time
from dataclasses import dataclass

from pydantic import BaseModel, validator


@dataclass
class TokenData:
    access_token: str
    expire_in: int

    def __post_init__(self):
        self.expire_on = time.time() + self.expire_in

    def is_expired(self):
        now = time.time_ns()
        return now >= self.expire_on





