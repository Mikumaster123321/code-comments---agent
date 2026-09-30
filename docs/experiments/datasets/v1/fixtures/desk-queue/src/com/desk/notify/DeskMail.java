package com.desk.notify;

public class DeskMail {
    public String render(String id, String title) {
        return "Ticket " + id + ": " + title;
    }
}
