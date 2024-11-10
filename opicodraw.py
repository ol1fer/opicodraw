import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import pystray
from pystray import MenuItem as item
import keyboard
import pyautogui
import threading
import win32clipboard
from io import BytesIO
import os
import sys
import json

import ctypes  # Import ctypes for modifying window styles

if sys.platform == 'win32':
    from ctypes import windll

class OpicoDrawApp:
    def __init__(self, root):
        self.root = root
        self.config_path = os.path.join(os.getenv("APPDATA"), "opicodraw")
        self.config_file = os.path.join(self.config_path, "config.json")
        self.load_config()

        # Load the icon image
        self.icon_image = self.load_icon("opicodraw.ico")  # Replace with your icon filename

        # Remove setting the icon on the root window to prevent flashing
        # root.iconphoto(False, self.icon_image)

        self.drawing_window = None
        self.settings_window = None
        self.mini_settings_window = None
        self.is_window_open = False
        self.hotkey_id = None  # Track hotkey ID

        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 128

        # Set default if not loaded from config
        if not hasattr(self, 'render_canvas_brushstroke'):
            self.render_canvas_brushstroke = True

        # Initialize tray_icon_updater_id
        self.tray_icon_updater_id = None

        # Create the tray icon before starting the update loop
        self.create_tray_icon()

        # Apply the hotkey
        self.apply_hotkey()

    def load_icon(self, icon_filename):
        # Load the icon image for windows
        try:
            icon_path = self.resource_path(icon_filename)
        except Exception:
            icon_path = icon_filename
        return ImageTk.PhotoImage(file=icon_path)

    def load_tray_icon(self, icon_filename):
        # Load the tray icon image
        try:
            icon_path = self.resource_path(icon_filename)
        except Exception:
            icon_path = icon_filename
        return Image.open(icon_path)

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)

    def load_config(self):
        default_pictures_folder = os.path.join(os.getenv('USERPROFILE'), 'Pictures')
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)

        # Set default values
        self.window_width = 600
        self.window_height = 300
        self.pen_width = 4
        self.smoothing_factor = 10
        self.pen_color = "#000000"
        self.auto_copy_on_close = True
        self.hotkey = "alt+shift+q"
        self.last_save_dir = default_pictures_folder
        self.render_canvas_brushstroke = True

        if not os.path.exists(self.config_file) or os.stat(self.config_file).st_size == 0:
            # Config file is missing or empty, create one with default settings
            self.save_config()
        else:
            try:
                with open(self.config_file, "r") as file:
                    config = json.load(file)
                    self.window_width = config.get("window_width", self.window_width)
                    self.window_height = config.get("window_height", self.window_height)
                    self.pen_width = config.get("pen_width", self.pen_width)
                    self.smoothing_factor = config.get("smoothing_factor", self.smoothing_factor)
                    self.pen_color = config.get("pen_color", self.pen_color)
                    self.auto_copy_on_close = config.get("auto_copy_on_close", self.auto_copy_on_close)
                    self.hotkey = config.get("hotkey", self.hotkey)
                    self.last_save_dir = config.get("last_save_dir", self.last_save_dir)
                    self.render_canvas_brushstroke = config.get("render_canvas_brushstroke", True)
            except (json.JSONDecodeError, FileNotFoundError):
                # Config file exists but is invalid
                messagebox.showerror("Invalid Config File",
                                     f"The configuration file at '{self.config_file}' is invalid or corrupt.\n\n"
                                     "Please fix or delete the file so that it can be recreated on the next startup of the application.\n"
                                     "We recommend taking a backup of the file before deleting.\n\n"
                                     "For this session, default settings have been loaded.\n"
                                     "Opening the settings menu and clicking 'apply' will also overwrite the config file with the current (default) settings.")
                # Load default settings (already set)

    def save_config(self):
        config = {
            "window_width": self.window_width,
            "window_height": self.window_height,
            "pen_width": self.pen_width,
            "smoothing_factor": self.smoothing_factor,
            "pen_color": self.pen_color,
            "auto_copy_on_close": self.auto_copy_on_close,
            "hotkey": self.hotkey,
            "last_save_dir": self.last_save_dir,
            "render_canvas_brushstroke": self.render_canvas_brushstroke
        }
        with open(self.config_file, "w") as file:
            json.dump(config, file)

    def create_tray_icon(self):
        # Load the tray icon image
        tray_icon_image = self.load_tray_icon("opicodraw.ico")  # Replace with your tray icon filename

        self.icon = pystray.Icon("OpicoDraw", tray_icon_image, title="opico draw", menu=pystray.Menu(
            item("open opico draw", self.on_systray_open_drawing),
            item("settings", self.on_systray_open_settings),
            item("exit", self.on_systray_exit)
        ))

        # Start the icon without blocking
        threading.Thread(target=self.icon.run, daemon=True).start()

        # Start the periodic tray icon updater after ensuring the icon is initialized
        self.root.after(100, self.update_tray_icon)

    def update_tray_icon(self):
        # This method is called periodically to process tray icon events
        if self.icon is not None:
            self.icon.update_menu()
        self.tray_icon_updater_id = self.root.after(100, self.update_tray_icon)

    def on_systray_open_drawing(self):
        self.root.after(0, self.show_window)

    def on_systray_open_settings(self):
        self.root.after(0, self.show_settings)

    def on_systray_exit(self):
        self.root.after(0, self.exit_app)

    def apply_hotkey(self):
        if self.hotkey_id:
            try:
                keyboard.remove_hotkey(self.hotkey_id)
                self.hotkey_id = None
            except KeyError:
                self.hotkey_id = None

        # Register the hotkey with keyboard module
        self.hotkey_id = keyboard.add_hotkey(self.hotkey, lambda: self.root.after(0, self.show_window))

    def show_window(self):
        mouse_x, mouse_y = pyautogui.position()
        x_position = mouse_x - self.window_width // 2
        y_position = mouse_y - self.window_height // 2

        if self.drawing_window is None or not self.drawing_window.winfo_exists():
            self.drawing_window = tk.Toplevel()
            self.drawing_window.title("opico draw")
            self.drawing_window.geometry(f"{self.window_width}x{self.window_height}+{x_position}+{y_position}")
            self.drawing_window.configure(bg="white")
            self.drawing_window.protocol("WM_DELETE_WINDOW", self.close_window)
            self.drawing_window.resizable(False, False)
            self.drawing_window.attributes("-topmost", True)
            self.drawing_window.focus_force()

            # Delay setting the icon to prevent flashing
            self.drawing_window.after(50, lambda: self.drawing_window.iconphoto(False, self.icon_image))

            # Remove maximize and minimize buttons, leaving only the close button
            # Increase the delay to ensure the window is fully initialized
            self.drawing_window.after(500, lambda: remove_maximize_minimize(self.drawing_window))

            self.canvas = tk.Canvas(self.drawing_window, width=self.window_width, height=self.window_height, bg="white", cursor="cross")
            self.canvas.pack()

            self.create_image()

            self.last_x, self.last_y = None, None
            self.points = []
            self.is_drawing = False

            self.canvas.bind("<ButtonPress-1>", self.on_button_press)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

            # Key bindings
            self.drawing_window.bind("<Control-c>", self.save_as_png)
            self.drawing_window.bind("<Control-C>", self.save_as_png)  # Uppercase binding

            self.drawing_window.bind("<Control-s>", self.save_as_file)
            self.drawing_window.bind("<Control-S>", self.save_as_file)  # Uppercase binding

            self.drawing_window.bind("<Control-Alt-s>", self.save_as_file)
            self.drawing_window.bind("<Control-Alt-S>", self.save_as_file)  # Uppercase binding

            self.drawing_window.bind("<Control-Shift-Key-S>", self.save_as_file)

            self.drawing_window.bind("<Button-3>", self.toggle_mini_settings)

            # Key bindings for undo and redo
            self.drawing_window.bind("<Control-z>", self.undo)
            self.drawing_window.bind("<Control-Z>", self.undo)  # For Caps Lock
            self.drawing_window.bind("<Control-y>", self.redo)
            self.drawing_window.bind("<Control-Y>", self.redo)  # For Caps Lock
            self.drawing_window.bind("<Control-Shift-Key-Z>", self.redo)
            self.drawing_window.bind("<Control-Shift-Key-z>", self.redo)  # For Caps Lock

            self.is_window_open = True
        else:
            # Move the window to the new position without clearing the canvas
            self.drawing_window.geometry(f"+{x_position}+{y_position}")
            self.drawing_window.deiconify()
            self.drawing_window.lift()
            self.drawing_window.focus_force()
            # Update the canvas to reflect the current image
            self.update_canvas()
            # Close the mini settings window if it's open
            if self.mini_settings_window and self.mini_settings_window.winfo_exists():
                self.mini_settings_window.destroy()
                self.mini_settings_window = None

    def create_image(self):
        self.scale_factor = 4
        self.image = Image.new("RGBA", (self.window_width * self.scale_factor, self.window_height * self.scale_factor), (255, 255, 255, 0))
        self.draw = ImageDraw.Draw(self.image)

        # Clear the undo and redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()

        # Update the canvas to reflect the new image
        if self.is_window_open:
            self.update_canvas()

    def update_canvas(self):
        # Resize the image to match the canvas size
        resized_image = self.image.resize((self.window_width, self.window_height), Image.LANCZOS)
        # Convert to PhotoImage for Tkinter
        self.photo_image = ImageTk.PhotoImage(resized_image)
        # Clear the canvas and display the updated image
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo_image, anchor=tk.NW)

    def save_undo_state(self):
        # Remove oldest history if we exceed max history size
        if len(self.undo_stack) >= self.max_history:
            self.undo_stack.pop(0)

        # Save a copy of the current image
        self.undo_stack.append(self.image.copy())

        # Clear the redo stack since we're starting a new action
        self.redo_stack.clear()

    def undo(self, event=None):
        if self.undo_stack:
            # Push the current state onto the redo stack
            self.redo_stack.append(self.image.copy())

            # Pop the last state from the undo stack and restore it
            self.image = self.undo_stack.pop()
            self.draw = ImageDraw.Draw(self.image)

            # Update the canvas
            self.update_canvas()

    def redo(self, event=None):
        if self.redo_stack:
            # Push the current state onto the undo stack
            self.undo_stack.append(self.image.copy())

            # Pop the last state from the redo stack and restore it
            self.image = self.redo_stack.pop()
            self.draw = ImageDraw.Draw(self.image)

            # Update the canvas
            self.update_canvas()

    def on_button_press(self, event):
        if self.mini_settings_window is not None:
            self.mini_settings_window.destroy()
            self.mini_settings_window = None

        # Save the current state for undo
        self.save_undo_state()

        self.last_x, self.last_y = event.x, event.y
        self.points = [(self.last_x, self.last_y)]
        self.is_drawing = False

    def on_mouse_drag(self, event):
        self.is_drawing = True
        x, y = event.x, event.y
        self.points.append((x, y))

        if len(self.points) >= self.smoothing_factor:
            avg_x = sum(p[0] for p in self.points) / len(self.points)
            avg_y = sum(p[1] for p in self.points) / len(self.points)

            self.canvas.create_line(
                self.last_x, self.last_y, avg_x, avg_y,
                fill=self.pen_color, width=self.pen_width, capstyle=tk.ROUND, smooth=True
            )

            x1 = int(self.last_x * self.scale_factor)
            y1 = int(self.last_y * self.scale_factor)
            x2 = int(avg_x * self.scale_factor)
            y2 = int(avg_y * self.scale_factor)
            width = int(self.pen_width * self.scale_factor)
            line_coords = (x1, y1, x2, y2)
            self.draw_line_with_round_ends(line_coords, fill=self.pen_color, width=width)

            self.last_x, self.last_y = avg_x, avg_y
            self.points.pop(0)
        else:
            self.canvas.create_line(
                self.last_x, self.last_y, x, y,
                fill=self.pen_color, width=self.pen_width, capstyle=tk.ROUND, smooth=True
            )

            x1 = int(self.last_x * self.scale_factor)
            y1 = int(self.last_y * self.scale_factor)
            x2 = int(x * self.scale_factor)
            y2 = int(y * self.scale_factor)
            width = int(self.pen_width * self.scale_factor)
            line_coords = (x1, y1, x2, y2)
            self.draw_line_with_round_ends(line_coords, fill=self.pen_color, width=width)

            self.last_x, self.last_y = x, y

    def on_button_release(self, event):
        if not self.is_drawing:
            if self.last_x is None or self.last_y is None:
                return  # Nothing to do if last_x or last_y is None
            x, y = self.last_x, self.last_y
            self.canvas.create_oval(
                x - self.pen_width / 2, y - self.pen_width / 2,
                x + self.pen_width / 2, y + self.pen_width / 2,
                fill=self.pen_color, outline=self.pen_color
            )

            x1 = int(x * self.scale_factor)
            y1 = int(y * self.scale_factor)
            width = int(self.pen_width * self.scale_factor)
            radius = width / 2
            bbox = (x1 - radius, y1 - radius, x1 + radius, y1 + radius)
            self.draw.ellipse(bbox, fill=self.pen_color)

        self.last_x, self.last_y = None, None
        self.points = []
        self.is_drawing = False

        # Conditionally update the canvas
        if self.render_canvas_brushstroke:
            self.update_canvas()

    def draw_line_with_round_ends(self, coords, fill, width):
        x1, y1, x2, y2 = coords
        self.draw.line(coords, fill=fill, width=width)
        radius = width / 2
        bbox1 = (x1 - radius, y1 - radius, x1 + radius, y1 + radius)
        bbox2 = (x2 - radius, y2 - radius, x2 + radius, y2 + radius)
        self.draw.ellipse(bbox1, fill=fill)
        self.draw.ellipse(bbox2, fill=fill)

    def save_as_png(self, event=None):
        resized_image = self.image.resize((self.window_width, self.window_height), Image.LANCZOS)

        background = Image.new('RGB', resized_image.size, (255, 255, 255))

        if resized_image.mode == 'RGBA':
            background.paste(resized_image, mask=resized_image.split()[3])
        else:
            background.paste(resized_image)

        image_to_save = background

        output = BytesIO()
        image_to_save.save(output, format="BMP")
        bmp_data = output.getvalue()
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data[14:])
        win32clipboard.CloseClipboard()

    def save_as_file(self, event=None):
        # Get the initial directory
        default_pictures_folder = os.path.join(os.getenv('USERPROFILE'), 'Pictures')
        if os.path.exists(self.last_save_dir):
            initial_dir = self.last_save_dir
        else:
            initial_dir = default_pictures_folder
            # Update the last_save_dir in the config
            self.last_save_dir = default_pictures_folder
            self.save_config()

        # Open the Save As dialog
        file_path = filedialog.asksaveasfilename(
            parent=self.drawing_window,
            defaultextension='.png',
            filetypes=[('PNG files', '*.png'), ('All files', '*.*')],
            initialdir=initial_dir,
            title='save image as'
        )

        if file_path:
            # Save the image to the file
            resized_image = self.image.resize((self.window_width, self.window_height), Image.LANCZOS)

            background = Image.new('RGB', resized_image.size, (255, 255, 255))

            if resized_image.mode == 'RGBA':
                background.paste(resized_image, mask=resized_image.split()[3])
            else:
                background.paste(resized_image)

            background.save(file_path, 'PNG')

            # Update the last save directory
            self.last_save_dir = os.path.dirname(file_path)
            self.save_config()

    def toggle_mini_settings(self, event):
        if self.mini_settings_window is not None:
            self.mini_settings_window.destroy()
            self.mini_settings_window = None
        else:
            self.show_mini_settings(event)

    def show_mini_settings(self, event):
        if self.mini_settings_window is not None and self.mini_settings_window.winfo_exists():
            self.mini_settings_window.destroy()

        self.mini_settings_window = tk.Toplevel()
        self.mini_settings_window.title("mini settings")
        self.mini_settings_window.resizable(False, False)
        self.mini_settings_window.attributes("-topmost", True)
        self.mini_settings_window.overrideredirect(True)

        # Bind right-click to destroy the mini settings window
        self.mini_settings_window.bind("<Button-3>", lambda e: self.mini_settings_window.destroy())

        # Add widgets to the mini settings window
        tk.Label(self.mini_settings_window, text="pen size:").pack()
        pen_size_slider = tk.Scale(self.mini_settings_window, from_=1, to=25, orient=tk.HORIZONTAL)
        pen_size_slider.set(self.pen_width)
        pen_size_slider.pack()
        pen_size_slider.bind("<Motion>", lambda e: self.update_pen_size(pen_size_slider.get()))

        self.mini_color_display = tk.Label(
            self.mini_settings_window, 
            text="select color", 
            bg=self.pen_color, 
            width=20, 
            height=2, 
            fg=self.get_inverse_color(self.pen_color)
        )
        self.mini_color_display.pack(pady=5)
        self.mini_color_display.bind("<Button-1>", self.choose_color)

        # Delay setting the icon to prevent flashing
        self.mini_settings_window.after(50, lambda: self.mini_settings_window.iconphoto(False, self.icon_image))

        # Update the window to calculate its size
        self.mini_settings_window.update_idletasks()

        # Retrieve the window's dimensions
        window_width = self.mini_settings_window.winfo_width()
        window_height = self.mini_settings_window.winfo_height()

        # Calculate the new position so that the window's center aligns with the cursor
        center_x = event.x_root
        center_y = event.y_root
        pos_x = center_x - (window_width // 2)
        pos_y = center_y - (window_height // 2)

        # Set the new geometry with the calculated position
        self.mini_settings_window.geometry(f"+{pos_x}+{pos_y}")

    def update_pen_size(self, size):
        self.pen_width = size

    def close_window(self):
        if self.auto_copy_on_close:
            self.save_as_png()
        if self.drawing_window:
            self.drawing_window.destroy()
            self.drawing_window = None
            self.is_window_open = False
        if self.mini_settings_window:
            self.mini_settings_window.destroy()
            self.mini_settings_window = None

    def exit_app(self):
        # Remove the hotkey if it exists
        if self.hotkey_id is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_id)
            except KeyError:
                pass  # Hotkey may have already been removed
            self.hotkey_id = None

        # Destroy all Tkinter windows
        if self.drawing_window:
            self.drawing_window.destroy()
            self.drawing_window = None
        if self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None
        if self.mini_settings_window:
            self.mini_settings_window.destroy()
            self.mini_settings_window = None

        # Cancel the periodic tray icon update if it exists
        if self.tray_icon_updater_id is not None:
            try:
                self.root.after_cancel(self.tray_icon_updater_id)
            except Exception:
                pass
            self.tray_icon_updater_id = None

        # Stop the tray icon
        if self.icon:
            self.icon.visible = False
            self.icon.stop()
            self.icon = None

        self.root.quit()

    def get_inverse_color(self, hex_color):
        rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
        inverse_rgb = [(255 - c) for c in rgb]
        return f'#{inverse_rgb[0]:02x}{inverse_rgb[1]:02x}{inverse_rgb[2]:02x}'

    def choose_color(self, event=None):
        # Get the current mouse position
        mouse_x, mouse_y = pyautogui.position()
        
        # Create a temporary Toplevel window positioned at the mouse cursor
        temp_window = tk.Toplevel()
        temp_window.overrideredirect(True)  # Remove window decorations
        temp_window.geometry(f"1x1+{mouse_x}+{mouse_y}")  # Position at mouse and make it 1x1 pixel
        temp_window.attributes("-topmost", True)  # Ensure it's on top
        temp_window.update_idletasks()  # Ensure the window is created

        try:
            # Open the color chooser with the temporary window as the parent
            color_code = colorchooser.askcolor(title="Choose Pen Color", parent=temp_window)[1]
        finally:
            # Destroy the temporary window after the color chooser is closed
            temp_window.destroy()

        if color_code:
            self.pen_color = color_code
            inverse_color = self.get_inverse_color(self.pen_color)
            
            # Update the color display in settings window if it exists
            if hasattr(self, 'color_display') and self.color_display:
                self.color_display.config(bg=self.pen_color, fg=inverse_color)
            
            # Update the color display in mini settings window if it exists
            if hasattr(self, 'mini_color_display') and self.mini_color_display.winfo_exists():
                self.mini_color_display.config(bg=self.pen_color, fg=inverse_color)


    def show_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.deiconify()
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel()
        self.settings_window.title("settings")
        self.settings_window.geometry("322x510")  # Reverted to original size
        self.settings_window.resizable(False, False)
        self.settings_window.protocol("WM_DELETE_WINDOW", self.hide_settings)

        # Delay setting the icon to prevent flashing
        self.settings_window.after(50, lambda: self.settings_window.iconphoto(False, self.icon_image))

        # Create a main frame to hold all other frames
        main_frame = tk.Frame(self.settings_window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas Settings Frame (Renamed from General Settings)
        canvas_frame = tk.LabelFrame(main_frame, text="canvas settings", padx=10, pady=10)
        canvas_frame.grid(row=0, column=0, sticky="ew", pady=5)

        # Configure grid to expand
        canvas_frame.columnconfigure(1, weight=1)

        # Canvas Width (Renamed from Drawing Pad Width)
        tk.Label(canvas_frame, text="canvas width:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.width_entry = tk.Entry(canvas_frame)
        self.width_entry.insert(0, str(self.window_width))
        self.width_entry.grid(row=0, column=1, pady=5, sticky="ew")

        # Canvas Height (Renamed from Drawing Pad Height)
        tk.Label(canvas_frame, text="canvas height:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.height_entry = tk.Entry(canvas_frame)
        self.height_entry.insert(0, str(self.window_height))
        self.height_entry.grid(row=1, column=1, pady=5, sticky="ew")

        # Pen Settings Frame
        pen_frame = tk.LabelFrame(main_frame, text="pen settings", padx=10, pady=10)
        pen_frame.grid(row=1, column=0, sticky="ew", pady=5)

        # Configure grid to expand
        pen_frame.columnconfigure(1, weight=1)

        # Pen Size
        tk.Label(pen_frame, text="pen size:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.pen_size_entry = tk.Entry(pen_frame)
        self.pen_size_entry.insert(0, str(self.pen_width))
        self.pen_size_entry.grid(row=0, column=1, pady=5, sticky="ew")

        # Pen Smoothing (Moved and Renamed from Smoothing Factor)
        tk.Label(pen_frame, text="pen smoothing:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.pen_smoothing_entry = tk.Entry(pen_frame)
        self.pen_smoothing_entry.insert(0, str(self.smoothing_factor))
        self.pen_smoothing_entry.grid(row=1, column=1, pady=5, sticky="ew")

        # Pen Color
        tk.Label(pen_frame, text="pen color:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.color_display = tk.Label(
            pen_frame, 
            text="select color", 
            bg=self.pen_color, 
            fg=self.get_inverse_color(self.pen_color),  # Set fg correctly here
            width=15, 
            height=2, 
            relief=tk.SUNKEN,
            bd=1
        )
        self.color_display.grid(row=2, column=1, pady=5, sticky=tk.W)
        self.color_display.bind("<Button-1>", self.choose_color)

        # Advanced Settings Frame
        advanced_frame = tk.LabelFrame(main_frame, text="advanced settings", padx=10, pady=10)
        advanced_frame.grid(row=2, column=0, sticky="ew", pady=5)

        # Configure grid to expand
        advanced_frame.columnconfigure(1, weight=1)

        # Automatically Copy on Close
        self.auto_copy_var = tk.BooleanVar(value=self.auto_copy_on_close)
        self.auto_copy_checkbox = tk.Checkbutton(
            advanced_frame, 
            text="automatically copy on close", 
            variable=self.auto_copy_var, 
            command=self.update_auto_copy_setting
        )
        self.auto_copy_checkbox.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Render Canvas After Brush Stroke
        self.render_canvas_var = tk.BooleanVar(value=self.render_canvas_brushstroke)
        self.render_canvas_checkbox = tk.Checkbutton(
            advanced_frame,
            text="render canvas after brush stroke",
            variable=self.render_canvas_var,
            command=self.update_render_canvas_setting
        )
        self.render_canvas_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Hotkey Settings
        tk.Label(advanced_frame, text="hotkey to open opico draw:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.hotkey_label = tk.Label(advanced_frame, text=self.hotkey, relief=tk.SUNKEN, width=15)
        self.hotkey_label.grid(row=2, column=1, pady=5, sticky=tk.W)
        set_hotkey_button = tk.Button(advanced_frame, text="set hotkey", command=self.record_hotkey)
        set_hotkey_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

        # Apply Button Frame
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=2)

        apply_button = tk.Button(button_frame, text="apply settings and save to startup config", command=self.apply_settings, width=35)
        apply_button.pack(pady=5)  # Center the button within the button_frame




    def record_hotkey(self):
        self.hotkey_label.config(text="press keys...")
        if self.hotkey_id:
            try:
                keyboard.remove_hotkey(self.hotkey_id)
                self.hotkey_id = None
            except KeyError:
                self.hotkey_id = None

        def get_hotkey():
            final_hotkey = keyboard.read_hotkey(suppress=False)
            self.root.after(0, self.set_new_hotkey, final_hotkey)

        threading.Thread(target=get_hotkey).start()

    def set_new_hotkey(self, final_hotkey):
        # Normalize the hotkey
        self.hotkey = final_hotkey.lower()
        self.hotkey_label.config(text=self.hotkey)
        self.apply_hotkey()
        self.save_config()

    def update_auto_copy_setting(self):
        self.auto_copy_on_close = self.auto_copy_var.get()
        self.save_config()

    def update_render_canvas_setting(self):
        self.render_canvas_brushstroke = self.render_canvas_var.get()
        self.save_config()

    def hide_settings(self):
        if self.settings_window:
            self.settings_window.withdraw()

    def apply_settings(self):
        try:
            # Retrieve new width and height from the settings entries
            new_width = int(self.width_entry.get())
            new_height = int(self.height_entry.get())

            # Retrieve pen size and smoothing factor from the settings entries
            self.pen_width = int(self.pen_size_entry.get())
            self.smoothing_factor = int(self.pen_smoothing_entry.get())  # Corrected reference

            # Update window dimensions before saving to config
            self.window_width = new_width
            self.window_height = new_height

            # Save all updated settings to the configuration file
            self.save_config()

            # If the drawing window is open, update its size and the canvas
            if self.drawing_window and self.is_window_open:
                # Update the window size
                self.drawing_window.geometry(f"{self.window_width}x{self.window_height}")

                # Update the canvas size
                self.canvas.config(width=self.window_width, height=self.window_height)

                # Recreate the image with the new canvas size
                self.create_image()

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integer values for width, height, pen size, and smoothing factor.")


# Add the function to remove maximize and minimize buttons
def remove_maximize_minimize(window):
    if sys.platform != 'win32':
        return
    hwnd = windll.user32.GetParent(window.winfo_id())
    GWL_STYLE = -16
    WS_SYSMENU = 0x00080000
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_FRAMECHANGED = 0x0020

    style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
    # Keep WS_SYSMENU (system menu), remove minimize and maximize
    style = style | WS_SYSMENU
    style = style & ~WS_MINIMIZEBOX & ~WS_MAXIMIZEBOX
    windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
    windll.user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED)

if __name__ == "__main__":
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.withdraw()
    app = OpicoDrawApp(root)
    root.mainloop()
