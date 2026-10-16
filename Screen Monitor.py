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
        self.large_display_font = font.Font(family="Arial", size=72, weight="bold")
        self.counter_font = font.Font(family="Arial", size=32, weight="bold")
        self.sidebar_title_font = font.Font(family="Arial", size=22, weight="bold")
        self.sidebar_data_font = font.Font(family="Arial", size=20, weight="bold")

        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.setup_main_display()
        self.setup_sidebar_history()
        self.refresh_state()

    def setup_main_display(self):
        main_frame = tk.Frame(self.root, bg="#1a1a1a", bd=0, highlightthickness=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=2)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_rowconfigure(3, weight=0)

        status_label = tk.Label(
            main_frame, text="NOW SERVING", font=self.title_font,
            fg="#00ffcc", bg="#1a1a1a",
        )
        status_label.grid(row=0, column=0, pady=(0, 10))

        self.lbl_ticket = tk.Label(
            main_frame, text="---", font=self.large_display_font,
            fg="#ffffff", bg="#262626", width=10, relief="flat", bd=10,
        )
        self.lbl_ticket.grid(row=1, column=0, ipady=30)

        self.lbl_counter = tk.Label(
            main_frame, text="WAITING FOR NEXT CLIENT", font=self.counter_font,
            fg="#ffcc00", bg="#1a1a1a",
        )
        self.lbl_counter.grid(row=2, column=0, pady=(20, 0))

        self.lbl_queue = tk.Label(
            main_frame, text="Clients waiting: 0", font=self.sidebar_title_font,
            fg="#aaaaaa", bg="#1a1a1a",
        )
        self.lbl_queue.grid(row=3, column=0, pady=(12, 0))

    def setup_sidebar_history(self):
        self.sidebar_frame = tk.Frame(self.root, bg="#262626", width=300)
        self.sidebar_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=40)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(1, weight=1)

        history_title = tk.Label(
            self.sidebar_frame, text="RECENT CALLS", font=self.sidebar_title_font,
            fg="#aaaaaa", bg="#262626",
        )
        history_title.grid(row=0, column=0, columnspan=2, pady=30, sticky="n")
        self.history_rows = []

    def refresh_state(self):
        try:
            with self.state_path.open(encoding="utf-8") as state_file:
                state = json.load(state_file)
        except (OSError, json.JSONDecodeError):
            state = {}

        waiting_queue = state.get("waiting_queue", [])
        consultants = state.get("consultants", [])
        recent_calls = state.get("recent_calls", [])
        active = [consultant for consultant in consultants if consultant.get("ticket")]

        if active:
            consultant = active[0]
            ticket = consultant["ticket"]
            self.lbl_ticket.config(text=f"{ticket['ticket_number']:03}")
            self.lbl_counter.config(text=f"COUNTER {consultant['id']}  |  {ticket['service']}")
        else:
            self.lbl_ticket.config(text="---")
            self.lbl_counter.config(text="WAITING FOR NEXT CLIENT")

        self.lbl_queue.config(text=f"Clients waiting: {len(waiting_queue)}")
        for row in self.history_rows:
            for label in row:
                label.destroy()
        self.history_rows.clear()

        for index, call in enumerate(recent_calls[:8], start=1):
            ticket_label = tk.Label(
                self.sidebar_frame, text=f"{call['ticket_number']:03}",
                font=self.sidebar_data_font, fg="#ffffff", bg="#262626",
            )
            ticket_label.grid(row=index, column=0, pady=10, padx=20, sticky="w")
            counter_label = tk.Label(
                self.sidebar_frame, text=f"Counter {call['consultant_id']}",
                font=self.sidebar_data_font, fg="#aaaaaa", bg="#262626",
            )
            counter_label.grid(row=index, column=1, pady=10, padx=20, sticky="e")
            self.history_rows.append((ticket_label, counter_label))

        self.root.after(1000, self.refresh_state)


if __name__ == "__main__":
    window = tk.Tk()
    app = BankingQueueMonitor(window)
    window.mainloop()