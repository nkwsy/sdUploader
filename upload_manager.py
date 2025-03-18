from tkinter import *
import tkinter as tk
from tkinter import ttk

from utils.copy_tools import FileManifest

class UploadJob:
    def __init__(self, download_path, upload_path, file_manifest):
        self.download_path = download_path
        self.upload_path = upload_path
        self.file_manifest = file_manifest
        self.status = "pending"
        self.progress = 0
        self.error = None
        self.start_time = None
        self.end_time = None
        self.duration = None

class UploadManager:

    def __init__(self, master):
        self.master = master
        self.upload_manager_window = tk.Toplevel()
        self.upload_manager_window.title("Upload Manager")
        self.upload_manager_window.geometry("300x200")
        self.upload_queue = []
        button_close = ttk.Button(
            self.upload_manager_window,
            text="Close window",
            command=self.destroy)
        button_close.place(x=75, y=75)

    def destroy(self):
        self.master.remove_upload_manager()
        self.upload_manager_window.destroy()



    def add_upload_job(self, download_path, file_manifest):
        self.upload_queue.append((download_path, file_manifest))
