# PGM1 ASSIGNMENT
# Library Management System
A library management system built with Python, Tkinter and SQLite.

## Features

- **Add Book:** Add a book with a 13-digit ISBN, title, author and quantity. Duplicate ISBNs are rejected.
- **Search:** Search by ISBN, title or author.
- **Borrow:** Issue a book to a member. The due date is set to 14 days from issue.
- **Return:** Return a book using its Borrow ID.
- **Low Stock:** Lists books with 2 or fewer copies remaining.
- **All Books:** Lists the full catalogue sorted by title.
- **Exit:** Asks for confirmation before closing.

## Requirements

- Python 3.8 or later
- Pillow (for the logo image)

## Installing Pillow

Open a terminal or command prompt and run:

```
pip install pillow
```

## Setup

1. Put the script and `librarylogo.jpeg` in the same folder.
2. Run the script with Python.

The program creates a `library.db` file in the same folder on first run. All data is stored there.
