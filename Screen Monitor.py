import json
from pathlib import Path
import tkinter as tk
from tkinter import font


class BankingQueueMonitor:
    def __init__(self, root):
        self.root = root
        self.state_path = Path(__file__).with_name("queue_state.json")
        self.root.title("Banking Queue Monitor System")
        self.root.state("zoomed")
        self.root.configure(bg="#1a1a1a")

        self.title_font = font.Font(family="Arial", size=28, weight="bold")
        self.ticket_font = font.Font(family="Arial", size=112, weight="bold")
        self.consultant_font = font.Font(family="Arial", size=32, weight="bold")
        self.message_font = font.Font(family="Arial", size=20, weight="bold")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=3)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)

        self.setup_display()
        self.refresh_state()

    def setup_display(self):
        status_label = tk.Label(
            self.root, text="NOW SERVING", font=self.title_font,
            fg="#00ffcc", bg="#1a1a1a",
        )
        status_label.grid(row=0, column=0, pady=(24, 8))

        self.lbl_ticket = tk.Label(
            self.root, text="---", font=self.ticket_font,
            fg="#ffffff", bg="#262626", relief="flat",
        )
        self.lbl_ticket.grid(row=1, column=0, sticky="nsew", padx=100, pady=(10, 20))

        self.lbl_counter = tk.Label(
            self.root, text="CONSULTANT --", font=self.consultant_font,
            fg="#ffcc00", bg="#1a1a1a",
        )
        self.lbl_counter.grid(row=2, column=0, pady=10)

        message_label = tk.Label(
            self.root, text="THANK YOU FOR YOUR PATIENCE", font=self.message_font,
            fg="#aaaaaa", bg="#1a1a1a",
        )
        message_label.grid(row=3, column=0, pady=(10, 24), sticky="s")

    def refresh_state(self):
        try:
            with self.state_path.open(encoding="utf-8") as state_file:
                state = json.load(state_file)
        except (OSError, json.JSONDecodeError):
            state = {}

        consultants = state.get("consultants", [])
        active = [consultant for consultant in consultants if consultant.get("ticket")]

        if active:
            consultant = active[0]
            ticket = consultant["ticket"]
            self.lbl_ticket.config(text=f"{ticket['ticket_number']:03}")
            self.lbl_counter.config(text=f"CONSULTANT {consultant['id']}")
        else:
            self.lbl_ticket.config(text="---")
            self.lbl_counter.config(text="CONSULTANT --")

        self.root.after(1000, self.refresh_state)


if __name__ == "__main__":
    window = tk.Tk()
    app = BankingQueueMonitor(window)
    window.mainloop()