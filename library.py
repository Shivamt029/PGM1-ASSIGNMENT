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

#LOGIC
def isbn_checker(isbn):
    return len(isbn) == 13 and isbn.isdigit()

def can_borrow(book, stock):
    # book is a row: (isbn, title, author, quantity)
    return book is not None and stock > 0 and book[3] >= stock

def calculate_due_date(days=14):
    return (date.today() + timedelta(days=days)).isoformat()

#GUI LOGIC
def handle_add():
    isbn = isbn_entry.get().strip()
    title = title_entry.get().strip()
    author = author_entry.get().strip()
    try:
        quantity = int(quantity_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Quantity must be a whole number.")
        return

    if not isbn_checker(isbn):
        messagebox.showerror("Error", "ISBN must be 13 digits.")
        return
    if not title or not author:
        messagebox.showerror("Error", "Title and author cannot be empty.")
        return

    if add_book(isbn, title, author, quantity):
        messagebox.showinfo("Saved", f"{title} added.")
        refresh_list()
    else:
        messagebox.showerror("Error", "That ISBN already exists.")

def handle_borrow():
    isbn = isbn_entry.get().strip()
    book = search_book(isbn)
    if not can_borrow(book, 1):
        messagebox.showerror("Error", "Unknown ISBN or no copies left.")
        return
    update_book(isbn, -1)
    messagebox.showinfo("Borrowed", f"Borrowed: {book[1]}.")
    refresh_list()

def refresh_list():
    result_box.delete(0, tk.END)
    for isbn, title, author, quantity in get_all_books():
        result_box.insert(tk.END, f"{isbn}  {title}  {author}  (quantity: {quantity})")

# GUI APPLICATION
app = tk.Tk()
app.title("City Central Library Management System")
app.geometry("1100x700")
app.minsize(850, 600)
app.resizable(width=True, height=True)
app.configure(bg="#eeeeee")

tk.Label(app, text="ISBN (13 digits)").grid(row=0, column=0, sticky="w")
isbn_entry = tk.Entry(app)
isbn_entry.grid(row=0, column=1)

tk.Label(app, text="Title").grid(row=1, column=0, sticky="w")
title_entry = tk.Entry(app)
title_entry.grid(row=1, column=1)

tk.Label(app, text="Author").grid(row=2, column=0, sticky="w")
author_entry = tk.Entry(app)
author_entry.grid(row=2, column=1)

tk.Label(app, text="Quantity").grid(row=3, column=0, sticky="w")
quantity_entry = tk.Entry(app)
quantity_entry.grid(row=3, column=1)

tk.Button(app, text="Add book", command=handle_add).grid(row=4, column=0)
tk.Button(app, text="Borrow book", command=handle_borrow).grid(row=4, column=1)

result_box = tk.Listbox(app, width=50)
result_box.grid(row=5, column=0, columnspan=2, pady=10)

refresh_list()
app.mainloop()