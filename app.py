import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from backend import DatabaseHandler  
import re  

class BaseForm(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.db = DatabaseHandler()
        self.create_widgets()
        self.resizable(False, False)
        
    def create_widgets(self):
        pass  

class DatePicker(tk.Frame):
    def __init__(self, parent, label_text):
        super().__init__(parent)
        self.label = tk.Label(self, text=label_text)
        self.cal = DateEntry(self, date_pattern='yyyy-mm-dd')
        self.clear_btn = tk.Button(self, text="Clear", command=self.clear_date)
        
        self.label.pack(side=tk.LEFT)
        self.cal.pack(side=tk.LEFT, padx=5)
        self.clear_btn.pack(side=tk.LEFT)

    def get_date(self):
        return self.cal.get_date() or None

    def set_date(self, date_str):
        self.cal.set_date(date_str) if date_str else self.clear_date()

    def clear_date(self):
        self.cal.delete(0, tk.END)

class SearchBar(tk.Frame):
    def __init__(self, parent, search_callback):
        super().__init__(parent)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self, textvariable=self.search_var, width=40)
        self.search_btn = tk.Button(self, text="Search", command=search_callback)
        
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_btn.pack(side=tk.LEFT)
        self.search_var.trace_add("write", lambda *_: search_callback())

class MemberForm(BaseForm):
    def __init__(self, parent, title, member_id=None):
        self.member_id = member_id
        super().__init__(parent, title)
        
    def create_widgets(self):
        self.fields = {}
        labels = ['Full Name', 'First Name', 'Last Name', 'Address', 'Phone Number']
        
        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(self, width=30)
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.fields[label.lower().replace(' ', '_')] = entry

        date_frame = tk.Frame(self)
        date_frame.grid(row=0, column=2, rowspan=3, padx=10, pady=5, sticky='w')

        self.dob_picker = DatePicker(date_frame, "Date of Birth")
        self.dob_picker.pack(anchor='w', pady=5)

        self.joined_picker = DatePicker(date_frame, "Date Joined")
        self.joined_picker.pack(anchor='w', pady=5)

        self.exit_picker = DatePicker(date_frame, "Date Exit")
        self.exit_picker.pack(anchor='w', pady=5)

        self.photo_path = tk.StringVar()
        tk.Label(self, text="Photo").grid(row=5, column=0, padx=10, pady=5, sticky='e')
        tk.Entry(self, textvariable=self.photo_path, width=30).grid(row=5, column=1, padx=10, pady=5)
        tk.Button(self, text="Upload", command=self.upload_photo).grid(row=5, column=2, padx=10, pady=5)

        tk.Button(self, text="Save", command=self.on_save).grid(row=6, column=1, pady=10)
        tk.Button(self, text="Cancel", command=self.destroy).grid(row=6, column=2, pady=10)

        if self.member_id:
            self.load_data()

    def load_data(self):
        member = self.db.get_member(self.member_id)
        if member:
            fields = ['full_name', 'first_name', 'last_name', 'address', 'phone_number']
            for field, value in zip(fields, member[1:6]):
                self.fields[field].insert(0, value)
            
            self.dob_picker.set_date(member[6])
            self.joined_picker.set_date(member[7])
            self.exit_picker.set_date(member[8])
            self.photo_path.set(member[9])

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            self.photo_path.set(file_path)
            self.show_photo_preview(file_path)

    def show_photo_preview(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            preview = tk.Label(self, image=photo)
            preview.image = photo
            preview.grid(row=4, column=2, rowspan=2)
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {str(e)}")

    def validate_form(self):
        data = {
            'full_name': self.fields['full_name'].get(),
            'first_name': self.fields['first_name'].get(),
            'last_name': self.fields['last_name'].get(),
            'address': self.fields['address'].get(),
            'phone_number': self.fields['phone_number'].get(),
            'dob': self.dob_picker.get_date(),
            'date_joined': self.joined_picker.get_date(),
            'date_exit': self.exit_picker.get_date(),
            'photo': self.photo_path.get()
        }

        errors = []
        if not data['full_name'].strip():
            errors.append("Full name is required")
        if not re.match(r'^\+?[0-9\s-]{7,}$', data['phone_number']):
            errors.append("Invalid phone number format")
        if data['date_exit'] and data['date_joined'] > data['date_exit']:
            errors.append("Exit date cannot be before join date")

        return data, errors

    def on_save(self):
        data, errors = self.validate_form()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        if self.db.save_member(data, self.member_id):
            messagebox.showinfo("Success", "Member saved successfully")
            self.destroy()

class AdminView(BaseForm):
    def __init__(self, parent):
        super().__init__(parent, "Administrator View")
        self.selected_member = None

    def create_widgets(self):
        
        self.search_bar = SearchBar(self, self.update_table)
        self.search_bar.grid(row=0, column=0, columnspan=3, pady=10)

       
        columns = ("ID", "Full Name", "First Name", "Last Name")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode='browse')
        self.tree.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

       
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        tk.Button(btn_frame, text="View", command=self.view_member).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.edit_member).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.update_table).pack(side=tk.LEFT, padx=5)

        self.update_table()

    def update_table(self):
        search_term = self.search_bar.search_var.get()
        members = self.db.search_members(search_term)
        
        self.tree.delete(*self.tree.get_children())
        for member in members:
            self.tree.insert('', 'end', values=member)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_member = self.tree.item(selected[0])['values'][0]

    def view_member(self):
        if self.selected_member:
            MemberDetails(self, self.selected_member)

    def edit_member(self):
        if self.selected_member:
            MemberForm(self, "Edit Member", self.selected_member)

class MemberDetails(BaseForm):
    def __init__(self, parent, member_id):
        self.member_id = member_id
        super().__init__(parent, "Member Details")

    def create_widgets(self):
        member = self.db.get_member(self.member_id)
        if not member:
            messagebox.showerror("Error", "Member not found")
            self.destroy()
            return

        labels = ['Full Name', 'First Name', 'Last Name', 'Address', 
                 'Phone Number', 'Date of Birth', 'Date Joined', 'Date Exit']
        
        for i, (label, value) in enumerate(zip(labels, member[1:9])):
            tk.Label(self, text=label+":", font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky='e', padx=10)
            tk.Label(self, text=value or 'N/A').grid(row=i, column=1, sticky='w', padx=10)

        if member[9]:  
            try:
                img = Image.open(member[9])
                img.thumbnail((200, 200))
                photo = ImageTk.PhotoImage(img)
                tk.Label(self, image=photo).grid(row=0, column=2, rowspan=5, padx=10)
                self.photo = photo  
            except:
                pass

        tk.Button(self, text="Close", command=self.destroy).grid(row=8, column=1, pady=10)

class AdminLogin(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Administrator Login")
        self.geometry("300x150")
        self.resizable(False, False)
        self.create_widgets()
        self.grab_set()

    def create_widgets(self):
        tk.Label(self, text="Username:").pack(pady=(10, 0))
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=(0, 10), padx=20, fill='x')

        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=(0, 10), padx=20, fill='x')

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Login", command=self.check_credentials).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def check_credentials(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username == "admin" and password == "admin1234":
            messagebox.showinfo("Login Successful", "Welcome, administrator!")
            self.destroy()
            AdminView(self.parent)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

class MemberManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Member Management System")
        self.geometry("400x300")
        self.db = DatabaseHandler()
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="[Church Name] Member Management", font=("Arial", 16, "bold")).pack(pady=10)

        stats = self.db.get_member_stats()
        member_count = stats[0]
        last_update = stats[1] if stats[1] else "N/A"

        tk.Label(self, text=f"Total Members: {member_count}").pack(pady=5)
        tk.Label(self, text=f"Last Update: {last_update}").pack(pady=5)

        tk.Button(self, text="Add Member", command=self.open_add_form, 
                 width=20, height=2).pack(pady=10)
        tk.Button(self, text="List Members", command=self.open_list_view, 
                 width=20, height=2).pack(pady=10)
        tk.Button(self, text="Admin View", command=self.open_admin_view, 
                 width=20, height=2).pack(pady=10)

    def open_add_form(self):
        MemberForm(self, "Add Member")

    def open_list_view(self):
        list_window = BaseForm(self, "Member List")
        
        columns = ("Full Name", "Date Joined", "Date Exit")
        tree = ttk.Treeview(list_window, columns=columns, show="headings")
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        members = self.db.get_all_members()
        for member in members:
            tree.insert('', 'end', values=member)

    def open_admin_view(self):
        AdminLogin(self)

if __name__ == "__main__":
    app = MemberManagementApp()
    app.mainloop()
