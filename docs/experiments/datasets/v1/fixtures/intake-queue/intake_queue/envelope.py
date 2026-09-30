from dataclasses import dataclass
from hashlib import sha256


@dataclass
class Envelope:
    envelope_id: str
    body: str
    checksum: str

    def declared_checksum(self):
        return self.checksum


def compute_checksum(envelope):
    return sha256((envelope.envelope_id + envelope.body).encode("utf-8")).hexdigest()
