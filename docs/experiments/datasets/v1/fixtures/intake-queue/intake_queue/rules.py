from intake_queue.envelope import compute_checksum


class IntakeRules:
    def accepts(self, envelope):
        return envelope.declared_checksum() == compute_checksum(envelope)
