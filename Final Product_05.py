import json
import math
import signal
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# Bank Queue Management System (Final Product)
# Improved: persistent state load/save, atomic writes, better wait estimates,
# and safer JSON handling. Designed to align with monitor and prototypes.

monitor_state_path = Path(__file__).with_name("queue_state.json")

# Default configuration
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

# Runtime state (will attempt to load from queue_state.json)
ticket_number = 1
waiting_queue = []
recent_calls = []
consultants = []


def default_consultants(count=3):
    return [{"id": i + 1, "busy_for": 0, "ticket": None} for i in range(count)]


def atomic_write_json(path: Path, obj):
    # Write to a temp file then rename (atomic on most platforms)
    tmp = None
    try:
        tmp = NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=path.parent)
        json.dump(obj, tmp, indent=2)
        tmp.flush()
        tmp.close()
        Path(tmp.name).replace(path)
    except Exception:
        # Attempt best-effort cleanup
        if tmp is not None:
            try:
                Path(tmp.name).unlink()
            except Exception:
                pass
        raise


def load_state():
    global ticket_number, waiting_queue, consultants, recent_calls
    if not monitor_state_path.exists():
        # initialize defaults
        consultants = default_consultants(3)
        return

    try:
        with monitor_state_path.open(encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, json.JSONDecodeError):
        # corrupted or unreadable state — start fresh but keep a backup
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

    # Load arrays safely with defaults
    waiting_queue = state.get("waiting_queue", []) or []
    consultants = state.get("consultants", []) or default_consultants(3)
    recent_calls = state.get("recent_calls", []) or []

    # Ensure numeric fields exist and are sane
    for c in consultants:
        c.setdefault("busy_for", 0)
        c.setdefault("ticket", None)
        c.setdefault("id", consultants.index(c) + 1)

    # Recover ticket_number to avoid duplicates
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
    except Exception as e:
        print("Warning: failed to write monitor state:", e)


def estimate_wait_for_new_client():
    """Estimate minutes until a newly arriving client starts service.

    Strategy:
    - Sum remaining busy time for all consultants.
    - Sum required service time for all queued tickets.
    - Add an estimated service time for the new client (not included here because
      caller may want the time until start, not completion).
    - Distribute total work across number of consultants (must be >=1).
    - Round up.
    """
    # Compute dynamic number of consultants
    num_consultants = max(1, len(consultants))
    total_busy = sum(max(0, int(c.get("busy_for", 0))) for c in consultants)
    queued_work = 0
    for client in waiting_queue:
        queued_work += service_times.get(client.get("service"), 0)
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

    # Serve the oldest ticket (lowest ticket number)
    try:
        oldest_ticket = min(waiting_queue, key=lambda t: int(t.get("ticket_number", 0)))
    except Exception:
        oldest_ticket = waiting_queue[0]

    waiting_queue.remove(oldest_ticket)
    service_time = service_times.get(oldest_ticket.get("service"), 0)
    free["busy_for"] = service_time
    free["ticket"] = oldest_ticket
    return oldest_ticket, free


def print_menu():
    print("\n===== BANK QUEUE MANAGEMENT =====")
    print("Select your service")
    for key, value in services.items():
        print(f"{key}. {value}")
    print("6. Call next client")
    print("7. View full queue")
    print("8. View consultants status")
    print("9. Advance time (simulate minutes)")
    print("10. Cancel a ticket")
    print("0. Exit")
    print("=================================")


def print_full_queue():
    if not waiting_queue:
        print("\nQueue is empty.")
        return

    sorted_queue = sorted(waiting_queue, key=lambda ticket: int(ticket.get("ticket_number", 0)))
    print("\n===== FULL QUEUE =====")
    print(f"{'Pos':>3}  {'Ticket':>6}  {'Service'}")
    print("-------------------------------")
    for position, ticket in enumerate(sorted_queue, start=1):
        print(f"{position:>3}   {int(ticket['ticket_number']):03}     {ticket['service']}")
    print("-------------------------------")
    print(f"Total waiting: {len(waiting_queue)}")


def print_consultants():
    print("\n===== CONSULTANTS =====")
    for c in consultants:
        status = "Idle" if int(c.get("busy_for", 0)) == 0 else f"Busy ({int(c.get('busy_for',0))} min left)"
        ticket = c.get("ticket")
        ticket_info = "" if not ticket else f" - Ticket {int(ticket.get('ticket_number')):03} ({ticket.get('service')})"
        print(f"Consultant {c.get('id')}: {status}{ticket_info}")
    print("=======================")


def advance_time(minutes):
    if minutes <= 0:
        return
    for c in consultants:
        remaining = max(0, int(c.get("busy_for", 0)) - minutes)
        c["busy_for"] = remaining
        if remaining == 0:
            c["ticket"] = None


def cancel_ticket(ticket_no):
    for t in list(waiting_queue):
        try:
            if int(t.get("ticket_number", -1)) == ticket_no:
                waiting_queue.remove(t)
                return True
        except Exception:
            continue
    return False


def graceful_exit(signum=None, frame=None):
    write_monitor_state()
    print("\nState saved. Exiting.")
    sys.exit(0)


# Wire signals for clean shutdown
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

# Load initial state
load_state()
# Ensure we always have a reasonable number of consultants
if not consultants:
    consultants = default_consultants(3)

# Initial write to create monitor state for the monitor app
write_monitor_state()


if __name__ == "__main__":
    while True:
        print_menu()
        try:
            choice = input("Choose your service: ").strip()
        except (EOFError, KeyboardInterrupt):
            graceful_exit()

        # Exit the queue system
        if choice == "0":
            graceful_exit()

        # Consultant calls the next client in the queue (oldest ticket)
        if choice == "6":
            ticket, info = serve_next_client()
            if ticket:
                consultant = info
                print("\n===== CALLING NEXT CLIENT =====")
                print(f"Ticket number: {int(ticket['ticket_number']):03}")
                print(f"Service: {ticket['service']}")
                print(f"Assigned to consultant: {consultant['id']}")
                print("Clients waiting in the queue:", len(waiting_queue))
                recent_calls.insert(0, {
                    "ticket_number": int(ticket["ticket_number"]),
                    "service": ticket["service"],
                    "consultant_id": consultant["id"],
                })
                # trim recent calls
                recent_calls = recent_calls[:50]
                write_monitor_state()
            else:
                print(info)
            continue

        # View the full queue
        if choice == "7":
            print_full_queue()
            continue

        # View consultants
        if choice == "8":
            print_consultants()
            continue

        # Advance time to simulate consultants finishing work
        if choice == "9":
            try:
                minutes = int(input("Advance time by how many minutes? ").strip())
            except ValueError:
                print("Please enter a valid number of minutes.")
                continue
            advance_time(minutes)
            write_monitor_state()
            print(f"Advanced time by {minutes} minute(s).")
            print_consultants()
            continue

        # Cancel a ticket by number
        if choice == "10":
            try:
                tno = int(input("Enter ticket number to cancel: ").strip())
            except ValueError:
                print("Please enter a valid ticket number.")
                continue
            if cancel_ticket(tno):
                write_monitor_state()
                print(f"Ticket {tno:03} cancelled.")
            else:
                print(f"Ticket {tno:03} not found in waiting queue.")
            continue

        # Client selects a service and generates a ticket number
        if choice in services:
            service = services[choice]

            # Number of clients already waiting in the shared queue
            people_ahead = len(waiting_queue)

            # Estimate waiting time (minutes until start)
            estimated_waiting_time = estimate_wait_for_new_client()

            # Add the new client to the shared queue.
            new_ticket = {"ticket_number": ticket_number, "service": service}
            waiting_queue.append(new_ticket)

            write_monitor_state()

            print("\n=======================================")
            print("            BANK QUEUE TICKET")
            print("=======================================")
            print(f"Ticket number: {ticket_number:03}")
            print(f"Service: {service}")
            print(f"People ahead: {people_ahead}")
            print(f"Estimated waiting time until start: {estimated_waiting_time} minutes")
            print("---------------------------------------")
            print("Please wait until your number is called.")
            print("Thank you for your patience.")
            print("=======================================")
            print("Total clients waiting in the queue:", len(waiting_queue))
            print("=================================")

            ticket_number += 1
            continue

        # Invalid input
        print("Invalid selection. Please choose a valid option.")
