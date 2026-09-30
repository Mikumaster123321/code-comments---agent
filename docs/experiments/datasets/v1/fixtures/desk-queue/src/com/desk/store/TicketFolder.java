package com.desk.store;

import com.desk.model.Ticket;

public class TicketFolder {
    public Ticket[] entries = new Ticket[0];

    public void put(Ticket ticket) {
        for (int i = 0; i < entries.length; i++) {
            if (entries[i].id().equals(ticket.id())) {
                entries[i] = ticket;
                return;
            }
        }
        Ticket[] expanded = new Ticket[entries.length + 1];
        System.arraycopy(entries, 0, expanded, 0, entries.length);
        expanded[entries.length] = ticket;
        entries = expanded;
    }

    public Ticket find(String id) {
        for (Ticket stored : entries) {
            if (stored.id().equals(id)) {
                Ticket copy = new Ticket(stored.id(), stored.title());
                copy.note = stored.note;
                if (!stored.isOpen()) { copy.markClosed(); }
                return copy;
            }
        }
        return null;
    }
}
