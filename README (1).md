# Personal Expense Tracker

A Python desktop application (Tkinter + SQLite) for recording and reviewing everyday spending.
Built as an academic mini project for *Programming with Python* at Marwadi University, Rajkot.

> **Academic prototype.** Not an accounting tool and not financial advice.

## Features
- Add, view, update and delete expenses
- Search by title or notes; filter by category and month (YYYY-MM)
- Dashboard: total spent, this month's spend, number of transactions, top category
- Category-wise summary window
- Input validation (title, amount greater than 0, date format, category, payment mode)
- Export records to CSV

## Requirements
- Python 3 (Tkinter is included with the standard Windows installation)
- No extra packages needed

## How to run
```
py expense_tracker.py
```
The database file `expenses.db` is created automatically in the same folder.

## Tech
Python, Tkinter/ttk, SQLite3, csv

## Author
Vartika Sahu - B.Tech CSE, Marwadi University
