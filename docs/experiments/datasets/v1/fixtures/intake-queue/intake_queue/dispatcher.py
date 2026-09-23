from dataclasses import dataclass, field
from intake_queue.rules import IntakeRules
from intake_queue.parser import IntakeParser
from intake_queue.audit import IntakeAudit


@dataclass
class Dispatcher:
    rules: object = field(default_factory=IntakeRules)
    parser: object = field(default_factory=IntakeParser)
    audit: object = field(default_factory=IntakeAudit)
    queue: list = field(default_factory=list)

    def enqueue(self, envelope):
        if not self.rules.accepts(envelope):
            self.audit.record(envelope, self.parser.reject_reason(envelope))
            return False
        self.queue.append(envelope)
        return True

    def dispatch_ready(self, envelopes):
        accepted = []
        for envelope in envelopes:
            if self.enqueue(envelope):
                accepted.append(envelope)
        return tuple(accepted)
