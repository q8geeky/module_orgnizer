import os
import requests
import json
import time
import cloudscraper
from tkinter import Tk, Label, Button, Entry, filedialog, messagebox, Toplevel, Scrollbar, Text, Y, Frame, StringVar
from tkinter.ttk import Progressbar

class CivitaiOrganizer:
    def __init__(self, master):
        self.master = master
        master.title("Civitai Module Organizer")

        self.api_key_label = Label(master, text="Enter Civitai API Key:")
        self.api_key_label.pack()

        self.api_key_var = StringVar()
        self.api_key_var.trace("w", self.mask_api_key)
        self.api_key_entry = Entry(master, textvariable=self.api_key_var, show="*")
        self.api_key_entry.pack()

        self.folder_label = Label(master, text="Specify 'modules' folder:")
        self.folder_label.pack()

        self.folder_entry = Entry(master)
        self.folder_entry.pack()

        self.browse_button = Button(master, text="Browse", command=self.browse_folder)
        self.browse_button.pack()

        self.organize_button = Button(master, text="Organize Modules", command=self.organize_modules)
        self.organize_button.pack()

        self.progress_frame = Frame(master)
        self.progress_frame.pack(pady=20)

        # Scanning Progress Bar
        self.progress_label1 = Label(self.progress_frame, text="Scanning Progress:")
        self.progress_label1.pack()
        self.progress = Progressbar(self.progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.pack()

        # Reading Temp File Progress Bar
        self.progress_label3 = Label(self.progress_frame, text="Reading Temp File Progress:")
        self.progress_label3.pack()
        self.progress_read = Progressbar(self.progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_read.pack()

        # Moving Progress Bar
        self.progress_label2 = Label(self.progress_frame, text="Moving Progress:")
        self.progress_label2.pack()
        self.progress_move = Progressbar(self.progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_move.pack()

        self.output_text = Text(master, height=10, width=50)
        self.output_text.pack(pady=20)
        self.scroll = Scrollbar(master, command=self.output_text.yview)
        self.scroll.pack(side="right", fill="y")
        self.output_text.configure(yscrollcommand=self.scroll.set)

    def mask_api_key(self, *args):
        if self.api_key_entry.focus_get() != self.api_key_entry:  # Mask only when focus is out
            api_key = self.api_key_var.get()
            masked_key = '*' * len(api_key)
            self.api_key_var.set(masked_key)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, folder_selected)
    
    def organize_modules(self):
        api_key = self.api_key_entry.get()
        folder_path = self.folder_entry.get()

        if not api_key or not folder_path:
            messagebox.showerror("Error", "API Key and Folder Path are required!")
            return

        # Verify API Key
        test_response = requests.get("https://civitai.com/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        if test_response.status_code != 200:
            messagebox.showerror("Error", "Invalid API Key!")
            return

        allowed_extensions = ['.pt', '.bin', '.ckpt', '.safetensors', '.pickle', '.pkl']
        module_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and any(f.endswith(ext) for ext in allowed_extensions)]
        temp_file_path = "temp_response.txt"

        with open(temp_file_path, "w", encoding="utf-8") as temp_file:
            for idx, module_file in enumerate(module_files):
                self.output_text.insert("end", f"Scanning: {module_file}\n")
                self.output_text.see("end")
                self.master.update()

                try:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    response = requests.get(f"https://civitai.com/api/v1/models?name={module_file}", headers=headers)
            
                    if response.status_code < 400:  # Check for successful status codes
                        content = response.json()
                        if 'data' in content and 'type' in content['data']:  # Corrected extraction of 'type'
                            temp_file.write(content['data']['type'] + "\n")
                        else:
                            self.output_text.insert("end", f"Module {module_file} not recognized or deprecated.\n")
                    else:
                        self.output_text.insert("end", f"Error fetching API response for {module_file}: {response.status_code}\n")


                except Exception as e:
                    self.output_text.insert("end", f"Error fetching API response for {module_file}: {str(e)}\n")

                self.progress["value"] = (idx + 1) / len(module_files) * 100
                self.master.update()
                time.sleep(5) 

        # Optional: Add a delay (not necessary but can be added for safety)
        # time.sleep(1)
        # Read API responses and move files
        if os.path.exists(temp_file_path):
            with open(temp_file_path, "r", encoding="utf-8") as temp_file:
                module_types = temp_file.readlines()
                for idx, module_type in enumerate(module_types):
                    module_type = module_type.strip()
                    if module_type in ["checkpoint", "embedding", "lora", "lycoris", "vae"]:
                        subfolder_path = os.path.join(folder_path, module_type)
                        if not os.path.exists(subfolder_path):
                            os.makedirs(subfolder_path)
                        os.rename(os.path.join(folder_path, module_files[idx]), os.path.join(subfolder_path, module_files[idx]))
                        self.output_text.insert("end", f"Moved {module_files[idx]} to {subfolder_path}\n")
                        self.output_text.see("end")  # Auto-scroll

                    self.output_text.insert("end", f"Reading response for module: {module_files[idx]}\n")
                    self.output_text.see("end")
                    self.master.update()
                    
                    try:
                       # Use json.loads instead of eval
                        content = json.loads(line.strip())
                        responses.append(content)
                    except Exception as e:
                        self.output_text.insert("end", f"Error processing response for module {module_files[idx]}: {str(e)}\n")

                    self.progress_read["value"] = (idx + 1) / len(module_files) * 100
                    self.master.update()

if __name__ == "__main__":
    root = Tk()
    app = CivitaiOrganizer(root)
    root.mainloop()
