package com.example;

import java.util.ArrayList;
import java.util.List;

public class UserService {

    private String serviceName;
    private int maxUsers;

    public UserService(String name, int limit) {
        this.serviceName = name;
        this.maxUsers = limit;
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public int getMaxUsers() {
        return maxUsers;
    }

    public boolean addUser(List<String> users, String userName) {
        if (users.size() >= maxUsers) {
            return false;
        }
        users.add(userName);
        return true;
    }

    public List<String> filterUsers(List<String> users, String prefix) {
        List<String> result = new ArrayList<>();
        for (String user : users) {
            if (user.startsWith(prefix)) {
                result.add(user);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        UserService service = new UserService("UserManager", 100);
        List<String> users = new ArrayList<>();
        service.addUser(users, "Alice");
        service.addUser(users, "Bob");
        List<String> filtered = service.filterUsers(users, "A");
        System.out.println("Filtered: " + filtered);
    }
}
