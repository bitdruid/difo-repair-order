import sys
import os
import magic
import re
import datetime

import piexif
from PIL import Image

from win32_setctime import setctime

from pathlib import Path
from shutil import copyfile
import tkinter as tk
from pprint import pprint
from tkinter import Tk, Canvas, Entry, PhotoImage, filedialog, scrolledtext

# Global variables
FILES = []
FOLDER = ""
DISORDER_FOUND = False
CHECKBOX_NO_BACKUP = False
CHECKBOX_DELETE = False
BACKUP_CREATED = False

VERSION = "1.0.0"

def relative_to_assets(path: str) -> Path:
    if getattr(sys, 'frozen', False):
        # as one-file executable
        return Path(sys._MEIPASS) / Path(r"assets") / Path(path)
    else:
        # as script
        return Path(__file__).parent / Path(r"assets") / Path(path)

def toggle_checkbox(checkbox_var: str, checkbox_image_id: int, checked_image: PhotoImage, unchecked_image: PhotoImage):
    global CHECKBOX_DELETE, CHECKBOX_NO_BACKUP

    if checkbox_var == 'CHECKBOX_DELETE':
        CHECKBOX_DELETE = not CHECKBOX_DELETE
        new_image = checked_image if CHECKBOX_DELETE else unchecked_image
    elif checkbox_var == 'CHECKBOX_NO_BACKUP':
        CHECKBOX_NO_BACKUP = not CHECKBOX_NO_BACKUP
        new_image = checked_image if CHECKBOX_NO_BACKUP else unchecked_image

    canvas.itemconfig(checkbox_image_id, image=new_image)





def print_log(message, clean=False):
    if clean:
        log_output.config(state="normal")
        log_output.delete(1.0, tk.END)
        log_output.config(state="disabled")
        pprint(message)
    else:
        log_output.config(state="normal")
        log_output.insert(tk.END, message + "\n")
        log_output.config(state="disabled")
        pprint(message)

def save_log():
    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_output.config(state="normal")
    log_content = log_output.get(1.0, tk.END)
    log_output.config(state="disabled")
    file = filedialog.asksaveasfile(mode="w", title="Log speichern", initialfile="diforepairorder_" + date, defaultextension=".log", filetypes=[("Text files", "*.txt")])
    if file:
        file.write(log_content)

def proceed_messagebox():
    message = f"Verzeichnis:\n{FOLDER}\n\n"
    if CHECKBOX_DELETE:
        message += "- Alles außer Bilder wird gelöscht\n"
    if CHECKBOX_NO_BACKUP:
        message += "- Es wird keine Sicherung erstellt\n"
    message += "\nACHTUNG!\nDateien in diesem Ordner werden umbenannt und/oder gelöscht! Ist das Verzeichnis korrekt?"
    message += "\nFortfahren?"
    return tk.messagebox.askquestion("Einstellungen prüfen", message, icon="warning")

def choose_directory():
    directory = filedialog.askdirectory()
    if directory:
        # set folder_selection to None if system drive
        #if "c:" in directory.lower():
        #    print_log("Das ausgewählte Verzeichnis befindet sich auf dem Systemlaufwerk. Bitte den Ordner auf der SD-Karte der Kamera auswählen.\n")
        #else:
        print_log("", clean=True)
        print_log("Ausgewähltes Verzeichnis:\n" + directory + "\n")
        folder_selection.delete(0, tk.END)
        folder_selection.insert(0, directory)
        directory_files = os.listdir(directory)
        print_log("Dateien im ausgewählten Verzeichnis:\n")
        for file in directory_files:
            print_log(f"- {file}")
        print_log("")





def read_files():
        
    global FILES
    FILES = []
    for file in os.listdir(FOLDER):
        if os.path.isdir(file): continue
        file_path = os.path.join(FOLDER, file)
        file_info = {
            "name_old": file,
            "name_new": "",
            "filetype": magic.Magic(mime=True).from_file(file_path).split("/")[0],
            "file_created": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        }
        FILES.append(file_info)
    pprint(FILES)

def repair_order():
    global FILES, DISORDER_FOUND
    FILES = sorted(FILES, key=lambda x: x["name_old"])
    files_last_correct_number = False
    DISORDER_FOUND = False
    for file in FILES:
        if file["filetype"] == "image":
            number = re.search(r'\d+', file["name_old"])
            if number:
                number = int(number.group())
                if files_last_correct_number is False:
                    files_last_correct_number = number
                else:
                    if number == files_last_correct_number + 1:
                        files_last_correct_number = number
                    else:
                        DISORDER_FOUND = True
    if DISORDER_FOUND:
        print_log("Fehlerhafte Bildreihenfolge gefunden\n")
    else:
        print_log("Keine fehlerhafte Bildreihenfolge gefunden\n")

    pprint(FILES)





def rename_files():
    global FILES
    FILES = sorted(FILES, key=lambda x: x["file_created"])
    print_log("Bilder werden umbenannt:")
    name_new = "IMG_%s.%s"
    counter = 1
    for file in FILES:
        if file["filetype"] == "image":
            file["name_new"] = name_new % (str(counter).zfill(4), file["name_old"].split(".")[1])
            os.rename(file["name_old"], file["name_new"])
            print_log(f"Alt: {file['name_old']} -> Neu: {file['name_new']}")
            counter += 1
    print_log("")

def timestamp_files():
    """
    Takes the timestamp of the first image and applies the same timestamp on each image with 1 second interval.
    """
    global FILES
    print_log("Zeitstempel der Bilder wird angereiht:")
    first_image = True
    shot_date = None
    shot_time = None
    for file in FILES:
        if file["filetype"] == "image":
            if first_image:
                shot_date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y:%m:%d")
                shot_time = "00:00:00"
                first_image = False
            else:
                shot_time = (datetime.datetime.strptime(shot_time, "%H:%M:%S") + datetime.timedelta(seconds=1)).strftime("%H:%M:%S")
            
            current_image = file["name_new"] if file["name_new"] else file["name_old"]

            im = Image.open(current_image)
            try:
                exif_dict = piexif.load(im.info["exif"])
            except KeyError:
                exif_dict = {
                    "0th": {}, 
                    "Exif": {}, 
                    "GPS": {}, 
                    "Interop": {}, 
                    "1st": {}, 
                    "thumbnail": None
                    }
            datetime_str = f"{shot_date} {shot_time}"
            exif_dict["0th"][piexif.ImageIFD.Make] = b"NASA"
            exif_dict["0th"][piexif.ImageIFD.Model] = b"Hubble Space Telescope Perkin-Elmer Corporation"
            exif_dict["0th"][piexif.ImageIFD.DateTime] = datetime_str

            exif_dict["1st"][piexif.ImageIFD.Make] = b"NASA"
            exif_dict["1st"][piexif.ImageIFD.Model] = b"Hubble Space Telescope Perkin-Elmer Corporation"
            exif_dict["1st"][piexif.ImageIFD.DateTime] = datetime_str

            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = datetime_str
            exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = datetime_str
            exif_dict["Exif"][piexif.ExifIFD.LensMake] = b"Perkin-Elmer Corporation"
            exif_dict["Exif"][piexif.ExifIFD.LensModel] = b"Hubble Space Telescope"

            # set exif data
            exif_bytes = piexif.dump(exif_dict)
            im.save(current_image, "jpeg", exif=exif_bytes)

            # set file data
            win_timestamp = datetime.datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S").timestamp() # convert to windows timestamp
            os.utime(current_image, (win_timestamp, win_timestamp)) # change access and modified time
            setctime(current_image, win_timestamp) # change creation time (windows)

            print_log(f"{current_image} -> {datetime_str}")
    print_log("")





def backup_folder():
    global BACKUP_CREATED
    try:
        user_desktop = Path.home() / "Desktop"
        backup_folder = os.path.basename(FOLDER) + "_backup"
        backup_path = user_desktop / backup_folder
        if os.path.isdir(backup_path):
            print_log(f"Es gibt bereits ein Backup für diesen Ordner - Bitte überprüfen:\n{backup_path}\n")
            raise Exception
        os.mkdir(user_desktop / backup_folder)
        count_files = 0
        for file in FILES:
            copyfile(FOLDER + "/" + file['name_old'], backup_path / file['name_old'])
            count_files += 1
        if os.path.isdir(backup_path) and count_files == len(FILES):
            BACKUP_CREATED = True
            print_log(f"Backup wurde erstellt unter:\n{backup_path}\n")
    except Exception:
        BACKUP_CREATED = False
        print_log("Backup konnte nicht erstellt werden - Abbruch\n")

def delete_non_images():
    global FILES
    for file in FILES:
        if file["filetype"] != "image":
            os.remove(os.path.join(FOLDER, file["name_old"]))
            print_log(f"Gelöscht: {file['name_old']}")
    print_log("")

def start_processing():
    global FOLDER, CHECKBOX_DELETE, CHECKBOX_NO_BACKUP, BACKUP_CREATED, DISORDER_FOUND, FILES
    FOLDER = folder_selection.get()
    if proceed_messagebox() == "yes":
        print_log("", clean=True) # clean the log when starting a new process
        if FOLDER:
            if os.path.isdir(FOLDER):
                print_log(f"Prüfe Bilder in:\n{FOLDER}\n")
                os.chdir(FOLDER)
                read_files()
                if FILES:
                    repair_order()
                    if DISORDER_FOUND:
                        if not CHECKBOX_NO_BACKUP:
                            backup_folder()
                            if BACKUP_CREATED:
                                rename_files()
                                timestamp_files()
                                if CHECKBOX_DELETE:
                                    delete_non_images()
                        else:
                            rename_files()
                            timestamp_files()
                            if CHECKBOX_DELETE:
                                delete_non_images()
                else:
                    print_log("Im Verzeichnis wurden keine Dateien gefunden\n")
            else:
                print_log("Das ausgewählte Verzeichnis existiert nicht\n")
        else:
            print_log("Es wurde kein Verzeichnis ausgewählt\n")
    else:
        print_log("Abbruch durch Benutzer\n")





""" 
Height of rectangles: 30.0
Width of rectangles: 250.0
Space between rectangles: 90.0
"""

# Initialize the main window
window = Tk()
window.geometry("900x625")
window.configure(bg="white")

# Basic Canvas Elements
canvas = Canvas(window, bg="white", height=625, width=911, bd=0, highlightthickness=0, relief="ridge")

# Background image
image_background = PhotoImage(file=relative_to_assets("background.png"))
canvas.create_image(455.0, 315.0, image=image_background)

# Left side log splitter
canvas.create_rectangle(0.0, 0.0, 472.0, 625.0, fill="#FBD4BC", outline="black")

# Place canvas
canvas.place(x=0, y=0)

# START BUTTON
image_start = PhotoImage(file=relative_to_assets("start.png"))
image_start_glow = PhotoImage(file=relative_to_assets("start_glow.png"))
start_canvas = canvas.create_image(675.0, 450.0, image=image_start)
canvas.tag_bind(start_canvas, "<Button-1>", lambda x: start_processing())
canvas.tag_bind(start_canvas, "<Enter>", lambda x: enter_start_image(start_canvas, image_start_glow))
canvas.tag_bind(start_canvas, "<Leave>", lambda x: leave_start_image(start_canvas, image_start))
def enter_start_image(canvas_id, image_start_glow):
    canvas.itemconfig(canvas_id, image=image_start_glow)
    canvas.config(cursor="hand2")
def leave_start_image(canvas_id, image_start):
    canvas.itemconfig(canvas_id, image=image_start)
    canvas.config(cursor="")

# Choose Directory
folder_selection = Entry(bd=0, bg="white", fg="black", highlightthickness=0, font=("Inter Medium", 12 * -1))
folder_selection.place(x=530.0, y=110.0, width=250.0, height=30.0)
folder_selection.insert(0, "Ordner auswählen")
# Folder image
image_folder = PhotoImage(file=relative_to_assets("folder.png"))
image_folder_glow = PhotoImage(file=relative_to_assets("folder_glow.png"))
folder_canvas = canvas.create_image(800.0, 93.0, image=image_folder, anchor="nw")
canvas.tag_bind(folder_canvas, "<Button-1>", lambda x: choose_directory())
canvas.tag_bind(folder_canvas, "<Enter>", lambda x: enter_folder_image(folder_canvas, image_folder_glow))
canvas.tag_bind(folder_canvas, "<Leave>", lambda x: leave_folder_image(folder_canvas, image_folder))
def enter_folder_image(canvas_id, image_folder_glow):
    canvas.itemconfig(canvas_id, image=image_folder_glow)
    canvas.config(cursor="hand2")
def leave_folder_image(canvas_id, image_folder):
    canvas.itemconfig(canvas_id, image=image_folder)
    canvas.config(cursor="")

# Checkbox Alles außer Bilder löschen
canvas.create_rectangle(530.0, 200.0, 780.0, 230.0, fill="white", outline="")
canvas.create_text(535.0, 205.0, anchor="nw", text="Alles außer Bilder löschen", fill="#000000", font=("Inter Medium", 16 * -1))
# Checkbox image for Alles außer Bilder löschen
image_delete_content_unchecked = PhotoImage(file=relative_to_assets("checkbox_unchecked.png"))
image_delete_content_checked = PhotoImage(file=relative_to_assets("checkbox_checked.png"))
delete_content_image_id = canvas.create_image(800.0, 200.0, image=image_delete_content_unchecked, anchor="nw")
canvas.tag_bind(delete_content_image_id, "<Button-1>", lambda x: toggle_checkbox('CHECKBOX_DELETE', delete_content_image_id, image_delete_content_checked, image_delete_content_unchecked))
canvas.tag_bind(delete_content_image_id, "<Enter>", lambda x: canvas.config(cursor="hand2"))
canvas.tag_bind(delete_content_image_id, "<Leave>", lambda x: canvas.config(cursor=""))

# Checkbox Keine Sicherung erstellen
canvas.create_rectangle(530.0, 290.0, 780.0, 320.0, fill="white", outline="")
canvas.create_text(535.0, 295.0, anchor="nw", text="Keine Sicherung erstellen", fill="#000000", font=("Inter Medium", 16 * -1))
# Checkbox image for Keine Sicherung erstellen
image_no_backup_unchecked = PhotoImage(file=relative_to_assets("checkbox_unchecked.png"))
image_no_backup_checked = PhotoImage(file=relative_to_assets("checkbox_checked.png"))
no_backup_image_id = canvas.create_image(800.0, 290.0, image=image_no_backup_unchecked, anchor="nw")
canvas.tag_bind(no_backup_image_id, "<Button-1>", lambda x: toggle_checkbox('CHECKBOX_NO_BACKUP', no_backup_image_id, image_no_backup_checked, image_no_backup_unchecked))
canvas.tag_bind(no_backup_image_id, "<Enter>", lambda x: canvas.config(cursor="hand2"))
canvas.tag_bind(no_backup_image_id, "<Leave>", lambda x: canvas.config(cursor=""))

# LOG
canvas.create_rectangle(47.0, 40.0, 425.0, 100.0, fill="#FBADB3", outline="black")
canvas.create_text(200.0, 55.0, anchor="nw", text="Log", fill="#000000", font=("Inter Medium", 25 * -1))
# Log output field with scrollbar
log_frame = tk.Frame(window)
log_frame.place(x=47.0, y=120.0, width=378.0, height=450.0)
log_output = scrolledtext.ScrolledText(log_frame, width=80, height=20, wrap=tk.WORD, font=("Inter Medium", 12 * -1))
log_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
log_output.config(state="disabled")
# Log image
image_log = PhotoImage(file=relative_to_assets("log.png"))
image_log_glow = PhotoImage(file=relative_to_assets("log_glow.png"))
log_canvas = canvas.create_image(414.0, 69.0, image=image_log)
canvas.tag_bind(log_canvas, "<Button-1>", lambda x: save_log())
canvas.tag_bind(log_canvas, "<Enter>", lambda x: enter_log_image(log_canvas, image_log_glow))
canvas.tag_bind(log_canvas, "<Leave>", lambda x: leave_log_image(log_canvas, image_log))
def enter_log_image(canvas_id, image_log_glow):
    canvas.itemconfig(canvas_id, image=image_log_glow)
    canvas.config(cursor="hand2")
def leave_log_image(canvas_id, image_log):
    canvas.itemconfig(canvas_id, image=image_log)
    canvas.config(cursor="")

# Version
canvas.create_text(10.0, 605.0, anchor="nw", text=f"Version {VERSION}", fill="#000000", font=("Inter Medium", 12 * -1))

# Finalize window settings
window.title("DiFo Repair Order - Bildreihenfolge reparieren")
window.resizable(False, False)
window.mainloop()
