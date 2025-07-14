from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import os
import cv2
import difflib
from database import herbs_plants, symptom_medicine
import json
from keras.models import load_model
from keras.preprocessing import image
import numpy as np


Window.clearcolor = (0.9, 1, 0.9, 1)

class HerbalApp(BoxLayout):
    def __init__(self, username, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.username = username
        self.search_history = self.load_user_data(username) or []
        self.model = load_model('herb_classifier_model.h5')
        self.model_input_size = (224, 224)

        with self.canvas.before:
            Color(0.8, 1, 0.8, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self.update_rect, pos=self.update_rect)

        # Header layout with icon and label
        self.header_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.15), padding=10)
        
        # Icon Image
        icon = AsyncImage(source="assets/icon.png", size_hint=(None, None), size=(65,65))
        self.header_layout.add_widget(icon)

        # Header Label
        self.header = Label(
            text="[b]Smart Herb[/b]",
            font_size=30,
            markup=True,
            color=(0.1, 0.3, 0.1, 1)
        )
        self.header_layout.add_widget(self.header)

        self.add_widget(self.header_layout)

        self.search_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=10, spacing=10)
        self.search_input = TextInput(hint_text='Enter herb name or symptom...', size_hint=(0.7, 1), font_size=18)
        self.search_button = Button(text='Search', size_hint=(0.3, 1), font_size=18, background_color=(0.2, 0.6, 0.2, 1))
        self.search_button.bind(on_press=self.process_input)
        self.search_layout.add_widget(self.search_input)
        self.search_layout.add_widget(self.search_button)
        self.add_widget(self.search_layout)

        self.upload_button = Button(text="Upload Image", size_hint=(0.5, 0.06), font_size=18, background_color=(0.3, 0.6, 1, 1))
        self.upload_button.bind(on_press=self.open_file_chooser)
        self.add_widget(self.upload_button)

        self.history_button = Button(text="View Search History", size_hint=(0.5, 0.06), font_size=18, background_color=(0.4, 0.4, 0.9, 1))
        self.history_button.bind(on_press=self.show_search_history)
        self.add_widget(self.history_button)

        self.results_scroll = ScrollView(size_hint=(1, 0.55))
        self.results_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=20, spacing=20)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.results_scroll.add_widget(self.results_layout)
        self.add_widget(self.results_scroll)

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos

    def process_input(self, instance):
        user_input = self.search_input.text.strip().lower()
        self.results_layout.clear_widgets()

        if user_input and user_input not in self.search_history:
            self.search_history.append(user_input)
            self.save_user_data(self.username)

        herb_match = next((key for key in herbs_plants if key.lower() == user_input), None)
        if herb_match:
            self.display_herb(herb_match, herbs_plants[herb_match])
            return

        symptom_match = next((key for key in symptom_medicine if key.lower() == user_input), None)
        if symptom_match:
            self.display_medicine(symptom_match, symptom_medicine[symptom_match])
            return

        symptoms = [s.strip() for s in user_input.split("and")]
        matching_herbs = []

        for herb, data in herbs_plants.items():
            herb_symptoms = [s.lower() for s in data.get("symptoms", [])]
            if any(symptom in herb_symptoms for symptom in symptoms):
                matching_herbs.append((herb, data))

        if matching_herbs:
            for herb_name, herb_data in matching_herbs:
                self.display_herb(herb_name, herb_data)
            return

        suggestions = difflib.get_close_matches(user_input, list(herbs_plants.keys()) + list(symptom_medicine.keys()), n=1)
        suggestion_text = f"Did you mean: {suggestions[0]}?" if suggestions else "No matching herb or symptom found."
        popup = Popup(title='No Results', content=Label(text=suggestion_text, font_size=18), size_hint=(0.6, 0.4))
        popup.open()

    def show_search_history(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        if not self.search_history:
            layout.add_widget(Label(text="No search history yet.", font_size=18))
        else:
            for item in reversed(self.search_history[-10:]):
                btn = Button(text=item, size_hint_y=None, height=40)
                btn.bind(on_press=self.search_from_history)
                
                layout.add_widget(btn)

        close_btn = Button(text="Close", size_hint_y=None, height=40, background_color=(1, 0.5, 0.5, 1))
        layout.add_widget(close_btn)

        popup = Popup(title="Search History", content=layout, size_hint=(0.8, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def search_from_history(self, instance):
        self.search_input.text = instance.text
        self.process_input(None)
  
    def save_user_data(self, username):
        data = {}
        if os.path.exists('users.json'):
            with open('users.json', 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = {}
        if username not in data:
            data[username] = {"password": "", "search_history": []}
        data[username]["search_history"] = self.search_history

        with open('users.json', 'w') as file:
            json.dump(data, file, indent=4)

    def load_user_data(self, username):
        """Load search history from users.json."""
        if os.path.exists('users.json'):
            with open('users.json', 'r') as file:
                data = json.load(file)
                return data.get(username, {}).get('search_history', [])
        return []

    def open_file_chooser(self, instance):
        layout = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView()
        layout.add_widget(file_chooser)

        button_layout = BoxLayout(size_hint=(1, 0.2))
        select_button = Button(text="Select")
        cancel_button = Button(text="Cancel")
        popup = Popup(title="Select an Image", content=layout, size_hint=(0.9, 0.9))

        def on_selection(instance):
             selection = file_chooser.selection
             if selection:
                popup.dismiss()
                self.process_uploaded_image(selection[0])

        select_button.bind(on_press=on_selection)
        cancel_button.bind(on_press=lambda instance: popup.dismiss())

        button_layout.add_widget(select_button)
        button_layout.add_widget(cancel_button)
        layout.add_widget(button_layout)
        popup.open()


    def preprocess_image(self, image_path):
        """Preprocess the image to fit the model input requirements."""
        img = image.load_img(image_path, target_size=self.model_input_size)  # Load the image
        img_array = image.img_to_array(img)  # Convert image to array
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        img_array = img_array / 255.0  # Normalize the image
        return img_array

    def process_uploaded_image(self, image_path):
        if not os.path.exists(image_path):
            popup = Popup(title="Error", content=Label(text="File not found!"), size_hint=(0.6, 0.4))
            popup.open()
            return

        self.results_layout.clear_widgets()
        img_array = self.preprocess_image(image_path)

        # Predict the herb using the preprocessed image
        prediction = self.model.predict(img_array)
        predicted_class = np.argmax(prediction, axis=1)[0]

        herb_names = list(herbs_plants.keys())
        if predicted_class < len(herb_names):  # Get the herb name from the class index
            matched_herb = list(herbs_plants.keys())[predicted_class]
            self.display_herb(matched_herb, herbs_plants[matched_herb])

        if matched_herb.lower() not in self.search_history:
            self.search_history.append(matched_herb.lower())
            self.save_user_data(self.username)

        else:
            popup = Popup(title="No Match", content=Label(text="No matching herb found!", font_size=18), size_hint=(0.6, 0.4))
            popup.open()

    def display_herb(self, herb_name, herb_data):
        container = BoxLayout(orientation='vertical', size_hint_y=None, height=650, padding=10, spacing=10)

        img_path = herb_data.get("image", "images/default.jpg")
        if not os.path.exists(img_path):
            img_path = "images/default.jpg"

        herb_img = AsyncImage(source=img_path, size_hint=(None, None), size=(250, 250), allow_stretch=True)
        herb_img_container = AnchorLayout(anchor_x='center')
        herb_img_container.add_widget(herb_img)

        def create_label(text, bold=False):
            return Label(
                text=f"[b]{text}[/b]" if bold else text,
                markup=True,
                font_size=18,
                color=(0.1, 0.2, 0.1, 1),
                size_hint_y=None,
                height=30
            )

        herb_name_label = create_label(herb_name.capitalize(), bold=True)
        sci_name = herb_data.get("scientific_name", "N/A")
        sci_name_label = create_label(f"Scientific Name: {sci_name}")

        benefits = herb_data.get("benefits", "N/A")
        benefits_label = create_label(f"Benefits: {benefits}")

        symptoms = ", ".join(herb_data.get("symptoms", []))
        symptoms_label = create_label(f"Used For: {symptoms if symptoms else 'N/A'}")

        usage = herb_data.get("usage", "N/A")
        usage_label = create_label(f"Usage: {usage}")

        precautions = herb_data.get("precautions", "N/A")
        precautions_label = create_label(f"Precautions: {precautions}")

        container.add_widget(herb_name_label)
        container.add_widget(sci_name_label)
        container.add_widget(herb_img_container)
        container.add_widget(benefits_label)
        container.add_widget(symptoms_label)
        container.add_widget(usage_label)
        container.add_widget(precautions_label)

        self.results_layout.add_widget(container)

    def display_medicine(self, symptom, medicine):
        label = Label(
            text=f"[b]Suggested Medicine for {symptom}:[/b]\n{medicine}",
            markup=True,
            font_size=18,
            size_hint_y=None,
            height=150,
            color=(0.1, 0.2, 0.1, 1)
        )
        self.results_layout.add_widget(label)

class HerbalAppApp(App):
    def build(self):
        return HerbalApp(username="test_user")

if __name__ == '__main__':
    HerbalAppApp().run()
