# opico draw

**opico draw** is a lightweight, popup drawing application designed for quick and seamless integration into your workflow. inspired by pictochat, opico draw runs discreetly in the background, allowing you to instantly access a drawing window via a customizable hotkey. whether you're doodling, annotating, or creating quick sketches, opico draw makes it easy to capture your ideas and paste them directly into applications like discord.

## table of contents

- [features](#features)
- [installation](#installation)
- [usage](#usage)
- [shortcuts](#shortcuts)
- [configuration](#configuration)
- [default values](#default-values)
- [dependencies](#dependencies)
- [license](#license)
- [contributing](#contributing)
- [faq](#faq)
- [contact](#contact)

## features

- **quick access:** activate the drawing window instantly with a customizable hotkey.
- **brush customization:** easily change brush size and color using the right mouse button within the drawing window.
- **clipboard integration:** copy your drawings to the clipboard with a simple keyboard shortcut.
- **undo/redo functionality:** robust history support with up to 128 undo and redo steps.
- **auto-copy on close:** automatically copy the current drawing to the clipboard when closing the window (configurable).
- **save options:** multiple save dialog options for flexibility.
- **tray icon:** access opico draw functionalities through a system tray icon.
- **settings window:** customize various settings such as canvas size, pen properties, and hotkeys.
- **minimal ui:** designed to be unobtrusive with a clean and simple interface.

## installation

### compiling and downloading executables

opico draw can be compiled with **pyinstaller** to create a standalone executable. use the following command:

```bash
pyinstaller --onefile --noconsole --icon=opicodraw.ico --add-data "opicodraw.ico;." --upx-dir "C:\UPX\DIRECTORY\LOCATION" --strip --exclude-module pyinstaller --exclude-module altgraph --exclude-module pyinstaller_hooks_contrib --exclude-module pefile --exclude-module pywin32_ctypes --exclude-module packaging opicodraw.py
```

make sure that `opicodraw.py` is in the same folder or specify its location in the command. a precompiled version (`exe`) is also available, compressed with **upx** in a virtual environment for optimal file size.

### downloading opico draw

you can download the latest release from the [releases page](https://github.com/ol1fer/opicodraw/releases) or clone the source code to build it yourself.

### prerequisites

- **operating system:** windows (due to the use of `win32clipboard` and specific window style modifications).
- **python version:** python 3.7 or higher.

### steps

1. **clone the repository:**

   ```bash
   git clone https://github.com/ol1fer/opicodraw.git
   ```

2. **navigate to the project directory:**

   ```bash
   cd opicodraw
   ```

3. **install dependencies:**

   it's recommended to use a virtual environment.

   ```bash
   python -m venv venv
   venv\scripts\activate
   pip install -r requirements.txt
   ```

4. **run the application:**

   ```bash
   python opicodraw.py
   ```

   *note: replace `opicodraw.py` with the actual entry point of your application.*

### adding opico draw to startup

to have opico draw start automatically when you log into windows, you can manually add the program or a shortcut to the startup folder:

1. **locate the executable or create a shortcut:**
   - navigate to the directory containing `opicodraw.py/opicodraw.exe`.
   - if you prefer, create a shortcut to `opicodraw.py/opicodraw.exe` by right-clicking the file and selecting **create shortcut**.

2. **copy to startup folder:**

   - press `win + r`, type `shell:startup`, and press `enter`. this will open the startup folder.
   
   - **path:**
     ```
     C:\Users\oliver\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
     ```

   - paste the `opicodraw.py/opicodraw.exe` file or its shortcut into this folder.

   opico draw will now launch automatically each time you start your computer.

## usage

1. **activate drawing window:**
   - press the default hotkey `alt + shift + q` (configurable) to open the drawing window.

2. **drawing:**
   - use your mouse or tablet to draw within the window.
   - right-click to quickly change brush size or color.

3. **copying:**
   - press `ctrl + c` to copy the current drawing to the clipboard.
   - the drawing is automatically copied when you close the window (if enabled).

4. **saving:**
   - press `ctrl + s` to open the save dialog.
   - additional save options:
     - `ctrl + shift + s`
     - `ctrl + alt + s`

5. **undo/redo:**
   - press `ctrl + z` to undo the last action.
   - press `ctrl + shift + z` or `ctrl + y` to redo the last undone action.

6. **accessing settings:**
   - right-click the system tray icon and select "settings" to customize various application settings.

7. **applying and saving settings:**
   - after adjusting settings in the settings window, click the **"apply settings and save to startup config"** button at the bottom to save your preferences. these settings are stored in a configuration file and will be loaded automatically on startup.

## shortcuts

| action                           | shortcut                           |
|----------------------------------|------------------------------------|
| open drawing window              | `alt + shift + q`                  |
| open save dialog                 | `ctrl + s`                         |
| open alternate save dialog       | `ctrl + shift + s`                 |
| open another save dialog         | `ctrl + alt + s`                   |
| copy drawing to clipboard        | `ctrl + c`                         |
| undo last action                 | `ctrl + z`                         |
| redo last action                 | `ctrl + shift + z`                 |
| redo last action (alternative)    | `ctrl + y`                         |
| open settings                    | system tray > settings             |
| open drawing window via tray     | system tray > open opico draw       |

*all shortcuts are configurable through the settings window.*

## configuration

opico draw offers several configuration options to tailor the application to your workflow. these settings can be accessed through the settings window, which can be opened via the system tray icon or by using the designated shortcut.

### settings categories

1. **canvas settings:**
   - **canvas width:** adjust the width of the drawing canvas.
   - **canvas height:** adjust the height of the drawing canvas.

2. **pen settings:**
   - **pen size:** change the thickness of the brush.
   - **pen smoothing:** adjust the smoothing factor for smoother lines.
   - **pen color:** select the color of the brush.

3. **advanced settings:**
   - **automatically copy on close:** enable or disable automatic copying of the drawing to the clipboard upon closing the window.
   - **render canvas after brush stroke:** toggle rendering the canvas after each brush stroke for performance optimization.
   - **hotkey to open opico draw:** customize the keyboard shortcut used to activate the drawing window.

### how to change settings

1. **open settings:**
   - right-click the opico draw icon in the system tray and select "settings."

2. **modify desired settings:**
   - navigate through the different settings categories and adjust the values as needed.

3. **apply and save:**
   - click the **"apply settings and save to startup config"** button at the bottom of the settings window to save changes. this action updates the configuration file, ensuring that your preferences persist across application restarts.

### configuration file

opico draw saves its configuration in a json file located at:

```
%APPDATA%\opicodraw\config.json
```

this file stores all user-defined settings, ensuring that preferences persist across application restarts.

## default values

- **default shortcut:** `alt + shift + q`
- **undo history:** up to 128 steps
- **auto-copy on close:** enabled by default
- **brush size:** 4 pixels
- **pen color:** black (`#000000`)
- **canvas size:** 600x300 pixels
- **smoothing factor:** 10
- **last save directory:** `%userprofile%\pictures`
- **render canvas after brush stroke:** enabled by default

## dependencies

opico draw relies on several python libraries to function correctly. ensure all dependencies are installed before running the application.

### core dependencies

- **tkinter:** standard python interface to the tk gui toolkit.
- **pillow (pil):** python imaging library for image processing.
- **pystray:** for creating and managing the system tray icon.
- **keyboard:** for global hotkey registration and handling.
- **pyautogui:** for interacting with the mouse and retrieving cursor positions.
- **pywin32:** for clipboard operations on windows.

### installation of dependencies

install all dependencies using `pip`:

```bash
pip install pillow pystray keyboard pyautogui pywin32
```

*note: ensure you have the necessary permissions to install python packages.*

## license

plase see license.md for more info.

## faq

**q1: how do i change the activation hotkey?**

*a:* open the settings window via the system tray icon, navigate to the "advanced settings" section, and click on "set hotkey." press your desired key combination, and it will be updated accordingly.

**q2: the drawing window isn't opening when i press the hotkey. what should i do?**

*a:* ensure that the application is running and that the hotkey hasn't been changed. you can also try restarting the application or checking if another application is using the same hotkey combination.

**q3: can i change the default save directory for my drawings?**

*a:* yes. save with one of the hotkeys, like ctrl + s then save a drawing somewhere. this will now be the default directory.

**q4: i'm experiencing lag when drawing. how can i improve performance?**

*a:* reducing the canvas size or lowering the smoothing factor in the settings may help improve performance. it's extremely low impact on your pc, especially when not actively drawing. if you get performance issues you may need a new pc lol

**q5: is opico draw available on macos or linux?**

*a:* no
