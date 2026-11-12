
import json
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window


# ==========================================
# CYBERGRAM FIREBASE CONFIGURATION
# ==========================================

FIREBASE_API_KEY = "AIzaSyD_bMwulXnrTBCXautXHtvKivrg8v3NHFQ"

PROJECT_ID = "cybergram-67"

AUTH_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:"
)

FIRESTORE_URL = (
    "https://firestore.googleapis.com/v1/projects/"
    + PROJECT_ID
    + "/databases/(default)/documents"
)


# ==========================================
# FIREBASE CONNECTION
# ==========================================

def firebase_request(url, data=None, token=None, method=None):

    headers = {
        "Content-Type": "application/json"
    }

    if token:
        headers["Authorization"] = "Bearer " + token

    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method or ("POST" if body else "GET")
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = response.read().decode("utf-8")
            return json.loads(result) if result else {}

    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8")

        try:
            message = json.loads(message)["error"]["message"]
        except Exception:
            pass

        raise Exception(message)


def firebase_auth(action, email, password):

    url = (
        AUTH_URL + action
        + "?key=" + urllib.parse.quote(FIREBASE_API_KEY)
    )

    return firebase_request(
        url,
        {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
    )


def firestore_save(path, fields, token, create_only=False):

    url = FIRESTORE_URL + "/" + path

    if create_only:
        url += "?currentDocument.exists=false"

    return firebase_request(
        url,
        {"fields": fields},
        token=token,
        method="PATCH"
    )


def firestore_get(path, token):

    return firebase_request(
        FIRESTORE_URL + "/" + path,
        token=token
    )


def string_field(value):

    return {"stringValue": str(value)}


def read_field(document, name):

    return (
        document.get("fields", {})
        .get(name, {})
        .get("stringValue", "")
    )


# ==========================================
# CYBERGRAM APP
# ==========================================

class CyberGramApp(App):

    def build(self):

        self.title = "CyberGram"

        self.token = None
        self.user_id = None
        self.email = None
        self.username = None

        Window.clearcolor = (0.05, 0.05, 0.08, 1)

        self.root_layout = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        self.show_login()

        return self.root_layout

    def clear_screen(self):

        self.root_layout.clear_widgets()

    def heading(self, text, size=26):

        return Label(
            text=text,
            font_size=dp(size),
            bold=True,
            color=(0.3, 0.65, 1, 1),
            size_hint_y=None,
            height=dp(55)
        )

    def make_input(self, hint, password=False):

        return TextInput(
            hint_text=hint,
            password=password,
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            padding=[dp(12), dp(12)],
            background_color=(0.14, 0.14, 0.19, 1),
            foreground_color=(1, 1, 1, 1)
        )

    def make_button(self, text, callback):

        button = Button(
            text=text,
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=(0.15, 0.4, 0.95, 1),
            color=(1, 1, 1, 1),
            bold=True
        )

        button.bind(on_release=callback)

        return button

    def make_message(self):

        self.message = Label(
            text="Welcome to CyberGram!",
            size_hint_y=None,
            height=dp(55),
            color=(1, 0.75, 0.3, 1)
        )

        return self.message

    def show_message(self, message):

        self.message.text = message

    # ======================================
    # LOGIN
    # ======================================

    def show_login(self):

        self.clear_screen()

        self.root_layout.add_widget(
            self.heading("CYBERGRAM")
        )

        self.email_input = self.make_input("Email address")
        self.password_input = self.make_input(
            "Password", True
        )

        self.root_layout.add_widget(self.email_input)
        self.root_layout.add_widget(self.password_input)

        self.root_layout.add_widget(
            self.make_button("LOGIN", self.login)
        )

        self.root_layout.add_widget(
            self.make_button(
                "CREATE ACCOUNT",
                self.show_register
            )
        )

        self.root_layout.add_widget(self.make_message())

    # ======================================
    # REGISTRATION
    # ======================================

    def show_register(self, *args):

        self.clear_screen()

        self.root_layout.add_widget(
            self.heading("CREATE ACCOUNT")
        )

        self.email_input = self.make_input("Email address")

        self.password_input = self.make_input(
            "Password (minimum 6 characters)", True
        )

        self.username_input = self.make_input(
            "Choose username"
        )

        self.root_layout.add_widget(self.email_input)
        self.root_layout.add_widget(self.password_input)
        self.root_layout.add_widget(self.username_input)

        self.root_layout.add_widget(
            self.make_button("REGISTER", self.register)
        )

        self.root_layout.add_widget(
            self.make_button(
                "BACK TO LOGIN",
                lambda x: self.show_login()
            )
        )

        self.root_layout.add_widget(self.make_message())

    def register(self, *args):

        email = self.email_input.text.strip().lower()
        password = self.password_input.text
        username = self.username_input.text.strip()

        if not email or not password or not username:
            self.show_message("Fill in all fields.")
            return

        if len(password) < 6:
            self.show_message("Password must be at least 6 characters.")
            return

        if len(username) < 3 or len(username) > 20:
            self.show_message("Username must be 3-20 characters.")
            return

        if not username.replace("_", "").isalnum():
            self.show_message("Invalid username.")
            return

        try:

            self.show_message("Creating account...")

            result = firebase_auth(
                "signUp",
                email,
                password
            )

            self.token = result["idToken"]
            self.user_id = result["localId"]
            self.email = email

            firestore_save(
                "usernames/" + username.lower(),
                {
                    "username": string_field(username),
                    "uid": string_field(self.user_id)
                },
                self.token,
                create_only=True
            )

            firestore_save(
                "profiles/" + self.user_id,
                {
                    "username": string_field(username),
                    "email": string_field(email),
                    "uid": string_field(self.user_id),
                    "createdAt": string_field(str(int(time.time())))
                },
                self.token
            )

            self.username = username

            self.show_home()

        except Exception as error:

            self.show_message("Error: " + str(error))

    # ======================================
    # LOGIN ACCOUNT
    # ======================================

    def login(self, *args):

        email = self.email_input.text.strip().lower()
        password = self.password_input.text

        if not email or not password:
            self.show_message("Enter email and password.")
            return

        try:

            self.show_message("Logging in...")

            result = firebase_auth(
                "signInWithPassword",
                email,
                password
            )

            self.token = result["idToken"]
            self.user_id = result["localId"]
            self.email = email

            profile = firestore_get(
                "profiles/" + self.user_id,
                self.token
            )

            self.username = read_field(profile, "username")

            self.show_home()

        except Exception as error:

            self.show_message("Login error: " + str(error))

    # ======================================
    # HOME
    # ======================================

    def show_home(self):

        self.clear_screen()

        self.root_layout.add_widget(
            self.heading("CYBERGRAM", 28)
        )

        self.root_layout.add_widget(
            Label(
                text="Welcome @" + self.username,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1)
            )
        )

        self.post_input = self.make_input("What's happening?")

        self.root_layout.add_widget(self.post_input)

        self.root_layout.add_widget(
            self.make_button("SHARE POST", self.create_post)
        )

        self.root_layout.add_widget(
            self.make_button("REFRESH FEED", self.load_feed)
        )

        self.root_layout.add_widget(
            self.make_button("LOG OUT", self.logout)
        )

        self.root_layout.add_widget(
            self.heading("YOUR FEED", 21)
        )

        self.feed = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None
        )

        self.feed.bind(minimum_height=self.feed.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.feed)

        self.root_layout.add_widget(scroll)
        self.root_layout.add_widget(self.make_message())

        self.load_feed()

    # ======================================
    # CREATE POST
    # ======================================

    def create_post(self, *args):

        content = self.post_input.text.strip()

        if not content:
            self.show_message("Write something first.")
            return

        if len(content) > 2000:
            self.show_message("Post is too long.")
            return

        try:

            post_id = uuid.uuid4().hex

            firestore_save(
                "posts/" + post_id,
                {
                    "uid": string_field(self.user_id),
                    "username": string_field(self.username),
                    "content": string_field(content),
                    "createdAt": string_field(str(int(time.time())))
                },
                self.token,
                create_only=True
            )

            self.post_input.text = ""

            self.show_message("Post shared!")

            self.load_feed()

        except Exception as error:

            self.show_message("Post error: " + str(error))

    # ======================================
    # LOAD FEED
    # ======================================

    def load_feed(self, *args):

        try:

            result = firestore_get(
                "posts?pageSize=50",
                self.token
            )

            self.feed.clear_widgets()

            documents = result.get("documents", [])

            documents.sort(
                key=lambda item: int(
                    read_field(item, "createdAt") or "0"
                ),
                reverse=True
            )

            if not documents:

                self.feed.add_widget(
                    Label(
                        text="No posts yet!",
                        size_hint_y=None,
                        height=dp(70),
                        color=(1, 1, 1, 1)
                    )
                )

            for document in documents:

                username = read_field(document, "username")
                content = read_field(document, "content")

                self.feed.add_widget(
                    Label(
                        text="@" + username + "\n" + content,
                        size_hint_y=None,
                        height=dp(90),
                        color=(1, 1, 1, 1),
                        halign="left",
                        valign="middle"
                    )
                )

        except Exception as error:

            self.show_message("Feed error: " + str(error))

    # ======================================
    # LOGOUT
    # ======================================

    def logout(self, *args):

        self.token = None
        self.user_id = None
        self.email = None
        self.username = None

        self.show_login()


# ==========================================
# START CYBERGRAM
# ==========================================

if __name__ == "__main__":
    CyberGramApp().run()
