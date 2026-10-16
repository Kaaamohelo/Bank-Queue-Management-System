import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from queue_core import (
    advance_time,
    cancel_ticket,
    mark_client_arrived,
    record_staff_action,
    read_monitor_state,
    serve_next_client,
)


COLORS = {
    "background": "#F1F4F2",
    "surface": "#FFFFFF",
    "ink": "#1F302B",
    "muted": "#65756E",
    "line": "#DCE4DF",
    "green": "#164C3D",
    "green_light": "#E3F1EA",
    "amber": "#A65E13",
    "amber_light": "#FFF0D9",
    "red": "#A33832",
}


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _ticket_number(value):
    return f"{_as_int(value):03}"


class StaffQueueMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Bank Queue | Staff Monitor")
        self.root.geometry("1360x860")
        self.root.minsize(1180, 720)
        self.root.state("zoomed")
        self.root.configure(bg=COLORS["background"])

        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.style.configure(
            "Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["ink"],
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Treeview.Heading",
            background="#E9EFEB",
            foreground=COLORS["muted"],
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        self.style.map(
            "Treeview",
            background=[("selected", COLORS["green_light"])],
            foreground=[("selected", COLORS["ink"])],
        )

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.refresh_state()

    def _build_layout(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.container = tk.Frame(self.root, bg=COLORS["background"])
        self.container.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_summary()
        self.body = tk.Frame(self.container, bg=COLORS["background"])
        self.body.grid(row=2, column=0, sticky="nsew")
        self.body.grid_columnconfigure(0, weight=4, uniform="dashboard-columns")
        self.body.grid_columnconfigure(1, weight=4, uniform="dashboard-columns")
        self.body.grid_columnconfigure(2, weight=3, uniform="dashboard-columns")
        self.body.grid_columnconfigure(3, weight=6, uniform="dashboard-columns")
        self.body.grid_rowconfigure(0, weight=1)
        self._build_controls()
        self._build_tables()

    def _build_header(self):
        header = tk.Frame(self.container, bg=COLORS["green"], padx=22, pady=16)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="STAFF QUEUE MONITOR",
            bg=COLORS["green"],
            fg="#FFFFFF",
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text="Branch operations",
            bg=COLORS["green"],
            fg="#C4D9CF",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))

        self.connection_label = tk.Label(
            header,
            text="LIVE",
            bg="#D5E9DE",
            fg=COLORS["green"],
            padx=12,
            pady=5,
            font=("Segoe UI", 9, "bold"),
        )
        self.connection_label.grid(row=0, column=1, sticky="e")
        self.updated_label = tk.Label(
            header,
            text="Waiting for update",
            bg=COLORS["green"],
            fg="#D5E2DC",
            font=("Segoe UI", 9),
        )
        self.updated_label.grid(row=1, column=1, sticky="e", pady=(3, 0))
    def _build_summary(self):
        summary = tk.Frame(self.container, bg=COLORS["background"])
        summary.grid(row=1, column=0, sticky="ew", pady=12)
        for column in range(4):
            summary.grid_columnconfigure(column, weight=1, uniform="summary")

        self.metric_values = {}
        for column, (key, title) in enumerate((
            ("waiting", "WAITING"),
            ("active", "IN SERVICE"),
            ("available", "AVAILABLE"),
            ("calls", "RECENT CALLS"),
        )):
            tile = tk.Frame(
                summary,
                bg=COLORS["surface"],
                padx=16,
                pady=10,
                highlightbackground=COLORS["line"],
                highlightthickness=1,
            )
            tile.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
            tk.Label(
                tile,
                text=title,
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                font=("Segoe UI", 9, "bold"),
            ).pack(anchor="w")
            value_label = tk.Label(
                tile,
                text="0",
                bg=COLORS["surface"],
                fg=COLORS["ink"],
                font=("Segoe UI", 23, "bold"),
            )
            value_label.pack(anchor="w", pady=(2, 0))
            self.metric_values[key] = value_label

    def _build_controls(self):
        controls = tk.Frame(
            self.body,
            bg=COLORS["surface"],
            padx=14,
            pady=14,
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        controls.grid(row=0, column=2, sticky="nsew", padx=8)
        controls.grid_columnconfigure(0, weight=1)

        tk.Label(
            controls,
            text="STAFF ACTIONS",
            bg=COLORS["surface"],
            fg=COLORS["ink"],
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            controls,
            text="Prototype mode - no sign-in required",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(3, 3))

        actor_controls = tk.Frame(controls, bg=COLORS["surface"])
        actor_controls.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.employee_label = tk.Label(
            actor_controls,
            text="Actions are recorded as Local staff",
            bg=COLORS["surface"],
            fg=COLORS["ink"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.employee_label.pack(fill="x", pady=5)

        tk.Label(
            controls,
            text="CALL HANDLING",
            bg=COLORS["surface"],
            fg=COLORS["green"],
            font=("Segoe UI", 9, "bold"),
        ).grid(row=3, column=0, sticky="w", pady=(2, 5))
        self.call_button = ttk.Button(
            controls,
            text="Call next client",
            command=self.call_next_client,
        )
        self.call_button.grid(row=4, column=0, sticky="ew", pady=3)
        self.arrival_button = ttk.Button(
            controls,
            text="Arrived",
            command=self.mark_selected_arrived,
            state="disabled",
        )
        self.arrival_button.grid(row=5, column=0, sticky="ew", pady=3)

        ttk.Separator(controls).grid(row=6, column=0, sticky="ew", pady=10)
        tk.Label(
            controls,
            text="QUEUE & CONSULTANTS",
            bg=COLORS["surface"],
            fg=COLORS["green"],
            font=("Segoe UI", 9, "bold"),
        ).grid(row=7, column=0, sticky="w", pady=(0, 5))
        ttk.Button(
            controls,
            text="View full queue",
            command=self.focus_queue,
        ).grid(row=8, column=0, sticky="ew", pady=3)
        ttk.Button(
            controls,
            text="Consultant status",
            command=self.focus_consultants,
        ).grid(row=9, column=0, sticky="ew", pady=3)

        advance_controls = tk.Frame(controls, bg=COLORS["surface"])
        advance_controls.grid(row=10, column=0, sticky="ew", pady=(10, 6))
        tk.Label(
            advance_controls,
            text="Minutes",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 4))
        self.minutes_input = ttk.Spinbox(
            advance_controls,
            from_=1,
            to=480,
        )
        self.minutes_input.set("5")
        self.minutes_input.pack(fill="x", pady=(0, 6))
        ttk.Button(
            advance_controls,
            text="Advance time",
            command=self.advance_simulated_time,
        ).pack(fill="x")

        cancel_controls = tk.Frame(controls, bg=COLORS["surface"])
        cancel_controls.grid(row=11, column=0, sticky="ew", pady=(6, 0))
        tk.Label(
            cancel_controls,
            text="Ticket",
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 4))
        self.cancel_ticket_input = ttk.Entry(cancel_controls)
        self.cancel_ticket_input.pack(fill="x", pady=(0, 6))
        ttk.Button(
            cancel_controls,
            text="Cancel ticket",
            command=self.cancel_selected_ticket,
        ).pack(fill="x")

    def _panel(self, parent, title, subtitle):
        panel = tk.Frame(
            parent,
            bg=COLORS["surface"],
            padx=14,
            pady=12,
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        tk.Label(
            panel,
            text=title,
            bg=COLORS["surface"],
            fg=COLORS["ink"],
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            panel,
            text=subtitle,
            bg=COLORS["surface"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(2, 9))
        return panel

    def _make_table(self, panel, columns, headings, widths):
        table_frame = tk.Frame(panel, bg=COLORS["surface"])
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Treeview",
        )
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading, anchor="w")
            tree.column(column, width=width, minwidth=60, anchor="w", stretch=True)
        tree.tag_configure("available", foreground=COLORS["green"])
        tree.tag_configure("busy", foreground=COLORS["amber"])
        tree.tag_configure("empty", foreground=COLORS["muted"])
        tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar.set)
        return tree

    def _build_tables(self):
        queue_panel = self._panel(self.body, "WAITING QUEUE", "Oldest ticket first")
        queue_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.queue_table = self._make_table(
            queue_panel,
            ("position", "ticket", "service"),
            ("POSITION", "TICKET", "SERVICE"),
            (78, 100, 250),
        )

        consultant_panel = self._panel(
            self.body,
            "CONSULTANT STATUS",
            "Current assignment and remaining time",
        )
        consultant_panel.grid(row=0, column=1, sticky="nsew", padx=8)
        self.consultant_table = self._make_table(
            consultant_panel,
            ("consultant", "status", "ticket", "remaining"),
            ("CONSULTANT", "STATUS", "TICKET", "LEFT"),
            (105, 105, 90, 65),
        )
        self.consultant_table.bind("<<TreeviewSelect>>", self._update_arrival_button)

        activity_panel = self._panel(
            self.body,
            "RECENT STAFF ACTIVITY",
            "Actions, acting consultant, and impact",
        )
        activity_panel.grid(row=0, column=3, sticky="nsew", padx=(8, 0))
        self.activity_table = self._make_table(
            activity_panel,
            ("action", "ticket", "actor", "consultants", "details"),
            ("ACTION", "TICKET", "EMPLOYEE", "CONSULTANTS", "DETAILS"),
            (145, 80, 145, 170, 260),
        )

    @staticmethod
    def _set_rows(tree, rows):
        desired_ids = {row[0] for row in rows}
        for item_id in tree.get_children():
            if item_id not in desired_ids:
                tree.delete(item_id)

        for position, (item_id, values, tags) in enumerate(rows):
            if tree.exists(item_id):
                tree.item(item_id, values=values, tags=tags)
            else:
                tree.insert("", "end", iid=item_id, values=values, tags=tags)
            tree.move(item_id, "", position)

    def _update_action_buttons(self, event=None):
        self.call_button.configure(
            state="normal" if getattr(self, "can_call_next", False) else "disabled"
        )

        selection = self.consultant_table.selection()
        if not selection:
            self.arrival_button.configure(state="disabled")
            return

        values = self.consultant_table.item(selection[0], "values")
        selected_consultant_id = _as_int(str(values[0]).rsplit(" ", 1)[-1])
        can_confirm = (
            len(values) >= 3
            and values[1] == "CALLING"
            and _as_int(values[2]) > 0
        )
        self.arrival_button.configure(state="normal" if can_confirm else "disabled")

    def _update_arrival_button(self, event=None):
        self._update_action_buttons()

    def mark_selected_arrived(self):
        selection = self.consultant_table.selection()
        if not selection:
            return

        values = self.consultant_table.item(selection[0], "values")
        ticket_number = _as_int(values[2]) if len(values) >= 3 else 0
        selected_consultant_id = (
            _as_int(str(values[0]).rsplit(" ", 1)[-1])
            if len(values) >= 3
            else 0
        )
        if ticket_number and mark_client_arrived(
            ticket_number,
            selected_consultant_id or None,
        ):
            self.updated_label.configure(text=f"Ticket {ticket_number:03} marked in service")
        else:
            self.updated_label.configure(text="Call changed; select the ticket currently on TV")

    def call_next_client(self):
        ticket, result = serve_next_client()
        if ticket:
            message = (
                f"Ticket {_ticket_number(ticket.get('ticket_number'))} called to "
                f"Consultant {result.get('id')}"
            )
        else:
            message = result
        self._finish_action(message)

    def focus_queue(self):
        self.queue_table.focus_set()
        queue_rows = self.queue_table.get_children()
        if queue_rows and queue_rows[0] != "queue-empty":
            self.queue_table.selection_set(queue_rows[0])
            self.queue_table.see(queue_rows[0])
        record_staff_action("Viewed waiting queue")
        self.updated_label.configure(text="Waiting queue selected")

    def focus_consultants(self):
        self.consultant_table.focus_set()
        record_staff_action("Viewed consultant status")
        self.updated_label.configure(text="Consultant status selected")

    def advance_simulated_time(self):
        try:
            minutes = int(self.minutes_input.get())
        except ValueError:
            self.updated_label.configure(text="Enter a valid number of minutes")
            return
        if minutes <= 0:
            self.updated_label.configure(text="Minutes must be greater than zero")
            return

        advance_time(minutes)
        self._finish_action(f"Advanced simulated time by {minutes} minute(s)")

    def cancel_selected_ticket(self):
        ticket_number = _as_int(self.cancel_ticket_input.get())
        if ticket_number <= 0:
            self.updated_label.configure(text="Enter a valid ticket number to cancel")
            return

        if cancel_ticket(ticket_number):
            message = f"Ticket {_ticket_number(ticket_number)} cancelled"
        else:
            message = f"Ticket {_ticket_number(ticket_number)} is not waiting"
        self._finish_action(message)

    def _finish_action(self, message):
        self.refresh_state(schedule=False)
        self.updated_label.configure(text=message)

    def refresh_state(self, schedule=True):
        try:
            state = read_monitor_state()
        except (sqlite3.Error, OSError, ValueError):
            self.connection_label.configure(
                text="DATA UNAVAILABLE",
                bg="#F8E2DF",
                fg=COLORS["red"],
            )
            self.updated_label.configure(text="Retrying local database")
            self.root.after(1000, self.refresh_state)
            return

        waiting_queue = sorted(
            state.get("waiting_queue", []),
            key=lambda ticket: _as_int(ticket.get("ticket_number")),
        )
        consultants = state.get("consultants", [])
        recent_calls = state.get("recent_calls", [])
        activity_log = state.get("activity_log", [])
        public_call = state.get("public_call")
        active_consultants = [
            consultant for consultant in consultants
            if consultant.get("ticket") or _as_int(consultant.get("busy_for")) > 0
        ]
        available_count = len(consultants) - len(active_consultants)

        self.metric_values["waiting"].configure(text=str(len(waiting_queue)))
        self.metric_values["active"].configure(text=str(len(active_consultants)))
        self.metric_values["available"].configure(text=str(available_count))
        self.metric_values["calls"].configure(text=str(len(recent_calls)))
        self.can_call_next = bool(waiting_queue) and any(
            _as_int(consultant.get("busy_for")) == 0
            and not consultant.get("ticket")
            and _as_int(consultant.get("id")) == self.consultant_id
            for consultant in consultants
        )
        self._update_action_buttons()

        queue_rows = [
            (
                f"queue-{_as_int(ticket.get('ticket_number'))}",
                (f"{position:02}", _ticket_number(ticket.get("ticket_number")),
                 ticket.get("service", "Unknown service")),
                (),
            )
            for position, ticket in enumerate(waiting_queue, start=1)
        ]
        if not queue_rows:
            queue_rows = [("queue-empty", ("--", "--", "No clients waiting"), ("empty",))]
        self._set_rows(self.queue_table, queue_rows)

        consultant_rows = []
        for consultant in consultants:
            ticket = consultant.get("ticket")
            remaining = max(0, _as_int(consultant.get("busy_for")))
            is_active = bool(ticket) or remaining > 0
            ticket_status = ticket.get("status") if isinstance(ticket, dict) else None
            is_public_call = (
                isinstance(ticket, dict)
                and isinstance(public_call, dict)
                and _as_int(public_call.get("ticket_number"))
                == _as_int(ticket.get("ticket_number"))
                and _as_int(public_call.get("consultant_id"))
                == _as_int(consultant.get("id"))
            )
            status = (
                "CALLING" if ticket_status == "Called" and is_public_call
                else "ON HOLD" if ticket_status == "Called"
                else "IN SERVICE" if is_active
                else "AVAILABLE"
            )
            ticket_text = (
                f"{_ticket_number(ticket.get('ticket_number'))}"
                if isinstance(ticket, dict)
                else "--"
            )
            consultant_rows.append((
                f"consultant-{consultant.get('id')}",
                (
                    f"Consultant {consultant.get('id')}",
                    status,
                    ticket_text,
                    f"{remaining} min" if is_active else "--",
                ),
                ("busy" if is_active else "available",),
            ))
        self._set_rows(self.consultant_table, consultant_rows)
        self._update_action_buttons()

        activity_rows = []
        for position, activity in enumerate(activity_log):
            affected_ids = activity.get("consultant_ids", [])
            consultants_text = ", ".join(
                f"Consultant {_as_int(consultant_id)}"
                for consultant_id in affected_ids
            )
            if not consultants_text and activity.get("action") == "Cancel ticket":
                consultants_text = "Unassigned"
            elif not consultants_text:
                consultants_text = "--"

            ticket_numbers = activity.get("ticket_numbers", [])
            if not ticket_numbers and activity.get("ticket_number") is not None:
                ticket_numbers = [activity["ticket_number"]]
            tickets_text = ", ".join(
                _ticket_number(ticket_number) for ticket_number in ticket_numbers
            ) or "--"
            activity_rows.append((
                f"activity-{position}",
                (
                    activity.get("action", "Action"),
                    tickets_text,
                    activity.get("actor_label") or "Local staff",
                    consultants_text,
                    activity.get("details", ""),
                ),
                (),
            ))
        if not activity_rows:
            activity_rows = [
                ("activity-empty", ("--", "--", "--", "--", "No staff actions recorded"), ("empty",))
            ]
        self._set_rows(self.activity_table, activity_rows)

        self.connection_label.configure(
            text="LIVE",
            bg="#D5E9DE",
            fg=COLORS["green"],
        )
        if schedule:
            self.updated_label.configure(
                text=f"Updated {datetime.now().strftime('%H:%M:%S')}"
            )
            self.root.after(1000, self.refresh_state)


if __name__ == "__main__":
    window = tk.Tk()
    app = StaffQueueMonitor(window)
    window.mainloop()