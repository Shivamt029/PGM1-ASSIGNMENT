import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

#DATABASE
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

def add_book(isbn, title, author, quantity):
    try:
        cursor.execute("INSERT INTO book VALUES (?,?,?)", (isbn, title, author, quantity))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def search_book(isbn):
    cursor.execute("SELECT * FROM book WHERE isbn = ?", (isbn))
    return cursor.fetchone()

def display_book():
    cursor.execute("SELECT * FROM book ORDER BY name")
    return cursor.fetchall()


# GUI APPLICATION
app = tk.Tk()
app.title("City Central Library Management System")
app.geometry("1920x1080")
app.resizable(width=False, height=False)

app.mainloop()