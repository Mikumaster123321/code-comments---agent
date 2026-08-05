package com.example;

import java.util.*;
import java.io.Serializable;

/**
 * 图书馆管理系统
 * 支持图书的借阅、归还和库存管理
 */
public class Library implements Serializable {

    private String name;
    private List<Book> books;
    private Map<String, Member> members;

    /**
     * 图书状态枚举
     */
    public enum BookStatus {
        AVAILABLE, BORROWED, LOST, RESERVED
    }

    // 静态嵌套类
    public static class Book {
        private String title;
        private String author;
        private BookStatus status;

        public Book(String title, String author) {
            this.title = title;
            this.author = author;
            this.status = BookStatus.AVAILABLE;
        }

        @Override
        public String toString() {
            return title + " by " + author + " [" + status + "]";
        }
    }

    // 内部类（非静态）
    public class Member {
        private String name;
        private List<Book> borrowedBooks;

        public Member(String name) {
            this.name = name;
            this.borrowedBooks = new ArrayList<>();
        }

        public void borrowBook(Book book) {
            if (book.status == BookStatus.AVAILABLE) {
                borrowedBooks.add(book);
                book.status = BookStatus.BORROWED;
            }
        }

        public int getBorrowedCount() {
            return borrowedBooks.size();
        }
    }

    public Library(String name) {
        this.name = name;
        this.books = new ArrayList<>();
        this.members = new HashMap<>();
    }

    /**
     * 添加图书到图书馆
     * @param book 要添加的图书对象
     * @throws IllegalArgumentException 图书为 null 时抛出
     */
    public void addBook(Book book) {
        if (book == null) {
            throw new IllegalArgumentException("图书不能为空");
        }
        books.add(book);
    }

    public Member registerMember(String name) {
        Member member = new Member(name);
        members.put(name, member);
        return member;
    }

    public Book findBookByTitle(String title) {
        for (Book book : books) {
            if (book.title.equals(title)) {
                return book;
            }
        }
        return null;
    }

    public <T extends Book> List<T> filterBooks(List<T> allBooks, String author) {
        List<T> result = new ArrayList<>();
        for (T book : allBooks) {
            if (book.author.equals(author)) {
                result.add(book);
            }
        }
        return result;
    }

    public void runMaintenanceTask() {
        Runnable task = new Runnable() {
            @Override
            public void run() {
                for (Book book : books) {
                    if (book.status == BookStatus.LOST) {
                        System.out.println("丢失: " + book.title);
                    }
                }
            }
        };
        Thread thread = new Thread(task);
        thread.start();
    }

    public List<Book> getAvailableBooks() {
        List<Book> available = new ArrayList<>();
        int[] counts = new int[BookStatus.values().length];
        for (Book book : books) {
            counts[book.status.ordinal()]++;
            if (book.status == BookStatus.AVAILABLE) {
                available.add(book);
            }
        }
        return available;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("Library: ").append(name).append("\n");
        sb.append("Books: ").append(books.size()).append("\n");
        sb.append("Members: ").append(members.size());
        return sb.toString();
    }
}
