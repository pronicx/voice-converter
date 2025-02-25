import tkinter as tk
from tkinter import ttk

class StatusBarComponent:
    def __init__(self, parent):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        self.status_bar = ttk.Label(
            parent, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def set_status(self, message):
        """Update the status bar with a message"""
        self.status_var.set(message) 