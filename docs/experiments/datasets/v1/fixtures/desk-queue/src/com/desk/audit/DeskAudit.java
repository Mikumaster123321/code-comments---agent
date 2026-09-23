package com.desk.audit;

import com.desk.model.Ticket;

public class DeskAudit {
    public String lastOpened = "";

    public void recordOpen(Ticket ticket) { lastOpened = ticket.id(); }
}
