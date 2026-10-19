"""Responsive desktop frontend for the model organizer."""
from __future__ import annotations
import queue
import threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from organizer_core import organize


def main():
    root=tk.Tk()
    root.title("Civitai Model Organizer")
    root.minsize(680,460)
    folder=tk.StringVar()
    dry_run=tk.BooleanVar(value=True)
    recursive=tk.BooleanVar(value=False)
    offline=tk.BooleanVar(value=False)
    progress=tk.DoubleVar(value=0)
    work_queue=queue.Queue()
    frame=ttk.Frame(root,padding=14)
    frame.pack(fill="both",expand=True)
    frame.columnconfigure(1,weight=1)
    ttk.Label(frame,text="Model folder").grid(row=0,column=0,sticky="w")
    ttk.Entry(frame,textvariable=folder).grid(row=0,column=1,sticky="ew",padx=8)
    ttk.Button(frame,text="Browse",command=lambda:folder.set(filedialog.askdirectory())).grid(row=0,column=2)
    ttk.Checkbutton(frame,text="Dry run (preview only; no files moved)",variable=dry_run).grid(
        row=1,column=0,columnspan=3,sticky="w",pady=10)
    toggles=ttk.Frame(frame)
    toggles.grid(row=2,column=0,columnspan=3,sticky="w")
    ttk.Checkbutton(toggles,text="Scan subfolders",variable=recursive).pack(side="left",padx=(0,14))
    ttk.Checkbutton(toggles,text="Offline (cache only)",variable=offline).pack(side="left")
    bar=ttk.Progressbar(frame,maximum=100,variable=progress)
    bar.grid(row=3,column=0,columnspan=3,sticky="ew",pady=6)
    log=tk.Text(frame,wrap="word",height=15)
    log.grid(row=4,column=0,columnspan=3,sticky="nsew")
    frame.rowconfigure(4,weight=1)
    status=tk.StringVar(value="Ready")
    ttk.Label(frame,textvariable=status).grid(row=5,column=0,columnspan=3,sticky="w")
    start=ttk.Button(frame,text="Preview organization")
    start.grid(row=6,column=0,columnspan=3,pady=10)

    def append(message):
        log.insert("end",message+"\n")
        log.see("end")

    def worker(path,preview,scan_subfolders,cache_only):
        try:
            stats=organize(Path(path),dry_run=preview,
                           recursive=scan_subfolders,offline=cache_only,
                           on_progress=lambda e:work_queue.put(("progress",e)))
            work_queue.put(("done",stats))
        except Exception as exc:
            work_queue.put(("error",str(exc)))

    def run():
        if not Path(folder.get()).is_dir():
            messagebox.showerror("Folder required","Choose an existing folder.")
            return
        if not dry_run.get() and not messagebox.askyesno(
                "Move model files","Move resolved model files into category folders?"):
            return
        log.delete("1.0","end")
        progress.set(0)
        start.configure(state="disabled")
        status.set("Working...")
        threading.Thread(target=worker,
                         args=(folder.get(),dry_run.get(),recursive.get(),offline.get()),
                         daemon=True).start()

    def poll():
        try:
            while True:
                kind,data=work_queue.get_nowait()
                if kind=="progress":
                    index,total,name,result=data
                    progress.set(100*index/max(total,1))
                    append(f"{name}: {result}")
                elif kind=="done":
                    status.set(", ".join(f"{k}: {v}" for k,v in data.items()))
                    start.configure(state="normal")
                    progress.set(100)
                else:
                    status.set("Error")
                    append(data)
                    start.configure(state="normal")
        except queue.Empty:
            pass
        root.after(100,poll)

    dry_run.trace_add("write",lambda *_:start.configure(
        text="Preview organization" if dry_run.get() else "Organize files"))
    start.configure(command=run)
    root.after(100,poll)
    root.mainloop()


if __name__=="__main__":
    main()
