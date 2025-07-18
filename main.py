#!/usr/bin/env python3

"""
state: idle
    andon: yellow
    transition: booth staff hits keyboard
    reTerminal: "waiting for wafer"
state: wafer loaded, waiting for selection
    andon: blue
    reTerminal: user selection dialogue
    transition: atendee hits F key + confirmation
state: running
    andon: green
    reTerminal: running splash screen
        laser cat would be amazing
    then back to idle
state: fault
    andon: red
    reTerminal: BSOD?
"""
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import subprocess
from woodpecker import Woodpecker
from jean import RobotArm

USE_HARDWARE=0
USE_ANDON=1

# NOTE: this connects the andon here right now
if USE_ANDON or USE_HARDWARE:
    print("Connecting to andon")
    from andon import Andon

IMAGE_FILES = ["images/fossf-silicon.png", "images/hackerfab.png", "images/open-sauce.png"]
LASERCAT_FILE = "images/lasercat.jpg"
SELECTION_KEYS = ["a", "s", "d"]
KEY_READY = " "

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Picker")
        self.woodpecker = None
        self.arm = None
        self.andon = None
        self.init_hardware()
        self.images = []
        self.labels = []
        self.selected_index = None
        self.countdown_popup = None
        self.countdown_label = None
        self.countdown_seconds = 5
        self.countdown_running = False
        # Fullscreen kiosk mode
        self.root.attributes('-fullscreen', True)
        self.root.configure(cursor="none")
        self.root.bind("<Key>", self.on_key)
        self.load_images()

        self.state = None
        self.set_state_idle()

    def set_state_idle(self):
        self.state = "IDLE"
        self.create_main_screen()
        self.update_label('Hold please! Waiting for wafer...')
        if self.andon:
            self.andon.set_only_orange()

    def set_state_wait_selection(self):
        self.state = "WAIT_SELECTION"
        self.update_label('LASER UPLINK ESTABLISHED... MAKE YOUR MOVE!')
        if self.andon:
            self.andon.set_only_blue()

    def set_state_running(self):
        self.state = "RUNNING"
        self.update_label('LASER GO BRRR')
        if self.andon:
            self.andon.set_only_green()

    def set_state_error(self):
        self.state = "ERROR"
        self.update_label('Oh noes! Contact booth staff :()')
        if self.andon:
            self.andon.set_only_red()
            # self.andon.set_beeper(1)

    def init_hardware(self):
        if USE_HARDWARE:
            print("Connecting to woodpecker...")
            self.woodpecker = Woodpecker()
            print("Connecting to arm...")
            self.arm = RobotArm()
        if USE_HARDWARE or USE_ANDON:
            # already connected
            self.andon = Andon()

    def load_images(self):
        # Get screen size for dynamic resizing
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # Reserve about 20% for labels/instructions
        img_height = int(screen_height * 0.7)
        img_width = int(screen_width / 3 * 0.9)
        square_dim = min(img_width, img_height)
        self.images = []
        for file in IMAGE_FILES:
            img = Image.open(file)
            img = img.resize((square_dim, square_dim), Image.LANCZOS)
            self.images.append(ImageTk.PhotoImage(img))

    def create_main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.labels = []
        F_LABELS = ["F1", "F2", "F3"]
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # Make the grid expand to fill the screen
        for i in range(3):
            self.root.grid_columnconfigure(i, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        for idx, img in enumerate(self.images):
            label = tk.Label(self.root, image=img)
            label.grid(row=0, column=idx, padx=screen_width//60, pady=screen_height//40, sticky="nsew")
            self.labels.append(label)
            # Add F1, F2, F3 label under each image
            f_label = tk.Label(self.root, text=F_LABELS[idx], font=("Arial", int(screen_height*0.04), "bold"))
            self.instr_label = tk.StringVar()
            instr = tk.Label(self.root, textvariable=self.instr_label, font=("Arial", int(screen_height*0.04)))
            instr.grid(row=2, column=0, columnspan=3, pady=screen_height//40)
            f_label.grid(row=1, column=idx, pady=(0, screen_height//50))
        self.selected_index = None
        self.countdown_running = False

    def update_label(self, text):
        self.instr_label.set(text)
        # self.instr_label.set("test")
        # print(dir(self.instr))
        # self.instr.textvariable = "Waiting for wafer..."

    def on_key(self, event):
        if self.countdown_running:
            if event.keysym == "Escape":
                self.cancel_countdown()
            return
        # Escape in main screen exits fullscreen/app
        if event.keysym == "Escape":
            self.root.attributes('-fullscreen', False)
            self.root.destroy()
            return
        if self.state == "IDLE":
            if event.char == " ":
                self.set_state_wait_selection()
        elif self.state == "WAIT_SELECTION":
            self.selected_index = SELECTION_KEYS.index(event.char)
            self.show_countdown_popup()

    def show_countdown_popup(self):
        self.countdown_running = True
        self.countdown_popup = tk.Toplevel(self.root)
        self.countdown_popup.title("Confirm?")
        # Show the chosen image
        chosen_img = self.images[self.selected_index]
        img_label = tk.Label(self.countdown_popup, image=chosen_img)
        img_label.pack(padx=10, pady=(15, 5))
        # Show the text with the F label
        F_LABELS = ["F1", "F2", "F3"]
        chosen_label_text = f"Press {F_LABELS[self.selected_index]} to confirm, or any other key to cancel."
        chosen_label = tk.Label(self.countdown_popup, text=chosen_label_text, font=("Arial", 20, "bold"))
        chosen_label.pack(pady=(0, 10))
        self.countdown_popup.grab_set()
        self.countdown_popup.bind("<Key>", self.on_confirm_key)


    def update_countdown(self):
        # Countdown logic no longer needed
        pass

    def on_confirm_key(self, event):
        chosen_key = SELECTION_KEYS[self.selected_index]
        if event.char == chosen_key:
            self.set_state_running()
            self.countdown_popup.destroy()
            self.countdown_running = False
            self.countdown_seconds = 5
            self.run_command()
            self.show_sleep_dialog()
        else:
            self.cancel_countdown()

    def show_sleep_dialog(self):
        self.sleep_seconds = 20
        self.sleep_dialog = tk.Toplevel(self.root)
        self.sleep_dialog.title("Please wait")
        # Show a larger lasercat image above the countdown label
        try:
            img = Image.open(LASERCAT_FILE)
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            large_dim = min(600, int(screen_width * 0.6), int(screen_height * 0.6))
            img = img.resize((large_dim, large_dim), Image.LANCZOS)
            self.lasercat_large_photo = ImageTk.PhotoImage(img)
            lasercat_label = tk.Label(self.sleep_dialog, image=self.lasercat_large_photo)
            lasercat_label.pack(padx=10, pady=(20, 10))
        except Exception as e:
            print(f"Could not load or resize lasercat.jpg for large dialog: {e}")
        self.sleep_label = tk.Label(self.sleep_dialog, text=f"INITIATING CYBER RETURN SEQUENCE: {self.sleep_seconds}", font=("Arial", 20, "bold"))
        self.sleep_label.pack(padx=30, pady=30)
        self.sleep_dialog.grab_set()
        self.update_sleep_dialog()

    def update_sleep_dialog(self):
        if self.sleep_seconds > 0:
            self.sleep_label.config(text=f"INITIATING CYBER RETURN SEQUENCE: {self.sleep_seconds}")
            self.sleep_seconds -= 1
            self.root.after(1000, self.update_sleep_dialog)
        else:
            self.close_sleep_dialog()

    def close_sleep_dialog(self):
        self.sleep_dialog.destroy()
        self.set_state_idle()


    def cancel_countdown(self):
        if self.countdown_popup:
            self.countdown_popup.destroy()
        self.countdown_running = False
        self.countdown_seconds = 5
        self.set_state_idle()

    def run_command(self):
        subprocess.Popen(['echo', '"YAAAY!"'])

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
