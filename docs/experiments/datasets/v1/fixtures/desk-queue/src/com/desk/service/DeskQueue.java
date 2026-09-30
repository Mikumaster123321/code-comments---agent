package com.desk.service;

import com.desk.model.Ticket;
import com.desk.model.DeskClock;
import com.desk.store.TicketFolder;
import com.desk.notify.DeskMail;
import com.desk.audit.DeskAudit;

public class DeskQueue {
    public TicketFolder folder = new TicketFolder();
    public DeskClock clock = new DeskClock();
    public DeskMail mail = new DeskMail();
    public DeskAudit audit = new DeskAudit();

    public Ticket openTicket(String id, String title) {
        Ticket ticket = new Ticket(id, title);
        folder.put(ticket);
        audit.recordOpen(ticket);
        return ticket;
    }

    public Ticket openTicket(String id, String title, String note) {
        Ticket ticket = openTicket(id, title);
        ticket.note = note;
        return ticket;
    }

    public void closeTicket(String id) {
        Ticket ticket = folder.find(id);
        if (ticket != null) { ticket.markClosed(); }
    }

    public String notifyOwner(String id) {
        Ticket ticket = folder.find(id);
        return mail.render(ticket.id(), ticket.title());
    }

    public int listOpen() { return folder.entries.length; }

    public int minutesLate(String id, int deadline) {
        Ticket ticket = folder.find(id);
        if (ticket == null) { return 0; }
        return -clock.minutesUntil(deadline);
    }
}
