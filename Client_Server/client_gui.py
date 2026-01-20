import tkinter as tk
from tkinter import messagebox, scrolledtext
import client
import threading


class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Chat Client")
        self.root.geometry("600x450")

        # Initialize the backend client
        self.client = client.Client()
        self.active_chat_user = None

        # --- UI Layout ---

        # Left Panel: Online Users
        self.user_panel = tk.Frame(root, width=150, bg="#f0f0f0")
        self.user_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.user_panel, text="Online Users", bg="#f0f0f0", font=('Arial', 10, 'bold')).pack(pady=5)

        self.users_listbox = tk.Listbox(self.user_panel)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_selected)

        self.refresh_btn = tk.Button(self.user_panel, text="Refresh List", command=self.client.get_active_users)
        self.refresh_btn.pack(pady=5)

        # Right Panel: Chat Area
        self.chat_panel = tk.Frame(root)
        self.chat_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(self.chat_panel, state='disabled', wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.entry_frame = tk.Frame(self.chat_panel)
        self.entry_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.msg_entry = tk.Entry(self.entry_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=10)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(self.entry_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT, padx=5, pady=10)

        # Overlay Connection Dialog
        self.show_connection_dialog()

        # Monkey-patch client handlers to update UI
        self.setup_client_callbacks()

    def setup_client_callbacks(self):
        """ Redirects client's background logic to update the GUI safely """
        self.client._handle_user_message = self.ui_handle_message
        self.client._handle_active_users = self.ui_handle_user_list
        self.client._handle_error_message = self.ui_handle_error

    def show_connection_dialog(self):
        self.conn_win = tk.Toplevel(self.root)
        self.conn_win.title("Connect to Server")
        self.conn_win.geometry("300x150")

        tk.Label(self.conn_win, text="Username:").pack(pady=5)
        self.user_entry = tk.Entry(self.conn_win)
        self.user_entry.pack()
        self.user_entry.insert(0, "User1")

        tk.Button(self.conn_win, text="Connect", command=self.perform_connect).pack(pady=20)

    def perform_connect(self):
        username = self.user_entry.get()
        if username:
            self.client.connect('127.0.0.1', 5000, username)
            self.conn_win.destroy()
            self.root.title(f"Chatting as: {username}")
            # Automatically request user list on start
            self.client.get_active_users()

    def on_user_selected(self, event):
        selection = self.users_listbox.curselection()
        if selection:
            self.active_chat_user = self.users_listbox.get(selection[0])
            self.display_local_msg(f"--- Chatting with {self.active_chat_user} ---", color="blue")

    def send_message(self):
        msg = self.msg_entry.get()
        if not self.active_chat_user:
            messagebox.showwarning("Warning", "Please select a user from the list first!")
            return

        if msg:
            self.client.send_msg_to_chat(msg, self.active_chat_user)
            self.display_local_msg(f"You: {msg}")
            self.msg_entry.delete(0, tk.END)

    # --- UI Update Methods (Thread Safe) ---

    def display_local_msg(self, text, color="black"):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, text + "\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.yview(tk.END)

    def ui_handle_message(self, data):
        """ Override for Client._handle_user_message """
        msg = f"{data['SrcUser']}: {data['Content']}"
        self.root.after(0, lambda: self.display_local_msg(msg))

    def ui_handle_user_list(self, data):
        """ Override for Client._handle_active_users """

        def update_list():
            self.users_listbox.delete(0, tk.END)
            for user in data["Content"]:
                if user != self.client.username:  # Don't show self
                    self.users_listbox.insert(tk.END, user)

        self.root.after(0, update_list)

    def ui_handle_error(self, data):
        """ Override for Client._handle_error_message """
        self.root.after(0, lambda: messagebox.showerror("Server Error", data["Content"]))


if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()