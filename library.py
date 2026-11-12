import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date, timedelta

#DATABASE SETUP
DB_NAME = "library.db"

conn = sqlite3.connect(DB_NAME)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS book (
    isbn TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity >= 0)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    date_joined TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS borrow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id TEXT NOT NULL,
    member_id INTEGER NOT NULL,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    status TEXT NOT NULL DEFAULT 'Issued',
    FOREIGN KEY(book_id) REFERENCES book(isbn),
    FOREIGN KEY(member_id) REFERENCES members(id)
)
""")
conn.commit()

#DATABASE FUNCTIONS

def add_book(isbn, title, author, quantity):
    try:
        cursor.execute(
            "INSERT INTO book (isbn, title, author, quantity) VALUES (?, ?, ?, ?)",
            (isbn, title, author, quantity))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def search_book(isbn):
    cursor.execute("SELECT * FROM book WHERE isbn = ?", (isbn,))
    return cursor.fetchone()

def update_book(isbn, change):
    cursor.execute("UPDATE book SET quantity = quantity + ? WHERE isbn = ?", (change, isbn))
    conn.commit()
    
def get_all_books():
    cursor.execute("SELECT * FROM book ORDER BY title")
    return cursor.fetchall()

def search_books(keyword):
    cursor.execute("""
        SELECT * FROM book
        WHERE isbn LIKE ? OR title LIKE ? OR author LIKE ?
        ORDER BY title
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    return cursor.fetchall()

def get_low_stock():
    cursor.execute(
        "SELECT * FROM book WHERE quantity <= 3 ORDER BY quantity"
    )
    return cursor.fetchall()

def get_or_add_members(name, email, phone):
    cursor.execute(
        "SELECT id FROM members WHERE name = ? AND email = ?", (name, email)
    )
    member = cursor.fetchone()

    if member:
        return member[0]

    cursor.execute("""
        INSERT INTO members (name, email, phone, date_joined)
        VALUES (?, ?, ?, ?)
    """, (name, email, phone, str(date.today())))
    return cursor.lastrowid

def issue_book(isbn, name, email, phone):
    try:
        book = search_book(isbn)

        if not book:
            return False, "Book not found."

        if book[3] <= 0:
            return False, "This book is out of stock."

        member_id = get_or_add_members(name, email, phone)

        issue_date = date.today()
        due_date = issue_date + timedelta(days=14)

        cursor.execute("""
            INSERT INTO borrow
            (book_id, member_id, issue_date, due_date, status)
            VALUES (?, ?, ?, ?, 'Issued')
        """, (isbn, member_id, str(issue_date), str(due_date)))

        cursor.execute(
            "UPDATE book SET quantity = quantity - 1 WHERE isbn = ?",
            (isbn,)
        )
        conn.commit()
        return True, f"Book issued successfully. Due date: {due_date}."
    
    except sqlite3.Error as error:
        conn.rollback()
        return False, f"Database error: {error}"


def return_book(borrow_id):
    try:
        cursor.execute("""
            SELECT book_id, status FROM borrow WHERE id = ?
        """, (borrow_id,))

        record = cursor.fetchone()

        if not record:
            return False, "Borrow record not found."
        
        if record[1] == "Returned":
            return False, "This book has already been returned."

        cursor.execute(
            "UPDATE books SET quantity = quantity + 1 WHERE isbn = ?", 
            (record[0],)
        )
        conn.commit()
        return True, "Book returned successfully."
    except sqlite3.Error as error:
        conn.rollback()
        return False, f"Database error: {error}."

def get_issued_book():
    cursor.execute("""
        SELECT borrow.id, book.title, members.name, borrow.issue_date, borrow.due_date
        FROM borrow
        JOIN book ON borrow.book_id = book.isbn
        JOIN members ON borrow.member_id = members.id
        WHERE borrow.status = 'Issued'
        ORDER BY borrow.due_date
    """)
    return cursor.fetchall

    
#Validation
def isbn_checker(isbn):
    return len(isbn) == 13 and isbn.isdigit()

def quantity_checker(quantity):
    return quantity.isdigit() and int(quantity) > 0

# GUI APPLICATION
app = tk.Tk()
app.title("City Central Library Management System")
app.geometry("1100x700")
app.minsize(850, 600)
app.resizable(width=True, height=True)
app.configure(bg="#eeeeee")

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    rowheight=28,
    font=("Arial", 10),
    background="white",
    fieldbackground="white"
)

style.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold"),
    background="#dce6f1"
)
style.configure(
    "TCombobox",
    padding=5
)

app.mainloop()