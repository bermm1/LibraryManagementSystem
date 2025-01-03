import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector
from tkinter import ttk


def connect_db():
    conn = mysql.connector.connect(
        host="localhost", user="root", password="b3rm", database="library_db"
    )
    return conn

def check_login():
    username = username_entry.get()
    password = password_entry.get()
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    if user:
        show_main_window(user[0])
    else:
        messagebox.showerror("Error", "Invalid login")
    conn.close()

def register_user():
    username = register_username_entry.get()
    password = register_password_entry.get()
    confirm_password = register_confirm_password_entry.get()
    email = register_email_entry.get()

    if password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match.")
        return

    if username and password and email:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, password))
        conn.commit()
        messagebox.showinfo("Success", "Registration successful!")
        show_login_form()
        conn.close()
    else:
        messagebox.showerror("Error", "Please fill in all fields.")


def show_login_form():
    register_frame.pack_forget()
    main_frame.pack_forget()
    login_frame.pack(fill=tk.BOTH, expand=True)

def show_register_form():
    login_frame.pack_forget()
    main_frame.pack_forget()
    register_frame.pack(fill=tk.BOTH, expand=True)

def show_main_window(user_id):
    global current_user_id
    current_user_id = user_id
    login_frame.pack_forget()
    register_frame.pack_forget()
    main_frame.pack(fill=tk.BOTH, expand=True)
    update_available_listbox()
    update_borrowed_listbox()


def fetch_available_books(search_query=None):
    conn = connect_db()
    cursor = conn.cursor()
    if search_query:
        cursor.execute(
            "SELECT book_id, title, copies, status FROM books WHERE title LIKE %s",
            (f"%{search_query}%",)
        )
    else:
        cursor.execute("SELECT book_id, title, copies, status FROM books")
    books = cursor.fetchall()
    conn.close()
    return books


def fetch_borrowed_books(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT books.book_id, books.title FROM books "
        "JOIN transactions ON books.book_id = transactions.book_id "
        "WHERE transactions.user_id=%s AND transactions.return_date IS NULL",
        (user_id,)
    )
    books = cursor.fetchall()
    conn.close()
    return books


def update_available_listbox(search_query=None):
    available_books = fetch_available_books(search_query)
    available_listbox.delete(0, tk.END)
    for book in available_books:
        available_listbox.insert(tk.END, f"{book[0]} - {book[1]}")


def update_borrowed_listbox():
    borrowed_books = fetch_borrowed_books(current_user_id)
    borrowed_listbox.delete(0, tk.END)
    for book in borrowed_books:
        borrowed_listbox.insert(tk.END, f"{book[0]} - {book[1]}")


def borrow_book():
    selected = available_listbox.get(tk.ACTIVE)
    if not selected:
        messagebox.showerror("Error", "No book selected!")
        return
    book_id = selected.split(" - ")[0]
    
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT copies FROM books WHERE book_id=%s", (book_id,))
    result = cursor.fetchone()
    if result and result[0] > 0:
        cursor.execute("UPDATE books SET copies = copies - 1 WHERE book_id=%s", (book_id,))
        
        cursor.execute("SELECT copies FROM books WHERE book_id=%s", (book_id,))
        available_copies = cursor.fetchone()[0]
        if available_copies == 0:
            cursor.execute("UPDATE books SET status='Not Available' WHERE book_id=%s", (book_id,))
        
        cursor.execute(
            "INSERT INTO transactions (user_id, book_id, borrow_date) VALUES (%s, %s, NOW())",
            (current_user_id, book_id)
        )
        conn.commit()
        messagebox.showinfo("Success", "Book borrowed successfully!")
        update_available_listbox()
        update_borrowed_listbox()
    else:
        messagebox.showerror("Error", "No copies available for this book.")
    
    conn.close()


def return_book():
    selected = borrowed_listbox.get(tk.ACTIVE)
    if not selected:
        messagebox.showerror("Error", "No book selected!")
        return
    
    book_id = selected.split(" - ")[0]
    
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT transaction_id FROM transactions WHERE user_id=%s AND book_id=%s AND return_date IS NULL LIMIT 1",
        (current_user_id, book_id)
    )
    transaction = cursor.fetchone()
    
    if not transaction:
        messagebox.showerror("Error", "No borrowed copy of this book to return!")
        conn.close()
        return
    
    transaction_id = transaction[0]

    cursor.execute("UPDATE books SET copies = copies + 1 WHERE book_id=%s", (book_id,))

    cursor.execute("SELECT copies FROM books WHERE book_id=%s", (book_id,))
    available_copies = cursor.fetchone()[0]
    if available_copies > 0:
        cursor.execute("UPDATE books SET status='Available' WHERE book_id=%s", (book_id,))
    
    cursor.execute(
        "UPDATE transactions SET return_date=NOW() WHERE transaction_id=%s",
        (transaction_id,)
    )

    conn.commit()
    messagebox.showinfo("Success", "Book returned successfully!")
    
    update_available_listbox()
    update_borrowed_listbox()

    conn.close()

def search_books():
    search_query = search_entry.get().strip()
    update_available_listbox(search_query)

def set_background(frame, image_path):
    img = Image.open(image_path)
    img = img.resize((600, 400), Image.LANCZOS)  
    img = ImageTk.PhotoImage(img)
    
    background = tk.Canvas(frame, width=600, height=400, highlightthickness=0)
    background.place(x=0, y=0, relwidth=1, relheight=1)
    background.create_image(0, 0, image=img, anchor=tk.NW)
    
    frame.background_image = img  # Store the image in the frame to prevent garbage collection

    return background

def toggle_password(entry, eye_label, visibility_state):
    if visibility_state[0]:
        entry.config(show="*")  
        eye_label.config(image=eye_closed)  
    else:
        entry.config(show="")  
        eye_label.config(image=eye_open)  

    visibility_state[0] = not visibility_state[0]


root = tk.Tk()
root.title("Library Management System")
root.geometry("600x400")
root.resizable(False, False)

eye_open = ImageTk.PhotoImage(Image.open("eye.png").resize((16, 16)))
eye_closed = ImageTk.PhotoImage(Image.open("hidden.png").resize((16, 16)))

login_frame = tk.Frame(root)
register_frame = tk.Frame(root)
main_frame = tk.Frame(root)

set_background(login_frame, "bckgrnd.png")
set_background(register_frame, "bckgrnd.png")
set_background(main_frame, "main.png")

title_label = tk.Label(login_frame, text="Login", font=("Arial", 24, "bold"), fg="black")
title_label.place(x=250, y=50)

tk.Label(login_frame, text="Username", font=("Arial", 10), bg="black", fg="white").place(x=150, y=150)
username_entry = tk.Entry(login_frame, width=30)
username_entry.place(x=230, y=150, width=200)

tk.Label(login_frame, text="Password", font=("Arial", 10), bg="black", fg="white").place(x=150, y=200)
password_entry = tk.Entry(login_frame, show="*", width=30)
password_entry.place(x=230, y=200, width=200)

password_visible = [False] 
eye_icon_label = tk.Label(login_frame, image=eye_closed, bg="white", cursor="hand2")
eye_icon_label.place(x=435, y=200)
eye_icon_label.bind("<Button-1>", lambda e: toggle_password(password_entry, eye_icon_label, password_visible))

login_button = tk.Button(login_frame, text="Login", font=("Arial", 10), bg="green", fg="white", command=check_login)
login_button.place(x=250, y=260, width=100)

register_button = tk.Button(login_frame, text="Register", font=("Arial", 10), bg="blue", fg="white", command=show_register_form)
register_button.place(x=250, y=300, width=100)


title_label = tk.Label(register_frame, text="Register", font=("Arial", 24, "bold"), fg="black")
title_label.place(x=250, y=40)

tk.Label(register_frame, text="Username", font=("Arial", 10), bg="black", fg="white").place(x=150, y=120)
register_username_entry = tk.Entry(register_frame, width=30)
register_username_entry.place(x=230, y=120, width=200)

tk.Label(register_frame, text="Email", font=("Arial", 10), bg="black", fg="white").place(x=170, y=160)
register_email_entry = tk.Entry(register_frame, width=30)
register_email_entry.place(x=230, y=160, width=200)

tk.Label(register_frame, text="Password", font=("Arial", 10), bg="black", fg="white").place(x=150, y=200)
register_password_entry = tk.Entry(register_frame, show="*", width=30)
register_password_entry.place(x=230, y=200, width=200)

register_password_visible = [False]  
eye_icon_label_pass = tk.Label(register_frame, image=eye_closed, bg="white", cursor="hand2")
eye_icon_label_pass.place(x=435, y=200)
eye_icon_label_pass.bind("<Button-1>", lambda e: toggle_password(register_password_entry, eye_icon_label_pass, register_password_visible))

tk.Label(register_frame, text="Confirm Password", font=("Arial", 10), bg="black", fg="white").place(x=100, y=240)
register_confirm_password_entry = tk.Entry(register_frame, show="*", width=30)
register_confirm_password_entry.place(x=230, y=240, width=200)

register_confirm_password_visible = [False]  
eye_icon_label_confirm = tk.Label(register_frame, image=eye_closed, bg="white", cursor="hand2")
eye_icon_label_confirm.place(x=435, y=240)
eye_icon_label_confirm.bind("<Button-1>", lambda e: toggle_password(register_confirm_password_entry, eye_icon_label_confirm, register_confirm_password_visible))

register_submit_button = tk.Button(register_frame, text="Register", font=("Arial", 10), bg="green", fg="white", command=register_user)
register_submit_button.place(x=250, y=300, width=100)

back_to_login_button = tk.Button(register_frame, text="Back to Login", font=("Arial", 10), bg="blue", fg="white", command=show_login_form)
back_to_login_button.place(x=250, y=340, width=100)


search_frame = tk.Frame(main_frame)
search_frame.grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(search_frame, text="Title:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
search_entry = tk.Entry(search_frame, width=40)
search_entry.pack(side=tk.LEFT, padx=5)
search_button = tk.Button(search_frame, text="Search", font=("Arial", 10), command=search_books)
search_button.pack(side=tk.LEFT, padx=5)

tk.Label(main_frame, text="Available Books", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=10)

available_frame = tk.Frame(main_frame)
available_frame.grid(row=2, column=0, padx=10, pady=10)

available_scrollbar = tk.Scrollbar(available_frame)
available_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

available_listbox = tk.Listbox(available_frame, height=10, width=40, background="skyblue", yscrollcommand=available_scrollbar.set)
available_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

available_scrollbar.config(command=available_listbox.yview)


tk.Label(main_frame, text="Your Borrowed Books", font=("Arial", 10)).grid(row=1, column=1, padx=10, pady=10)

borrowed_frame = tk.Frame(main_frame)
borrowed_frame.grid(row=2, column=1, padx=10, pady=10)

borrowed_scrollbar = tk.Scrollbar(borrowed_frame)
borrowed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

borrowed_listbox = tk.Listbox(borrowed_frame, height=10, width=40, background="pink", yscrollcommand=borrowed_scrollbar.set)
borrowed_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

borrowed_scrollbar.config(command=borrowed_listbox.yview)


borrow_button = tk.Button(main_frame, text="Borrow", font=("Arial", 10), bg="purple", fg="white", command=borrow_book)
borrow_button.grid(row=3, column=0, pady=10)

return_button = tk.Button(main_frame, text="Return", font=("Arial", 10), bg="purple", fg="white", command=return_book)
return_button.grid(row=3, column=1, pady=10)

logout_button = tk.Button(main_frame, text="Logout", font=("Arial", 10), bg="red", fg="white", command=show_login_form)
logout_button.grid(row=4, column=0, columnspan=2, pady=10)

show_login_form()

root.mainloop()