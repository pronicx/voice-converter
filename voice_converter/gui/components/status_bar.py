import tkinter as tk
from tkinter import ttk

class StatusBarComponent:
    def __init__(self, parent):
        self.parent = parent
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            parent, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(10, 5)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.set_status("Ready")
    
    def set_status(self, message, error=False):
        """Update the status bar message
        
        Args:
            message: The message to display
            error: Whether this is an error message (will be displayed differently)
        """
        self.status_var.set(message)
        
        # Ändere die Darstellung je nach Fehlertyp
        if error:
            self.status_bar.configure(foreground="red")
        else:
            self.status_bar.configure(foreground="black") 