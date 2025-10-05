frfrom kivy.lang import Builder
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.snackbar import Snackbar
import sqlite3

KV = """
ScreenManager:
    LoginScreen:
    RegisterScreen:
    HomeScreen:
    CreateEventScreen:
    CommentScreen:

<LoginScreen@Screen>:
    name: "login"
    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(20)
        padding: dp(20)
        MDLabel:
            text: "Login"
            halign: "center"
            font_style: "H4"
        MDTextField:
            id: username
            hint_text: "Username"
        MDTextField:
            id: password
            hint_text: "Password"
            password: True
        MDRaisedButton:
            text: "Login"
            on_release: app.login(username.text, password.text)
        MDFlatButton:
            text: "No account? Register"
            on_release: app.root.current = "register"

<RegisterScreen@Screen>:
    name: "register"
    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(20)
        padding: dp(20)
        MDLabel:
            text: "Register"
            halign: "center"
            font_style: "H4"
        MDTextField:
            id: new_user
            hint_text: "Choose username"
        MDTextField:
            id: new_pass
            hint_text: "Choose password"
            password: True
        MDTextField:
            id: role
            hint_text: "Role (owner / planner / member)"
        MDRaisedButton:
            text: "Register"
            on_release: app.register(new_user.text, new_pass.text, role.text)
        MDFlatButton:
            text: "Back to Login"
            on_release: app.root.current = "login"

<HomeScreen@Screen>:
    name: "home"
    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(10)
        padding: dp(10)

        MDLabel:
            text: "Family Events"
            halign: "center"
            font_style: "H5"

        ScrollView:
            MDList:
                id: event_list

        MDBoxLayout:
            size_hint_y: None
            height: dp(60)
            spacing: dp(10)

            MDRaisedButton:
                text: "Create Event"
                on_release: app.check_create_event()
            MDRaisedButton:
                text: "Logout"
                on_release: app.logout()

<CreateEventScreen@Screen>:
    name: "create_event"
    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(10)
        padding: dp(20)

        MDLabel:
            text: "Create Event"
            halign: "center"
            font_style: "H5"

        MDTextField:
            id: event_title
            hint_text: "Event Title"

        MDTextField:
            id: event_date
            hint_text: "Date (YYYY-MM-DD)"

        MDTextField:
            id: event_location
            hint_text: "Location"

        MDRaisedButton:
            text: "Save Event"
            on_release: app.save_event(event_title.text, event_date.text, event_location.text)
        MDFlatButton:
            text: "Back"
            on_release: app.root.current = "home"

<CommentScreen@Screen>:
    name: "comment"
    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(10)
        padding: dp(20)

        MDLabel:
            id: event_label
            text: "Comments for Event"
            halign: "center"
            font_style: "H5"

        ScrollView:
            MDList:
                id: comment_list

        MDTextField:
            id: comment_input
            hint_text: "Write a comment..."

        MDRaisedButton:
            text: "Post Comment"
            on_release: app.post_comment(comment_input.text)
        MDFlatButton:
            text: "Back"
            on_release: app.root.current = "home"
"""

class FamilyApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Yellow"

        # init db
        self.conn = sqlite3.connect("family.db")
        self.c = self.conn.cursor()
        self.c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
        self.c.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, title TEXT, date TEXT, location TEXT)")
        self.c.execute("CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, event_id INTEGER, user TEXT, comment TEXT)")
        self.conn.commit()

        self.current_user = None
        self.current_event_id = None

        return Builder.load_string(KV)

    # ---------- USER SYSTEM ----------
    def login(self, username, password):
        self.c.execute("SELECT id, role FROM users WHERE username=? AND password=?", (username, password))
        user = self.c.fetchone()
        if user:
            self.current_user = {"id": user[0], "username": username, "role": user[1]}
            self.root.current = "home"
            self.load_events()
            Snackbar(text=f"Welcome {username} ({user[1]})").open()
        else:
            Snackbar(text="Wrong username or password").open()

    def register(self, username, password, role):
        role = role.lower()
        # limits
        if role == "owner":
            self.c.execute("SELECT COUNT(*) FROM users WHERE role='owner'")
            if self.c.fetchone()[0] >= 1:
                Snackbar(text="Owner already exists").open()
                return
        if role == "planner":
            self.c.execute("SELECT COUNT(*) FROM users WHERE role='planner'")
            if self.c.fetchone()[0] >= 3:
                Snackbar(text="Max 3 planners allowed").open()
                return
        # register
        self.c.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)", (username, password, role))
        self.conn.commit()
        Snackbar(text="Registration successful!").open()
        self.root.current = "login"

    def logout(self):
        self.current_user = None
        self.root.current = "login"

    # ---------- EVENTS ----------
    def check_create_event(self):
        if self.current_user["role"] in ["owner", "planner"]:
            self.root.current = "create_event"
        else:
            Snackbar(text="Only owner/planners can create events").open()

    def save_event(self, title, date, location):
        if title.strip() == "" or date.strip() == "" or location.strip() == "":
            Snackbar(text="Please fill all fields").open()
            return
        self.c.execute("INSERT INTO events(title,date,location) VALUES (?,?,?)", (title, date, location))
        self.conn.commit()
        Snackbar(text="Event created!").open()
        self.root.current = "home"
        self.load_events()

    def load_events(self):
        event_list = self.root.get_screen("home").ids.event_list
        event_list.clear_widgets()
        self.c.execute("SELECT id,title,date,location FROM events")
        for row in self.c.fetchall():
            from kivymd.uix.list import OneLineListItem
            item = OneLineListItem(text=f\"{row[1]} — {row[2]} @ {row[3]}\")
            item.bind(on_release=lambda x, event_id=row[0]: self.open_comments(event_id))
            event_list.add_widget(item)

    # ---------- COMMENTS ----------
    def open_comments(self, event_id):
        self.current_event_id = event_id
        screen = self.root.get_screen("comment")
        # update label
        self.c.execute("SELECT title FROM events WHERE id=?", (event_id,))
        title = self.c.fetchone()[0]
        screen.ids.event_label.text = f"Comments for {title}"
        # load comments
        self.load_comments()
        self.root.current = "comment"

    def load_comments(self):
        comment_list = self.root.get_screen("comment").ids.comment_list
        comment_list.clear_widgets()
        self.c.execute("SELECT user,comment FROM comments WHERE event_id=?", (self.current_event_id,))
        from kivymd.uix.list import OneLineListItem
        for row in self.c.fetchall():
            comment_list.add_widget(OneLineListItem(text=f\"{row[0]}: {row[1]}\"))

    def post_comment(self, text):
        if not text.strip():
            return
        self.c.execute("INSERT INTO comments(event_id,user,comment) VALUES (?,?,?)",
                       (self.current_event_id, self.current_user["username"], text))
        self.conn.commit()
        self.load_comments()
        self.root.get_screen("comment").ids.comment_input.text = ""

