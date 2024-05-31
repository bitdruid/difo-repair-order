import sys
import os
import magic
import re
import datetime
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
    file = filedialog.asksaveasfile(mode="w", title="Save log", initialfile="diforepairorder_" + date, defaultextension=".log", filetypes=[("Text files", "*.txt")])
    if file:
        file.write(log_content)

def proceed_messagebox():
    message = f"Verzeichnis:\n{FOLDER}\n\n"
    if CHECKBOX_DELETE:
        message += "- Alles außer Bilder wird gelöscht\n"
    if CHECKBOX_NO_BACKUP:
        message += "- Es wird keine Sicherung erstellt\n"
    message += "\nACHTUNG!\nDateien in diesem Ordner werden umbenannt und/oder gelöscht! Der Zielpfad sollte am besten der Ordner auf der SD-Karte der Kamera sein!\n"
    message += "\nFortfahren?"
    return tk.messagebox.askquestion("Einstellungen prüfen", message, icon="warning")

def choose_directory():
    directory = filedialog.askdirectory()
    if directory:
        print_log("", clean=True)
        print_log("Selected directory:\n" + directory + "\n")
        folder_selection.delete(0, tk.END)
        folder_selection.insert(0, directory)
        directory_files = os.listdir(directory)
        print_log("Files in selected directory:\n")
        for file in directory_files:
            print_log(f"- {file}")
        print_log("")

def read_files():
    global FILES
    FILES = []
    for file in os.listdir(FOLDER):
        file_path = os.path.join(FOLDER, file)
        file_info = {
            "name_old": file,
            "name_new": "",
            "filetype": magic.Magic(mime=True).from_file(file_path).split("/")[0]
        }
        FILES.append(file_info)
    pprint(FILES)

def repair_order():
    global FILES, DISORDER_FOUND
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
                        file["name_new"] = file["name_old"].replace(str(number), str(files_last_correct_number + 1))
                        files_last_correct_number += 1
    if DISORDER_FOUND:
        print_log("Disordered images found\n")
    else:
        print_log("No disordered images found\n")

    pprint(FILES)

def rename_files():
    global FILES
    print_log("Renaming files:")
    for file in FILES:
        if file["name_new"]:
            os.rename(file["name_old"], file["name_new"])
            print_log(f"Old: {file['name_old']} -> New: {file['name_new']}")
    print_log("")

def backup_folder():
    global BACKUP_CREATED
    BACKUP_CREATED = True
    try:
        user_desktop = Path.home() / "Desktop"
        backup_folder = os.path.basename(FOLDER) + "_backup"
        backup_path = user_desktop / backup_folder
        if os.path.isdir(backup_path):
            print_log("There is already a backup - Please check\n")
            raise Exception
        os.mkdir(user_desktop / backup_folder)
        for file in FILES:
            copyfile(FOLDER + "/" + file['name_old'], backup_path / file['name_old'])
        print_log("Backup created at " + str(backup_path) + "\n")
    except Exception:
        BACKUP_CREATED = False
        print_log("Could not create backup - aborting\n")

def delete_non_images():
    global FILES
    for file in FILES:
        if file["filetype"] != "image":
            os.remove(os.path.join(FOLDER, file["name_old"]))
            print_log(f"Deleted: {file['name_old']}")
    print_log("")

def start_processing():
    global FOLDER, CHECKBOX_DELETE, CHECKBOX_NO_BACKUP, BACKUP_CREATED, DISORDER_FOUND, FILES
    FOLDER = folder_selection.get()
    if proceed_messagebox() == "yes":
        print_log("", clean=True)
        if FOLDER:
            if os.path.isdir(FOLDER):
                print_log("Searching in:\n" + FOLDER + "\n")
                os.chdir(FOLDER)
                read_files()
                if FILES:
                    repair_order()
                    if DISORDER_FOUND:
                        if not CHECKBOX_NO_BACKUP:
                            backup_folder()
                            if BACKUP_CREATED:
                                rename_files()
                                if CHECKBOX_DELETE:
                                    delete_non_images()
                        else:
                            rename_files()
                            if CHECKBOX_DELETE:
                                delete_non_images()
                else:
                    print_log("No files found in directory\n")
            else:
                print_log("Directory does not exist\n")
        else:
            print_log("No directory selected\n")
    else:
        print_log("Aborted by user\n")

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
start_canvas = canvas.create_image(675.0, 450.0, image=image_start)
canvas.tag_bind(start_canvas, "<Button-1>", lambda x: start_processing())
canvas.tag_bind(start_canvas, "<Enter>", lambda x: canvas.config(cursor="hand2"))
canvas.tag_bind(start_canvas, "<Leave>", lambda x: canvas.config(cursor=""))

# Choose Directory
folder_selection = Entry(bd=0, bg="white", fg="black", highlightthickness=0, font=("Inter Medium", 12 * -1))
folder_selection.place(x=530.0, y=110.0, width=250.0, height=30.0)
folder_selection.insert(0, "Choose Directory")
# Folder image
image_folder = PhotoImage(file=relative_to_assets("folder.png"))
folder_canvas = canvas.create_image(800.0, 93.0, image=image_folder, anchor="nw")
canvas.tag_bind(folder_canvas, "<Button-1>", lambda x: choose_directory())
canvas.tag_bind(folder_canvas, "<Enter>", lambda x: canvas.config(cursor="hand2"))
canvas.tag_bind(folder_canvas, "<Leave>", lambda x: canvas.config(cursor=""))

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
log_canvas = canvas.create_image(414.0, 69.0, image=image_log)
canvas.tag_bind(log_canvas, "<Button-1>", lambda x: save_log())
canvas.tag_bind(log_canvas, "<Enter>", lambda x: canvas.config(cursor="hand2"))
canvas.tag_bind(log_canvas, "<Leave>", lambda x: canvas.config(cursor=""))

# Version
canvas.create_text(10.0, 605.0, anchor="nw", text=f"Version {VERSION}", fill="#000000", font=("Inter Medium", 12 * -1))

# Finalize window settings
window.title("DiFo Repair Order - Bildreihenfolge reparieren")
window.resizable(False, False)
window.mainloop()
