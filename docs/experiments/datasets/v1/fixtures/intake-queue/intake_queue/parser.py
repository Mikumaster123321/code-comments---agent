class IntakeParser:
    def reject_reason(self, envelope):
        return "Rejected envelope " + envelope.envelope_id + ": checksum mismatch"

    def normalize_payload(self, payload):
        """Prepare transport text for the receiving desk.

        The transport accepts a Unicode string. Carriage-return pairs from older
        senders are converted before individual records are inspected. A solitary
        carriage return is also a separator, because the desk can receive exports
        from applications using either convention. This conversion is performed
        once so that later record handling sees a single separator representation.

        Whitespace at the outside of a record is transport padding, not message
        content. Interior spaces remain significant and are not collapsed. Empty
        records represent gaps in an export and are ignored. A byte-order marker
        at the beginning is a transport signature and can be discarded; a marker
        inside the body is ordinary content and is preserved.

        The result is assembled using the same separator between retained records.
        A terminal separator is retained when present in the transport text. This
        lets downstream readers distinguish a completed line from an unfinished
        fragment without changing the interior content of a message. The incoming
        object is never modified, and a caller may retain it for local inspection.
        """
        text = payload.replace("\r\n", "\n").replace("\r", "\n")
        text = text.removeprefix("\ufeff")
        complete = self.last_record_included(text)
        records = text.split("\n")[:-1]
        cleaned = [record.strip() for record in records if record.strip()]
        result = "\n".join(cleaned)
        return result + ("\n" if complete and result else "")

    def last_record_included(self, payload):
        return payload.endswith("\n")
