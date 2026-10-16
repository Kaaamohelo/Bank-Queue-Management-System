import json
import math
from pathlib import Path
from tempfile import NamedTemporaryFile

# Core queue logic shared across scripts
monitor_state_path = Path(__file__).with_name("queue_state.json")

service_times = {
    "Open an account": 10,
    "Credit enquiry": 15,
    "Funeral/Life Cover": 10,
    "Business account": 8,
    "General enquiries": 8,
}

services = {
    "1": "Open an account",
    "2": "Credit enquiry",
    "3": "Funeral/Life Cover",
    "4": "Business account",
    "5": "General enquiries",
}

# Runtime state
ticket_number = 1
waiting_queue = []
recent_calls = []
consultants = []


def default_consultants(count=3):
    return [{"id": i + 1, "busy_for": 0, "ticket": None} for i in range(count)]


def atomic_write_json(path: Path, obj):
    tmp = None
    try:
        tmp = NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=path.parent)
        json.dump(obj, tmp, indent=2)
        tmp.flush()
        tmp.close()
        Path(tmp.name).replace(path)
    except Exception:
        if tmp is not None:
            try:
                Path(tmp.name).unlink()
            except Exception:
                pass
        raise


def load_state():
    """Load state from queue_state.json — recovers gracefully on error."""
    global ticket_number, waiting_queue, consultants, recent_calls
    if not monitor_state_path.exists():
        consultants = default_consultants(3)
        waiting_queue = []
        recent_calls = []
        ticket_number = 1
        return

    try:
        with monitor_state_path.open(encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, json.JSONDecodeError):
        # Corrupt file: reset state but keep a backup if possible
        try:
            backup = monitor_state_path.with_suffix(".bak.json")
            monitor_state_path.replace(backup)
        except Exception:
            pass
        consultants = default_consultants(3)
        waiting_queue = []
        recent_calls = []
        ticket_number = 1
        return

    waiting_queue = state.get("waiting_queue", []) or []
    consultants = state.get("consultants", []) or default_consultants(3)
    recent_calls = state.get("recent_calls", []) or []

    for idx, c in enumerate(consultants):
        c.setdefault("busy_for", 0)
        c.setdefault("ticket", None)
        c.setdefault("id", idx + 1)

    # Recover ticket number to avoid duplicates
    max_ticket = 0
    for t in waiting_queue:
        try:
            max_ticket = max(max_ticket, int(t.get("ticket_number", 0)))
        except Exception:
            pass
    for call in recent_calls:
        try:
            max_ticket = max(max_ticket, int(call.get("ticket_number", 0)))
        except Exception:
            pass
    for c in consultants:
        tk = c.get("ticket")
        if isinstance(tk, dict):
            try:
                max_ticket = max(max_ticket, int(tk.get("ticket_number", 0)))
            except Exception:
                pass

    ticket_number = max_ticket + 1


def write_monitor_state():
    state = {
        "waiting_queue": waiting_queue,
        "consultants": consultants,
        "recent_calls": recent_calls[:8],
    }
    try:
        atomic_write_json(monitor_state_path, state)
    except Exception:
        # best-effort: ignore write failures (monitor may be offline)
        pass


def estimate_wait_for_new_client():
    num_consultants = max(1, len(consultants))
    total_busy = sum(max(0, int(c.get("busy_for", 0))) for c in consultants)
    queued_work = sum(service_times.get(client.get("service"), 0) for client in waiting_queue)
    total_work = total_busy + queued_work
    return math.ceil(total_work / num_consultants)


def find_free_consultant():
    for c in consultants:
        if int(c.get("busy_for", 0)) == 0:
            return c
    return None


def serve_next_client():
    if not waiting_queue:
        return None, "No clients in the queue."

    free = find_free_consultant()
    if not free:
        return None, "No available consultants right now. Please wait or advance time."

    try:
        oldest_ticket = min(waiting_queue, key=lambda t: int(t.get("ticket_number", 0)))
    except Exception:
        oldest_ticket = waiting_queue[0]

    waiting_queue.remove(oldest_ticket)
    service_time = service_times.get(oldest_ticket.get("service"), 0)
    free["busy_for"] = service_time
    free["ticket"] = oldest_ticket
    return oldest_ticket, free


def advance_time(minutes: int):
    if minutes <= 0:
        return
    for c in consultants:
        remaining = max(0, int(c.get("busy_for", 0)) - minutes)
        c["busy_for"] = remaining
        if remaining == 0:
            c["ticket"] = None


def cancel_ticket(ticket_no: int) -> bool:
    for t in list(waiting_queue):
        try:
            if int(t.get("ticket_number", -1)) == ticket_no:
                waiting_queue.remove(t)
                return True
        except Exception:
            continue
    return False


def add_ticket(service_name: str):
    """Add a new ticket for service_name. Returns (ticket, estimated_wait)."""
    global ticket_number
    new_ticket = {"ticket_number": ticket_number, "service": service_name}
    waiting_queue.append(new_ticket)
    estimated = estimate_wait_for_new_client()
    ticket_number += 1
    write_monitor_state()
    return new_ticket, estimated


# Initialize state on import
load_state()
# Ensure reasonable defaults
if not consultants:
    consultants = default_consultants(3)

# Ensure a monitor state exists
write_monitor_state()
