import logging
from tkinter import *
import tkinter as tk
from tkinter import ttk
from pathlib import Path

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

    def __init__(self, main_window):
        self.main_window = main_window
        self.master = tk.Toplevel()
        self.master.title("Upload Manager")
        self.master.geometry("800x600")

        self.upload_queue = []

        self.titleLabel = tk.Label(self.master, text="Upload Manager", font=("Comic Sans MS", 16, "bold"), fg="purple")


        #self.navbar = ttk.Frame(self.master)
        #self.navbar.grid(row=1, sticky=tk.W + tk.E + tk.N + tk.S, padx=10, pady=10)

        self.upload_queue_treeview = ttk.Treeview(self.master, columns=(
            'name',
            'file_count',
            'total_size',
            'status',
            'progress',
            'download_path'
        ))
        treeview = self.upload_queue_treeview
        treeview.column("#0", width=0, stretch=tk.NO)
        treeview.column("name", width=200)
        treeview.column("file_count", width=100)
        treeview.column("total_size", width=100)
        treeview.column("status", width=100)
        treeview.column("progress", width=100)
        treeview.column("download_path", width=200)
        treeview.heading("name", text="Name")
        treeview.heading("file_count", text="File Count")
        treeview.heading("total_size", text="Total Size")
        treeview.heading("status", text="Status")
        treeview.heading("progress", text="Progress")
        treeview.heading("download_path", text="Download Path")

        self.tree_scroll = ttk.Scrollbar(self.master, orient='vertical', command=self.upload_queue_treeview.yview)
        self.upload_queue_treeview.config(yscrollcommand=self.tree_scroll.set)


        self.titleLabel.grid(row=0, column=0, pady=20)
        self.upload_queue_treeview.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.tree_scroll.grid(row=1, column=1, sticky='ns')


        #self.upload_queue_tab = ttk.Frame(self.navbar)
        #self.navbar.add(self.upload_queue_tab, text="Upload Queue")


        self.upload_queue_frames = []




        #button_close = ttk.Button(
        #    self.master,
        #    text="Close window",
        #    command=self.destroy)
        #button_close.place(x=75, y=75)

    def destroy(self):
        self.main_window.remove_upload_manager()
        self.master.destroy()

    def update_upload_queue_tab(self, new_upload_job=None):
        # We're going to move completed jobs to a different queue in a bit (but not now)
        for index, upload_job in enumerate(self.upload_queue):
            self.upload_queue_treeview.delete(index)
        self.upload_queue.append(new_upload_job)
        for index, upload_job in enumerate(self.upload_queue):
            self.upload_queue_treeview.insert('', index, index, values=(
                upload_job.download_path.name,
                upload_job.file_manifest.file_count,
                upload_job.file_manifest.file_total_size,
                upload_job.status,
                upload_job.progress,
                upload_job.download_path))





    def add_upload_job(self, download_path, file_manifest):
        logging.debug(f"Adding upload job for {download_path} with manifest {file_manifest}")
        upload_job = UploadJob(download_path, None, file_manifest)
        self.update_upload_queue_tab(upload_job)




