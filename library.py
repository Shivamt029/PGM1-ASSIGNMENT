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

#General GUI functions
def clear_screen():
    for widget in content.winfo_children():
        widget.destroy()

def create_button(parent, text, command, color="#174a7e"):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg="white",
        activebackground="#0d345a",
        activeforeground="white",
        font=("Arial", 10, "bold"),
        width=18,
        height=2,
        relief="flat",
        cursor="hand2"
    )

def create_label(parent, text):
    return tk.Label(
        parent,
        text=text,
        bg="white",
        fg="#2222222"
        font=("Arial", 10)
    )

def create_entry(parent):
    return tk.Entry(
        parent,
        font=("Arial", 11),
        relief="solid",
        bd=1
    )

def create_heading(text):
    tk.Label(
        content,
        text=text,
        bg="#eeeeee",
        fg="#174a7e",
        font=("Arial", 19, "bold")
    ).pack(pady=(15, 10))

def back_button():
    create_button(
        content,
        "BACK TO MAIN MENU",
        show_main_menu,
        "#555555"
    ).pack(pady=12)

def create_table(parent, columnns, headings, height=10):
    table = ttk.Treeview(
        parent,
        columns=columnns,
        show="headings",
        height=height
    )    
    for column, heading in zip(columns, headings):
        table.heading(column, text=heading)
        table.column(column, anchor="center", width=120)
    table.pack(fill="both", expand=True, padx=10,  pady=10)
    return table
#Main menu screen
def show_main_menu():
    clear_screen()

    menu_area = tk.Frame(content, bg="#eeeeee")
    menu_area.pack(fill="both", expand=True, padx=20, pady=20)

    menu_area.columnconfigure(0, weight=1)
    menu_area.columnconfigure(1, weight=2)
    menu_area.columnconfigure(2, weight=1)
    menu_area.rowconfigure(0, weight=1)

    #Left menu
    left_menu = tk.Frame(menu_area, bg="#eeeeee")
    left_menu.grid(row=0, column=0, sticky="nsew", padx=10)

    create_button(
        left_menu, "ADD BOOK", show_add_book
    ).pack(fill="x", pady=12)

    create_button(
        left_menu, "BORROW", show_borrow
    ).pack(fill="x", pady=12)

    create_button(
        left_menu, "RETURN", show_return
    ).pack(fill="x", pady=12)

    #Centre area
    centre_area = tk.Frame(
        menu_area,
        bg="white",
        relief="solid",
        bd=1
    )
    centre_area.grid(
        row=0, column=1, sticky="nsew", padx=10, pady=10
    )
    #Right menu
    right_menu = tk.Frame(menu_area, bg="#eeeeee")
    right_menu.grid(row=0, column=2, sticky="nsew", padx=10)

    create_button(
        right_menu, "SEARCH", show_search
    ).pack(fill="x", pady=12)

    create_button(
        right_menu, "LOW STOCK", show_low_stock
    ).pack(fill="x", pady=12)

    create_button(
        right_menu, "ALL BOOKS", show_all_books
    ).pack(fill="x", pady=12)

    #Exit button
    create_button(
        content, "EXIT", exit_application, "#b83232"
    ).pack(pady=(0, 15))

#Add book screen
def show_add_book():
    clear_screen()
    create_heading("ADD NEW BOOK")

    form_area = tk.Frame(content, bg="#eeeeee")
    form_area.pack(fill="both", expand=True)

    form = tk.Frame(form_area, bg="white", padx=25, pady=20)
    form.place(relx=0.5, rely=0.45, anchor="center")

    entries = {}

    fields = [
        ("ISBN (13 digits)", "isbn"),
        ("Book Title", "title"),
        ("Author", "author"),
        ("Quantity", "quantity")
    ]

    for label, key in fields:
        create_label(form, label).pack(anchor="w", pady=(8, 3))
        entry = create_entry(form)
        entry.pack(fill="x", pady=3, ipady=5)
        entries[key] = entry

    def save_book():
        isbn = entries["isbn"].get().strip()
        title = entries["title"].get().strip()
        author = entries["author"].get().strip()
        quantity = entries["quantity"].get().strip()

        if not all([isbn, title, author, quantity]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if not isbn_checker(isbn):
            messagebox.showerror(
                "Error", "ISBN must contain exactly 13 digits."
            )
            return

        if not quantity_checker(quantity):
            messagebox.showerror(
                "Error", "Quantity must be a number greater than zero."
            )
            return

        if add_book(isbn, title, author, int(quantity)):
            messagebox.showinfo("Success", "Book added successfully.")
            for entry in entries.values():
                entry.delete(0, tk.END)
        else:
            messagebox.showerror(
                "Error", "A book with this ISBN already exists."
            )

    create_button(
        form, "SAVE BOOK", save_book, "#238636"
    ).pack(fill="x", pady=15)

    back_button()
#Borrow book screen
def show_borrow():
    clear_screen()
    create_heading("BORROW A BOOK")

    form_area = tk.Frame(content, bg="#eeeeee")
    form_area.pack(fill="both", expand=True)

    form = tk.Frame(form_area, bg="white", padx=25, pady=15)
    form.place(relx=0.5, rely=0.45, anchor="center")

    entries = {}

    fields = [
        ("Book ISBN", "isbn"),
        ("Member Name", "name"),
        ("Member Email", "email"),
        ("Member Phone", "phone")
    ]

    for label, key in fields:
        create_label(form, label).pack(anchor="w", pady=(7, 2))
        entry = create_entry(form)
        entry.pack(fill="x", pady=3, ipady=5)
        entries[key] = entry

    def borrow():
        isbn = entries["isbn"].get().strip()
        name = entries["name"].get().strip()
        email = entries["email"].get().strip()
        phone = entries["phone"].get().strip()

        if not isbn or not name:
            messagebox.showerror(
                "Error", "Book ISBN and member name are required."
            )
            return

        success, message = issue_book(isbn, name, email, phone)

        if success:
            messagebox.showinfo("Success", message)
            for entry in entries.values():
                entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", message)

    create_button(
        form, "ISSUE BOOK", borrow, "#238636"
    ).pack(fill="x", pady=15)

    back_button()
#Return book screen
def show_return():
    clear_screen()
    create_heading("RETURN A BOOK")

    table_area = tk.Frame(content, bg="#eeeeee")
    table_area.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("ID", "Book", "Member", "Issue Date", "Due Date")
    table = create_table(
        table_area,
        columns,
        columns,
        height=8
    )

    for record in get_issued_books():
        table.insert("", tk.END, values=record)

    action_area = tk.Frame(content, bg="white", padx=15, pady=12)
    action_area.pack(fill="x", padx=20, pady=5)

    create_label(action_area, "Borrow ID:").pack(side="left", padx=5)

    borrow_id_entry = create_entry(action_area)
    borrow_id_entry.pack(side="left", padx=5, ipady=4)

    def return_selected():
        borrow_id = borrow_id_entry.get().strip()

        if not borrow_id.isdigit():
            messagebox.showerror(
                "Error", "Please enter a valid Borrow ID."
            )
            return

        success, message = return_book(int(borrow_id))

        if success:
            messagebox.showinfo("Success", message)
            show_return()
        else:
            messagebox.showerror("Error", message)

    create_button(
        action_area, "RETURN BOOK", return_selected, "#238636"
    ).pack(side="left", padx=10)

    back_button()
#Search screen
def show_search():
    clear_screen()
    create_heading("SEARCH BOOKS")

    search_area = tk.Frame(content, bg="white", padx=15, pady=12)
    search_area.pack(fill="x", padx=20, pady=5)

    create_label(
        search_area, "Search by ISBN, title or author:"
    ).pack(side="left", padx=5)

    search_entry = create_entry(search_area)
    search_entry.pack(side="left", fill="x", expand=True, padx=5, ipady=5)

    table_area = tk.Frame(content, bg="#eeeeee")
    table_area.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("ISBN", "Title", "Author", "Quantity")
    table = create_table(
        table_area, columns, columns, height=10
    )

    def perform_search():
        for item in table.get_children():
            table.delete(item)

        keyword = search_entry.get().strip()

        for record in search_books(keyword):
            table.insert("", tk.END, values=record)

    create_button(
        search_area, "SEARCH", perform_search
    ).pack(side="left", padx=5)

    perform_search()
    back_button()

#Low stock screen


#All books screen
def show_all_books():
    clear_screen()
    create_heading("ALL BOOKS")

    table_area = tk.Frame(content, bg="#eeeeee")
    table_area.pack(fill="both", expand=True, padx=15, pady=5)

    columns = ("ISBN", "Title", "Author", "Quantity")
    table = create_table(
        table_area, columns, columns, height=12
    )

    for record in get_all_books():
        table.insert("", tk.END, values=record)

    back_button()

#Exit
app.mainloop()