import java.util.ArrayList;
import java.util.List;
import java.util.HashMap;
import java.util.Map;


public class Library {

    private String name;
    private Map<String, Book> books;
    private List<Member> members;

    public Library(String name) {
        this.name = name;
        this.books = new HashMap<>();
        this.members = new ArrayList<>();
    }

    public void registerMember(Member member) {
        if (member == null) {
            throw new IllegalArgumentException("成员不能为 null");
        }
        if (members.contains(member)) {
            return;
        }
        members.add(member);
    }

    public boolean addBook(Book book) {
        if (book == null || book.getIsbn() == null) {
            return false;
        }
        if (books.containsKey(book.getIsbn())) {
            return false;
        }
        books.put(book.getIsbn(), book);
        return true;
    }

    public Book findBook(String isbn) {
        return books.get(isbn);
    }

    public List<Book> searchByAuthor(String author) {
        List<Book> results = new ArrayList<>();
        for (Book book : books.values()) {
            if (book.getAuthor().equalsIgnoreCase(author)) {
                results.add(book);
            }
        }
        return results;
    }

    public int getBookCount() {
        return books.size();
    }

    public String getLibraryInfo() {
        return String.format("[%s] 藏书 %d 本，会员 %d 人",
                name, books.size(), members.size());
    }

    public static class Book {
        private String isbn;
        private String title;
        private String author;
        private boolean available;

        public Book(String isbn, String title, String author) {
            this.isbn = isbn;
            this.title = title;
            this.author = author;
            this.available = true;
        }

        public String getIsbn() {
            return isbn;
        }

        public String getTitle() {
            return title;
        }

        public String getAuthor() {
            return author;
        }

        public boolean isAvailable() {
            return available;
        }

        public void setAvailable(boolean available) {
            this.available = available;
        }
    }

    public static class Member {
        private int id;
        private String name;
        private List<Book> borrowed;

        public Member(int id, String name) {
            this.id = id;
            this.name = name;
            this.borrowed = new ArrayList<>();
        }

        public boolean borrow(Book book) {
            if (book == null || !book.isAvailable()) {
                return false;
            }
            book.setAvailable(false);
            borrowed.add(book);
            return true;
        }

        public boolean returnBook(Book book) {
            if (book == null || !borrowed.contains(book)) {
                return false;
            }
            book.setAvailable(true);
            borrowed.remove(book);
            return true;
        }

        public int getId() {
            return id;
        }

        public String getName() {
            return name;
        }
    }
}
