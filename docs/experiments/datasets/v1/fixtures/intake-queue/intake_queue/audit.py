from dataclasses import dataclass, field


@dataclass
class IntakeAudit:
    entries: list = field(default_factory=list)

    def record(self, envelope, reason):
        self.entries.append((envelope.envelope_id, reason))
