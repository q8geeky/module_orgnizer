import tkinter as tk
from tkinter import filedialog, ttk
import os
import hashlib
import requests
import json
import threading
import time

# Constants
ALLOWED_EXTENSIONS = ['.pt', '.bin', '.ckpt', '.safetensors', '.pickle', '.pkl']
FOLDERS = ['Checkpoint', 'TextualInversion', 'LORA', 'VAE', 'LoCon']
API_ENDPOINT = "https://civitai.com/api/v1/model-versions/by-hash/"
TEMP_FILE = "temp_hashes.txt"
hash_cache = {}  # In-memory cache for file hashes


def compute_sha256(file_path):
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


def get_module_type(file_name, file_hash):
    """Get module type using the API or from the temp file."""
    # Check in memory cache first
    if file_name in hash_cache:
        return hash_cache[file_name]

    # Check in temp file
    with open(TEMP_FILE, 'a+', encoding='utf-8') as f:
        f.seek(0)
        lines = f.readlines()
        for line in lines:
            stored_name, stored_type = line.strip().split(':')
            if stored_name == file_name:
                hash_cache[file_name] = stored_type
                return stored_type

    # If not in cache or temp file, make API request
    try:
        response = requests.get(API_ENDPOINT + file_hash)
        response.raise_for_status()
        data = json.loads(response.text)
        module_type = data['model'].get('type', None)
        # Store in temp file and cache
        with open(TEMP_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{file_name}:{module_type}\n")
        hash_cache[file_name] = module_type
        return module_type
    except requests.RequestException as e:
        print(f"API request error: {e}")
    return None

def get_all_module_types(path, text_box, file_type_progress):
    """Get module types for all files in the directory."""
    file_types = {}
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and os.path.splitext(f)[1] in ALLOWED_EXTENSIONS]
    total_files = len(files)
    processed_files = 0

    for file in files:
        file_path = os.path.join(path, file)
        file_hash = compute_sha256(file_path)
        module_type = get_module_type(file, file_hash)
        file_types[file] = module_type

        # Displaying info in the text box
        text_box.insert(tk.END, f"Processing: {file}\nHash: {file_hash}\nModule Type: {module_type}\n\n")
        text_box.see(tk.END)  # Auto-scroll

        # Update file type progress bar
        processed_files += 1
        file_type_progress['value'] = (processed_files / total_files) * 100

    return file_types


def start_organizing(folder_path, text_box, progress, file_type_progress):
    def worker():
        path = folder_path.get()
        if not path:
            text_box.insert(tk.END, "Please select a folder first.\n")
            return

        # Create all folders at the start
        for folder in FOLDERS:
            dest_folder = os.path.join(path, folder)
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)

        file_types = get_all_module_types(path, text_box, file_type_progress)
        total_files = len(file_types)
        processed_files = 0

        for file, module_type in file_types.items():
            file_path = os.path.join(path, file)

            # Move the file to the appropriate folder
            if module_type in FOLDERS:
                dest_folder = os.path.join(path, module_type)
                dest_file_path = os.path.join(dest_folder, file)
                
                # Check if file already exists in the destination
                if os.path.exists(dest_file_path):
                    # Rename the file by appending a timestamp
                    dest_file_path = os.path.join(dest_folder, f"{int(time.time())}_{file}")

                try:
                    os.rename(file_path, dest_file_path)
                except Exception as e:
                    text_box.insert(tk.END, f"Error moving {file}: {str(e)}\n")

            # Update progress bar
            processed_files += 1
            progress['value'] = (processed_files / total_files) * 100

    # Use threading to prevent GUI hang
    thread = threading.Thread(target=worker)
    thread.start()


def select_folder(folder_path):
    folder_path.set(filedialog.askdirectory())


def main():
    app = tk.Tk()
    app.title("Module File Organizer")

    # Folder path string variable
    folder_path = tk.StringVar()

    # Text box for displaying file info
    text_box = tk.Text(app, height=10, width=50)
    text_box.pack(pady=20)

    # Progress bar for file organization
    progress = ttk.Progressbar(app, orient="horizontal", length=300, mode="determinate")
    progress.pack(pady=20)

    # Progress bar for file types
    file_type_progress = ttk.Progressbar(app, orient="horizontal", length=300, mode="determinate")
    file_type_progress.pack(pady=20)

    # Buttons
    select_button = tk.Button(app, text="Select Folder", command=lambda: select_folder(folder_path))
    select_button.pack(pady=10)

    start_button = tk.Button(app, text="Start Organizing", command=lambda: start_organizing(folder_path, text_box, progress, file_type_progress))
    start_button.pack(pady=10)

    app.mainloop()


if __name__ == "__main__":
    # Create temp file on start
    with open(TEMP_FILE, 'a') as f:
        pass

    main()

    # Delete temp file on exit
    os.remove(TEMP_FILE)
