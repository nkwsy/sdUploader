import logging
import webbrowser
from tkinter import *
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from utils.copy_tools import FileManifest, CopyThread, write_manifest_file
from utils.card_metadata import (write_info_file, write_uploaded_marker_file, write_camera_info_file,
                                 create_upload_folder, find_download_metadata)
import webbrowser

class CompletedJob:
    def __init__(self, download_path, upload_path, camera_info, file_manifest, status="Uploaded"):
        self.download_path = download_path
        self.upload_path = upload_path
        self.camera_info = camera_info
        self.file_manifest = file_manifest
        self.status = status




class UploadThread(CopyThread):
    def __init__(self, download_path, upload_path, camera_info, file_manifest):
        super().__init__(download_path,
                         upload_path,
                         camera_info=camera_info,
                         total_size=file_manifest.file_total_size,
                         total_files=file_manifest.file_count,
                         modification_range=file_manifest.modification_range,
                         file_manifest=file_manifest)
        self.download_path = download_path
        self.upload_path = upload_path
        self.camera_info = camera_info
        self.file_manifest = file_manifest
        # make sure the manifest is written as complete with the upload path in both locations
        self.file_manifest.upload_state = "complete"
        self.file_manifest.upload_path = str(upload_path)
        self.status = self.get_progress_string()

    def progress_callback(self, current_size, current_files, total_size, total_files):
        super().progress_callback(current_size, current_files, total_size, total_files)
        self.status = self.get_progress_string()

    def write_metadata_files(self):
        write_info_file(self.upload_path, self.camera_info, self.file_manifest)
        write_camera_info_file(self.upload_path, self.camera_info)
        write_uploaded_marker_file(self.download_path, self.upload_path)
        write_manifest_file(self.download_path, self.file_manifest)

        super().write_metadata_files()

    def run(self):
        try:
            super().run()
            self.status = "Uploaded"
        except Exception as e:
            msg = f"Error uploading files: {str(e)}"
            logging.error(msg)
            self.error_message = msg
            self.status = "Error"






class UploadManager:

    def __init__(self, master):
        self.upload_queue = []
        self.upload_threads = []
        self.master = master
        self.titleLabel = tk.Label(self.master, text="Upload Manager", font=("Comic Sans MS", 16, "bold"), fg="purple")


        #self.navbar = ttk.Frame(self.master)
        #self.navbar.grid(row=1, sticky=tk.W + tk.E + tk.N + tk.S, padx=10, pady=10)

        self.upload_queue_treeview = ttk.Treeview(self.master, columns=(
            'name',
            'file_count',
            'total_size',
            'status',
            'download_path',
            'upload_path'
        ))
        treeview = self.upload_queue_treeview
        treeview.column("#0", width=0, stretch=tk.NO)
        treeview.column("name", width=180)
        treeview.column("file_count", width=70)
        treeview.column("total_size", width=100)
        treeview.column("status", width=100)
        treeview.column("download_path", width=300)
        treeview.column("upload_path", width=300)
        treeview.heading("name", text="Name")
        treeview.heading("file_count", text="File Count")
        treeview.heading("total_size", text="Total Size")
        treeview.heading("status", text="Status")
        treeview.heading("download_path", text="Download Path")
        treeview.heading("upload_path", text="Upload Path")
        #treeview.grid(row=0, column=0, sticky='nsew')

        self.tree_scroll = ttk.Scrollbar(self.master, orient='vertical', command=self.upload_queue_treeview.yview)
        self.upload_queue_treeview.config(yscrollcommand=self.tree_scroll.set)


        self.titleLabel.grid(row=0, column=0, pady=20)
        self.upload_queue_treeview.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        self.upload_queue_treeview.bind("<Double-1>", self.OnDoubleClick)
        self.tree_scroll.grid(row=1, column=1, sticky='ns')


        #self.upload_queue_tab = ttk.Frame(self.navbar)
        #self.navbar.add(self.upload_queue_tab, text="Upload Queue")


        self.upload_queue_frames = []

        self.load_completed_jobs()


    def OnDoubleClick(self, event):
        item = self.upload_queue_treeview.identify_row(event.y)
        if item:
            column = self.upload_queue_treeview.identify_column(event.x)
            if column == "#6":
                upload_path = self.upload_queue_treeview.item(item, "values")[5]
                logging.debug(f"Double clicked on {upload_path}")
                webbrowser.open(f"file://{upload_path}")
            elif column == "#5":
                download_path = self.upload_queue_treeview.item(item, "values")[4]
                logging.debug(f"Double clicked on {download_path}")
                webbrowser.open(f"file://{download_path}")
        else:
            logging.debug("Double clicked on nothing")

    def update_upload_queue_tab(self, new_upload_job=None):
        # We're going to move completed jobs to a different queue in a bit (but not now)
        for index, upload_job in enumerate(self.upload_queue):
            self.upload_queue_treeview.delete(index)
        if new_upload_job:
            self.upload_queue.append(new_upload_job)
        self.upload_queue.sort(reverse=True, key=lambda x: x.download_path.name)
        live_jobs = False
        for index, upload_job in enumerate(self.upload_queue):
            if isinstance(upload_job, UploadThread) and upload_job.is_alive():
                live_jobs = True
            self.upload_queue_treeview.insert('', index, index, values=(
                upload_job.download_path.name,
                upload_job.file_manifest.file_count,
                f"{round(upload_job.file_manifest.file_total_size / (1024.0 ** 3), 2)} GB",
                upload_job.status,
                upload_job.download_path,
                upload_job.upload_path))
        if live_jobs:
            self.master.after(100, self.update_upload_queue_tab)

    def is_working(self):
        for upload_job in self.upload_queue:
            if isinstance(upload_job, UploadThread) and upload_job.is_alive():
                return True
        return False

    def load_completed_jobs(self):
        download_metadata = find_download_metadata()
        for download_folder, manifest in download_metadata:
            job = CompletedJob(download_folder, manifest.upload_path, manifest.camera_info, manifest)
            self.update_upload_queue_tab(job)


    def add_upload_job(self, download_path, file_manifest):
        logging.debug(f"Adding upload job for {download_path} with manifest {file_manifest}")


        upload_path = create_upload_folder(file_manifest.camera_info.date,
                                           file_manifest.camera_info.camera,
                                           file_manifest.camera_info.location,
                                           file_manifest.camera_info.cameraid)

        logging.debug("Starting upload thread")
        upload_job = UploadThread(download_path, upload_path, file_manifest.camera_info, file_manifest)
        upload_job.start()

        self.update_upload_queue_tab(upload_job)










