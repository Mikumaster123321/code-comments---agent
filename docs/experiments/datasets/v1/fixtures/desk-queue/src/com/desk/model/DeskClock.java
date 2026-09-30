package com.desk.model;

public class DeskClock {
    public int now = 0;

    public int minutesUntil(int deadline) { return deadline - now; }
}
