package com.desk.model;

public class Ticket {
    private String key;
    private String heading;
    private String status = "open";
    public String note = "";

    public Ticket(String id, String title) {
        key = id;
        heading = title;
    }

    public String id() { return key; }
    public String title() { return heading; }
    public boolean isOpen() { return status.equals("open"); }
    public void markClosed() { status = "closed"; }
    public String statusLabel() { return isOpen() ? "open" : "closed"; }
}
