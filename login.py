import json
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.image import Image  # Import Image widget
from main import HerbalApp  # Make sure 'main.py' has HerbalApp class

USER_DATA_FILE = "users.json"

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

USER_CREDENTIALS = load_user_data()

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        with self.canvas.before:
            Color(0.1, 0.5, 0.2, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[0])
        self.bind(size=self.update_rect, pos=self.update_rect)

        layout = BoxLayout(orientation='vertical', spacing=15, padding=[40, 80, 40, 80])

        # Create a horizontal layout for the icon and title
        title_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=60, spacing=10)
        
        # Add icon (you can replace 'icon.png' with the path to your actual image)
        icon = Image(source="assets/icon.png", size_hint=(None, None), size=(60,60))  # Adjust size as needed
        title_layout.add_widget(icon)

        # Title label
        title_label = Label(
            text="[b]Smart Herb[/b]",
            markup=True,
            font_size=32,
            size_hint=(1, None),
            height=60,
            color=(0.9, 1, 0.9, 1),
            halign='center'
        )
        title_layout.add_widget(title_label)

        layout.add_widget(title_layout)

        self.username = TextInput(
            hint_text="Enter Username",
            multiline=False,
            size_hint=(1, None),
            height=50,
            background_color=(1, 1, 1, 0.9),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10],
            font_size=18
        )

        self.password = TextInput(
            hint_text="Enter Password",
            password=True,
            multiline=False,
            size_hint=(1, None),
            height=50,
            background_color=(1, 1, 1, 0.9),
            foreground_color=(0, 0, 0, 1),
            padding=[10, 10],
            font_size=18
        )

        login_button = Button(
            text="Login",
            size_hint=(1, None),
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=18
        )
        login_button.bind(on_press=self.validate_login)

        register_button = Button(
            text="Register",
            size_hint=(1, None),
            height=45,
            background_color=(0.1, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size=18
        )
        register_button.bind(on_press=self.register_user)

        forgot_button = Button(
            text="Forgot Password?",
            size_hint=(1, None),
            height=45,
            background_color=(0.9, 0.8, 0.2, 1),
            color=(1, 1, 1, 0.9),
            font_size=16
        )
        forgot_button.bind(on_press=self.forgot_password)

        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(login_button)
        layout.add_widget(register_button)
        layout.add_widget(forgot_button)

        container = BoxLayout(size_hint=(None, None), size=(340, 460), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        container.add_widget(layout)
        self.add_widget(container)

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

    def validate_login(self, instance):
        username = self.username.text.strip()
        password = self.password.text.strip()

        if username in USER_CREDENTIALS and USER_CREDENTIALS[username]["password"] == password:
            self.manager.get_screen("main").update_username(username)
            self.manager.current = "main"
        else:
            self.show_popup("Login Failed", "Invalid Username or Password")

    def register_user(self, instance):
        username = self.username.text.strip()
        password = self.password.text.strip()

        if username in USER_CREDENTIALS:
            self.show_popup("Registration Failed", "Username already exists.")
        elif not username or not password:
            self.show_popup("Error", "Username and Password cannot be empty.")
        else:
            USER_CREDENTIALS[username] = {"password": password, "search_history": []}
            save_user_data(USER_CREDENTIALS)
            self.show_popup("Success", "User registered successfully!")

    def forgot_password(self, instance):
        username = self.username.text.strip()
        if not username:
            self.show_popup("Input Required", "Please enter your username to retrieve the password.")
        elif username in USER_CREDENTIALS:
            password = USER_CREDENTIALS[username]["password"]
            self.show_popup("Password Found", f"Your password is: [b]{password}[/b]")
        else:
            self.show_popup("User Not Found", "Username does not exist in our records.")

    def show_popup(self, title, message):
        content = Label(text=message, markup=True, font_size=18)
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        popup.open()

class HerbalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.herbal_app = HerbalApp(username="")
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(self.herbal_app)

        logout_button = Button(
            text="Logout",
            size_hint=(None, None),
            width=280,
            height=50,
            background_color=(1, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=16
        )
        logout_button.bind(on_press=self.logout)
        layout.add_widget(logout_button)

        self.add_widget(layout)

    def update_username(self, username):
        self.herbal_app.username = username

    def on_enter(self):
        username = self.manager.get_screen("login").username.text.strip()
        self.herbal_app.username = username

    def logout(self, instance):
        self.herbal_app.username = ""
        self.manager.current = "login"

class HerbalAppMain(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HerbalScreen(name="main"))
        return sm

if __name__ == '__main__':
    HerbalAppMain().run()
