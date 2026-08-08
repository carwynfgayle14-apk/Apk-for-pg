"""
Secure Password Generator - Kivy GUI version
Dark themed, touch-friendly UI for Pydroid 3.

Includes: generate passwords, copy to clipboard, and save passwords
with a custom name for later (Use / Copy / Delete). Saved passwords
persist between runs in a "saved_passwords.json" file inside the
app's private data folder (works correctly both in Pydroid 3 and
once packaged into an Android APK).

HOW TO RUN IN PYDROID 3:
1. Open Pydroid 3
2. Tap the menu (☰) -> Pip
3. Search for "kivy" and install it
4. Open this file and press the Play button
"""

import json
import os
import secrets
import string

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.animation import Animation
from kivy.clock import Clock

# Where saved passwords are stored. We use Kivy's App.user_data_dir, which
# points to a proper writable, per-app folder on every platform:
#   - Android: /data/data/<package>/files/app  (private, persists across updates)
#   - Pydroid/desktop: a local user config folder
# This works both in Pydroid 3 and once the app is packaged into an APK,
# unlike a path based on __file__ (which isn't writable inside an APK).
def get_save_file_path():
    app = App.get_running_app()
    if app is not None:
        data_dir = app.user_data_dir
    else:
        # Fallback for edge cases where no App instance exists yet.
        data_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "saved_passwords.json")

Window.clearcolor = (0.07, 0.07, 0.1, 1)

INDIGO = (0.388, 0.4, 0.945, 1)
INDIGO_DARK = (0.31, 0.275, 0.9, 1)
PANEL = (0.14, 0.14, 0.19, 1)
GREEN = (0.2, 0.75, 0.45, 1)
YELLOW = (0.9, 0.7, 0.2, 1)
RED = (0.85, 0.3, 0.3, 1)
GREY_TEXT = (0.65, 0.65, 0.7, 1)


def load_saved_passwords():
    """Load the list of saved {name, password} entries from disk."""
    save_file = get_save_file_path()
    if not os.path.exists(save_file):
        return []
    try:
        with open(save_file, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (ValueError, OSError):
        pass
    return []


def write_saved_passwords(entries):
    """Write the full list of {name, password} entries to disk."""
    save_file = get_save_file_path()
    try:
        with open(save_file, "w") as f:
            json.dump(entries, f, indent=2)
        return True
    except OSError:
        return False


class RoundedBox(BoxLayout):
    """A BoxLayout with a rounded, colored background."""

    def __init__(self, bg=PANEL, radius=16, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class StyledButton(Button):
    """Flat button with rounded corners and a custom color."""

    def __init__(self, bg=INDIGO, radius=14, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.bold = True
        with self.canvas.before:
            self.color_instr = Color(*bg)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_color(self, color):
        self.color_instr.rgba = color


class TypeToggle(ToggleButton):
    """Chip-style toggle for character-type selection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.bold = True
        self.color = (1, 1, 1, 1)
        with self.canvas.before:
            self.color_instr = Color(0.2, 0.2, 0.27, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self._update, size=self._update, state=self._on_state)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def _on_state(self, *args):
        if self.state == "down":
            self.color_instr.rgba = INDIGO
        else:
            self.color_instr.rgba = (0.2, 0.2, 0.27, 1)


class PasswordGeneratorUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 24
        self.spacing = 18

        # ---------- Title ----------
        title = Label(
            text="Password Generator",
            font_size=28,
            bold=True,
            size_hint=(1, 0.09),
            color=(1, 1, 1, 1),
        )
        self.add_widget(title)

        # ---------- Output panel ----------
        output_panel = RoundedBox(bg=PANEL, size_hint=(1, 0.16), padding=16, spacing=6)
        output_panel.orientation = "vertical"

        self.password_label = Label(
            text="Tap Generate to create a password",
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.7),
        )
        self.password_label.bind(size=self._sync_text_size)

        strength_row = BoxLayout(size_hint=(1, 0.3), spacing=8)
        self.strength_label = Label(
            text="", font_size=14, color=GREY_TEXT, size_hint=(0.4, 1), halign="left"
        )
        self.strength_label.bind(size=self._sync_text_size)

        self.strength_bar_bg = RoundedBox(bg=(0.25, 0.25, 0.3, 1), size_hint=(0.6, 1), radius=8)
        self.strength_bar_fill = RoundedBox(bg=RED, size_hint=(0, 1), radius=8)
        self.strength_bar_bg.add_widget(self.strength_bar_fill)

        strength_row.add_widget(self.strength_label)
        strength_row.add_widget(self.strength_bar_bg)

        output_panel.add_widget(self.password_label)
        output_panel.add_widget(strength_row)
        self.add_widget(output_panel)

        # ---------- Copy button ----------
        self.copy_btn = StyledButton(text="Copy to Clipboard", bg=(0.22, 0.22, 0.28, 1), size_hint=(1, 0.08))
        self.copy_btn.bind(on_release=self.copy_password)
        self.add_widget(self.copy_btn)

        # ---------- Save / View saved buttons ----------
        save_row = BoxLayout(size_hint=(1, 0.08), spacing=10)
        self.save_btn = StyledButton(text="Save Password", bg=(0.22, 0.22, 0.28, 1))
        self.save_btn.bind(on_release=self.open_save_popup)
        self.view_saved_btn = StyledButton(text="Saved Passwords", bg=(0.22, 0.22, 0.28, 1))
        self.view_saved_btn.bind(on_release=self.open_saved_list)
        save_row.add_widget(self.save_btn)
        save_row.add_widget(self.view_saved_btn)
        self.add_widget(save_row)

        # ---------- Length slider ----------
        length_panel = RoundedBox(bg=PANEL, size_hint=(1, 0.13), padding=16, orientation="vertical", spacing=4)
        self.length_label = Label(text="Length: 12", font_size=16, bold=True, color=(1, 1, 1, 1), size_hint=(1, 0.4))
        self.length_slider = Slider(min=4, max=32, value=12, step=1, size_hint=(1, 0.6))
        self.length_slider.bind(value=self.on_length_change)
        length_panel.add_widget(self.length_label)
        length_panel.add_widget(self.length_slider)
        self.add_widget(length_panel)

        # ---------- Character type toggles ----------
        types_label = Label(text="Character types", font_size=14, color=GREY_TEXT, size_hint=(1, 0.05), halign="left")
        types_label.bind(size=self._sync_text_size)
        self.add_widget(types_label)

        toggles_grid = GridLayout(cols=2, size_hint=(1, 0.18), spacing=10)
        self.lower_toggle = TypeToggle(text="abc  lowercase", state="down")
        self.upper_toggle = TypeToggle(text="ABC  uppercase", state="down")
        self.digit_toggle = TypeToggle(text="123  numbers", state="down")
        self.symbol_toggle = TypeToggle(text="!@#  symbols", state="normal")
        for t in (self.lower_toggle, self.upper_toggle, self.digit_toggle, self.symbol_toggle):
            toggles_grid.add_widget(t)
        self.add_widget(toggles_grid)

        # ---------- Generate button ----------
        self.generate_btn = StyledButton(text="Generate Password", bg=INDIGO, size_hint=(1, 0.12), font_size=18)
        self.generate_btn.bind(on_release=self.generate_password)
        self.add_widget(self.generate_btn)

        self.error_label = Label(text="", font_size=13, color=RED, size_hint=(1, 0.05))
        self.add_widget(self.error_label)

        self.current_password = ""

    def _sync_text_size(self, instance, value):
        instance.text_size = instance.size

    def on_length_change(self, instance, value):
        self.length_label.text = f"Length: {int(value)}"

    def build_pool(self):
        pool = ""
        required_groups = []
        if self.lower_toggle.state == "down":
            pool += string.ascii_lowercase
            required_groups.append(string.ascii_lowercase)
        if self.upper_toggle.state == "down":
            pool += string.ascii_uppercase
            required_groups.append(string.ascii_uppercase)
        if self.digit_toggle.state == "down":
            pool += string.digits
            required_groups.append(string.digits)
        if self.symbol_toggle.state == "down":
            symbols = "!@#$%^&*()-_=+[]{};:,.<>?/"
            pool += symbols
            required_groups.append(symbols)
        return pool, required_groups

    def generate_password(self, instance):
        pool, required_groups = self.build_pool()
        length = int(self.length_slider.value)

        if not pool:
            self.error_label.text = "Select at least one character type."
            return
        self.error_label.text = ""

        while True:
            password = "".join(secrets.choice(pool) for _ in range(length))
            if all(any(ch in group for ch in password) for group in required_groups):
                break
            if length < len(required_groups):
                break

        self.current_password = password
        self.password_label.text = password
        self.update_strength(length, len(required_groups))

        # little "pop" animation on the output panel for feedback
        anim = Animation(font_size=24, duration=0.08) + Animation(font_size=20, duration=0.12)
        anim.start(self.password_label)

    def update_strength(self, length, groups_used):
        score = groups_used
        if length >= 12:
            score += 1
        if length >= 16:
            score += 1

        if score <= 2:
            label, color, fraction = "Weak", RED, 0.33
        elif score <= 4:
            label, color, fraction = "Good", YELLOW, 0.66
        else:
            label, color, fraction = "Strong", GREEN, 1.0

        self.strength_label.text = label
        self.strength_bar_fill.canvas.before.clear()
        with self.strength_bar_fill.canvas.before:
            Color(*color)
            self.strength_bar_fill.rect = RoundedRectangle(
                pos=self.strength_bar_fill.pos, size=self.strength_bar_fill.size, radius=[8]
            )
        Animation(size_hint_x=fraction, duration=0.3).start(self.strength_bar_fill)

    def copy_password(self, instance):
        if self.current_password:
            Clipboard.copy(self.current_password)
            original = self.copy_btn.text
            self.copy_btn.text = "Copied!"

            def reset_text(dt):
                self.copy_btn.text = original

            Clock.schedule_once(reset_text, 1)

    # ---------- Save a named password ----------
    def open_save_popup(self, instance):
        if not self.current_password:
            self.error_label.text = "Generate a password first."
            return
        self.error_label.text = ""

        content = BoxLayout(orientation="vertical", padding=16, spacing=12)

        preview = Label(
            text=f"Saving:\n{self.current_password}",
            font_size=16,
            color=(1, 1, 1, 1),
            size_hint=(1, 0.35),
        )
        preview.bind(size=self._sync_text_size)

        name_input = TextInput(
            hint_text="Name this password (e.g. Email, Bank)",
            multiline=False,
            size_hint=(1, 0.25),
            font_size=16,
        )

        status_label = Label(text="", font_size=13, color=RED, size_hint=(1, 0.15))

        btn_row = BoxLayout(size_hint=(1, 0.25), spacing=10)
        cancel_btn = StyledButton(text="Cancel", bg=(0.3, 0.3, 0.35, 1))
        confirm_btn = StyledButton(text="Save", bg=GREEN)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)

        content.add_widget(preview)
        content.add_widget(name_input)
        content.add_widget(status_label)
        content.add_widget(btn_row)

        popup = Popup(
            title="Save Password",
            content=content,
            size_hint=(0.9, 0.55),
            background_color=(0.1, 0.1, 0.14, 1),
        )

        def do_save(_):
            name = name_input.text.strip()
            if not name:
                status_label.text = "Please enter a name."
                return
            entries = load_saved_passwords()
            entries.append({"name": name, "password": self.current_password})
            if write_saved_passwords(entries):
                popup.dismiss()
            else:
                status_label.text = "Could not save to file."

        confirm_btn.bind(on_release=do_save)
        cancel_btn.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    # ---------- Browse saved passwords ----------
    def open_saved_list(self, instance):
        entries = load_saved_passwords()

        outer = BoxLayout(orientation="vertical", padding=16, spacing=10)

        popup = Popup(
            title="Saved Passwords",
            content=outer,
            size_hint=(0.92, 0.8),
            background_color=(0.1, 0.1, 0.14, 1),
        )

        if not entries:
            outer.add_widget(Label(text="No saved passwords yet.", color=GREY_TEXT))
            close_btn = StyledButton(text="Close", bg=(0.3, 0.3, 0.35, 1), size_hint=(1, 0.15))
            close_btn.bind(on_release=lambda *_: popup.dismiss())
            outer.add_widget(close_btn)
            popup.open()
            return

        scroll = ScrollView(size_hint=(1, 0.85))
        entry_list = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=4)
        entry_list.bind(minimum_height=entry_list.setter("height"))

        def refresh(_=None):
            entry_list.clear_widgets()
            current_entries = load_saved_passwords()
            for idx, entry in enumerate(current_entries):
                row = RoundedBox(bg=PANEL, size_hint=(1, None), height=110, padding=12, spacing=4)
                row.orientation = "vertical"

                name_lbl = Label(
                    text=entry.get("name", "Unnamed"),
                    font_size=16,
                    bold=True,
                    color=(1, 1, 1, 1),
                    size_hint=(1, 0.4),
                    halign="left",
                )
                name_lbl.bind(size=self._sync_text_size)

                pw_lbl = Label(
                    text=entry.get("password", ""),
                    font_size=14,
                    color=GREY_TEXT,
                    size_hint=(1, 0.3),
                    halign="left",
                )
                pw_lbl.bind(size=self._sync_text_size)

                btn_row = BoxLayout(size_hint=(1, 0.3), spacing=8)
                use_btn = StyledButton(text="Use", bg=INDIGO)
                copy_btn = StyledButton(text="Copy", bg=(0.22, 0.22, 0.28, 1))
                delete_btn = StyledButton(text="Delete", bg=RED)

                def make_use(pw=entry.get("password", "")):
                    def _use(*_a):
                        self.current_password = pw
                        self.password_label.text = pw
                        popup.dismiss()
                    return _use

                def make_copy(pw=entry.get("password", ""), btn=copy_btn):
                    def _copy(*_a):
                        Clipboard.copy(pw)
                        original = btn.text
                        btn.text = "Copied!"
                        Clock.schedule_once(lambda dt: setattr(btn, "text", original), 1)
                    return _copy

                def make_delete(i=idx):
                    def _delete(*_a):
                        current = load_saved_passwords()
                        if 0 <= i < len(current):
                            current.pop(i)
                            write_saved_passwords(current)
                        refresh()
                    return _delete

                use_btn.bind(on_release=make_use())
                copy_btn.bind(on_release=make_copy())
                delete_btn.bind(on_release=make_delete())

                btn_row.add_widget(use_btn)
                btn_row.add_widget(copy_btn)
                btn_row.add_widget(delete_btn)

                row.add_widget(name_lbl)
                row.add_widget(pw_lbl)
                row.add_widget(btn_row)
                entry_list.add_widget(row)

        refresh()
        scroll.add_widget(entry_list)
        outer.add_widget(scroll)

        close_btn = StyledButton(text="Close", bg=(0.3, 0.3, 0.35, 1), size_hint=(1, 0.1))
        close_btn.bind(on_release=lambda *_: popup.dismiss())
        outer.add_widget(close_btn)

        popup.open()


class PasswordGeneratorApp(App):
    def build(self):
        return PasswordGeneratorUI()


if __name__ == "__main__":
    PasswordGeneratorApp().run()
