import sqlite3
from tkinter import messagebox

class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect('members.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS member (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        full_name TEXT NOT NULL,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        address TEXT NOT NULL,
                        phone_number TEXT NOT NULL,
                        dob TEXT NOT NULL,
                        date_joined TEXT NOT NULL,
                        date_exit TEXT,
                        photo TEXT)''')
        self.conn.commit()

    def get_member(self, member_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM member WHERE id = ?", (member_id,))
        return cursor.fetchone()

    def search_members(self, search_term=None):
        cursor = self.conn.cursor()
        if search_term:
            cursor.execute("""SELECT id, full_name, first_name, last_name 
                            FROM member 
                            WHERE full_name LIKE ?""", (f'%{search_term}%',))
        else:
            cursor.execute("SELECT id, full_name, first_name, last_name FROM member")
        return cursor.fetchall()

    def get_all_members(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT full_name, date_joined, date_exit FROM member")
        return cursor.fetchall()

    def save_member(self, data, member_id=None):
        try:
            cursor = self.conn.cursor()
            if member_id:  
                cursor.execute("""UPDATE member SET
                                full_name=?, first_name=?, last_name=?, 
                                address=?, phone_number=?, dob=?, 
                                date_joined=?, date_exit=?, photo=?
                                WHERE id=?""", 
                             (*data.values(), member_id))
            else:  
                cursor.execute("""INSERT INTO member 
                                (full_name, first_name, last_name, address, 
                                phone_number, dob, date_joined, date_exit, photo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                             tuple(data.values()))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
            return False

    def get_member_stats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*), MAX(date_joined) FROM member")
        return cursor.fetchone()
