import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import time

STATE_DB_PATH = Path(__file__).with_name("queue_state.sqlite3")
LEGACY_STATE_PATH = Path(__file__).with_name("queue_state.json")

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

DEFAULT_CONSULTANT_COUNT = 8
PUBLIC_CALL_INTERVAL_SECONDS = 5
PUBLIC_CALL_ATTEMPTS = 3
PUBLIC_CALL_GRACE_SECONDS = 10

ticket_number = 1
waiting_queue = []
recent_calls = []
consultants = []


def default_consultants(count=DEFAULT_CONSULTANT_COUNT):
    return [{"id": index + 1, "busy_for": 0, "ticket": None} for index in range(count)]


def _connect():
    connection = sqlite3.connect(STATE_DB_PATH, timeout=10)
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS queue_state "
        "(id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL)"
    )
    return connection


@contextmanager
def _database():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _default_state():
    return {
        "ticket_number": 1,
        "waiting_queue": [],
        "consultants": default_consultants(),
        "recent_calls": [],
        "activity_log": [],
    }


def _normalize_state(state):
    state = state if isinstance(state, dict) else {}
    state["waiting_queue"] = state.get("waiting_queue", []) or []
    state["consultants"] = state.get("consultants", []) or default_consultants()
    state["recent_calls"] = state.get("recent_calls", []) or []
    state["activity_log"] = state.get("activity_log", []) or []
    state["public_call"] = state.get("public_call")
    for activity in state["activity_log"]:
        old_employee_number = activity.pop("actor_employee_number", None)
        old_consultant_id = activity.pop("actor_consultant_id", None)
        if old_employee_number:
            activity["actor_label"] = "Local staff"
        elif old_consultant_id is not None:
            activity.setdefault("actor_label", f"Legacy consultant {old_consultant_id}")

    for index, consultant in enumerate(state["consultants"]):
        consultant.setdefault("busy_for", 0)
        consultant.setdefault("ticket", None)
        consultant.setdefault("id", index + 1)
        if isinstance(consultant["ticket"], dict):
            consultant["ticket"].setdefault("status", "In service")

    next_consultant_id = 1
    while len(state["consultants"]) < DEFAULT_CONSULTANT_COUNT:
        existing_ids = {consultant.get("id") for consultant in state["consultants"]}
        while next_consultant_id in existing_ids:
            next_consultant_id += 1
        state["consultants"].append({
            "id": next_consultant_id,
            "busy_for": 0,
            "ticket": None,
        })
        next_consultant_id += 1

    max_ticket = 0
    for ticket in state["waiting_queue"] + state["recent_calls"]:
        try:
            max_ticket = max(max_ticket, int(ticket.get("ticket_number", 0)))
        except (AttributeError, TypeError, ValueError):
            continue
    for consultant in state["consultants"]:
        active_ticket = consultant.get("ticket")
        if isinstance(active_ticket, dict):
            try:
                max_ticket = max(max_ticket, int(active_ticket.get("ticket_number", 0)))
            except (TypeError, ValueError):
                pass

    try:
        stored_next_ticket = int(state.get("ticket_number", 1))
    except (TypeError, ValueError):
        stored_next_ticket = 1
    state["ticket_number"] = max(stored_next_ticket, max_ticket + 1)
    return state


def _read_legacy_state():
    if not LEGACY_STATE_PATH.exists():
        return _default_state()
    try:
        with LEGACY_STATE_PATH.open(encoding="utf-8") as state_file:
            return _normalize_state(json.load(state_file))
    except (OSError, json.JSONDecodeError):
        backup_path = LEGACY_STATE_PATH.with_suffix(".bak.json")
        try:
            LEGACY_STATE_PATH.replace(backup_path)
        except OSError:
            pass
        return _default_state()


def _state_from_connection(connection):
    row = connection.execute(
        "SELECT payload FROM queue_state WHERE id = 1"
    ).fetchone()
    if row is None:
        state = _read_legacy_state()
        connection.execute(
            "INSERT INTO queue_state (id, payload) VALUES (1, ?)",
            (json.dumps(state),),
        )
        return state
    return _normalize_state(json.loads(row[0]))


def _apply_state(state):
    global ticket_number
    ticket_number = state["ticket_number"]
    waiting_queue[:] = state["waiting_queue"]
    consultants[:] = state["consultants"]
    recent_calls[:] = state["recent_calls"]


def load_state():
    """Refresh in-memory state from SQLite, importing the legacy JSON once."""
    with _database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        state = _state_from_connection(connection)
        connection.execute(
            "UPDATE queue_state SET payload = ? WHERE id = 1",
            (json.dumps(state),),
        )
    _apply_state(state)


def read_monitor_state():
    """Return the public monitor's active-consultant state from SQLite."""
    with _database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        state = _state_from_connection(connection)
    return {
        "waiting_queue": state["waiting_queue"],
        "consultants": state["consultants"],
        "recent_calls": state["recent_calls"][:8],
        "public_call": state["public_call"],
        "activity_log": state["activity_log"][:30],
    }


def _update_state(update):
    with _database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        state = _state_from_connection(connection)
        result = update(state)
        state = _normalize_state(state)
        connection.execute(
            "UPDATE queue_state SET payload = ? WHERE id = 1",
            (json.dumps(state),),
        )
    _apply_state(state)
    return result


def _estimate_wait(state):
    availability = [max(0, int(consultant.get("busy_for", 0)))
                    for consultant in state["consultants"]]
    if not availability:
        return 0

    queued_tickets = sorted(
        state["waiting_queue"],
        key=lambda ticket: int(ticket.get("ticket_number", 0)),
    )
    for ticket in queued_tickets:
        consultant_index = min(
            range(len(availability)),
            key=lambda index: (availability[index], index),
        )
        availability[consultant_index] += service_times.get(ticket.get("service"), 0)
    return min(availability)


def estimate_wait_for_new_client():
    """Estimate start delay by scheduling existing FIFO work across consultants."""
    with _database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        state = _state_from_connection(connection)
    _apply_state(state)
    return _estimate_wait(state)


def find_free_consultant():
    load_state()
    for consultant in consultants:
        if int(consultant.get("busy_for", 0)) == 0:
            return consultant
    return None


def _validated_consultant_id(state, consultant_id):
    if consultant_id is None:
        return None
    consultant_id = int(consultant_id)
    if not any(int(item.get("id", -1)) == consultant_id for item in state["consultants"]):
        raise ValueError(f"Unknown consultant ID: {consultant_id}")
    return consultant_id


def _record_activity(
    state,
    action,
    ticket_number=None,
    consultant_ids=None,
    ticket_numbers=None,
    details="",
    actor_label=None,
):
    activity = {
        "action": action,
        "actor_label": actor_label,
        "ticket_number": ticket_number,
        "consultant_ids": list(consultant_ids or []),
        "ticket_numbers": list(ticket_numbers or []),
        "details": details,
        "created_at": time.time(),
    }
    state["activity_log"].insert(0, activity)
    state["activity_log"] = state["activity_log"][:100]


def record_staff_action(action: str):
    """Record a staff dashboard action in prototype mode."""
    def update(state):
        _record_activity(state, action, actor_label="Local staff")

    _update_state(update)


def serve_next_client(consultant_id=None):
    def update(state):
        assigned_consultant_id = _validated_consultant_id(state, consultant_id)
        if not state["waiting_queue"]:
            _record_activity(
                state,
                "Call next client",
                actor_label="Local staff",
                details="No waiting tickets",
            )
            return None, "No clients in the queue."

        free_consultant = next((
            consultant for consultant in state["consultants"]
            if int(consultant.get("busy_for", 0)) == 0
            and not consultant.get("ticket")
            and (
                assigned_consultant_id is None
                or int(consultant.get("id", -1)) == assigned_consultant_id
            )
        ), None)
        if free_consultant is None:
            if assigned_consultant_id is not None:
                message = f"Consultant {assigned_consultant_id} is not available right now."
            else:
                message = "No available consultants right now. Please wait or advance time."
            _record_activity(
                state,
                "Call next client",
                actor_label="Local staff",
                consultant_ids=[assigned_consultant_id] if assigned_consultant_id else [],
                details=message,
            )
            return None, message

        ticket_index = min(
            range(len(state["waiting_queue"])),
            key=lambda index: int(state["waiting_queue"][index].get("ticket_number", 0)),
        )
        ticket = state["waiting_queue"].pop(ticket_index)
        ticket["status"] = "Called"
        free_consultant["busy_for"] = service_times.get(ticket.get("service"), 0)
        free_consultant["ticket"] = ticket
        state["recent_calls"].insert(0, {
            "ticket_number": int(ticket["ticket_number"]),
            "service": ticket["service"],
            "consultant_id": free_consultant["id"],
            "status": "Called",
        })
        state["recent_calls"] = state["recent_calls"][:50]
        _record_activity(
            state,
            "Call next client",
            actor_label="Local staff",
            ticket_number=int(ticket["ticket_number"]),
            consultant_ids=[int(free_consultant["id"])],
            ticket_numbers=[int(ticket["ticket_number"])],
            details="Ticket assigned and displayed for calling",
        )
        return ticket, free_consultant

    return _update_state(update)


def mark_client_arrived(
    ticket_number: int,
    consultant_id=None,
) -> bool:
    """Confirm the currently displayed ticket arrived and is being assisted."""
    def update(state):
        assigned_consultant_id = _validated_consultant_id(state, consultant_id)
        public_call = state.get("public_call")
        if (
            not public_call
            or int(public_call.get("ticket_number", -1)) != ticket_number
            or (
                assigned_consultant_id is not None
                and int(public_call.get("consultant_id", -1)) != assigned_consultant_id
            )
        ):
            _record_activity(
                state,
                "Arrived",
                actor_label="Local staff",
                ticket_number=ticket_number,
                details="No matching current public call",
            )
            return False

        consultant = next(
            (
                item for item in state["consultants"]
                if int(item.get("id", -1)) == int(public_call.get("consultant_id", -2))
                and isinstance(item.get("ticket"), dict)
                and int(item["ticket"].get("ticket_number", -1)) == ticket_number
            ),
            None,
        )
        if consultant is None:
            _record_activity(
                state,
                "Arrived",
                actor_label="Local staff",
                ticket_number=ticket_number,
                details="Current call has no active consultant assignment",
            )
            return False

        consultant["ticket"]["status"] = "In service"
        for call in state["recent_calls"]:
            if (
                int(call.get("ticket_number", -1)) == ticket_number
                and int(call.get("consultant_id", -1)) == int(consultant["id"])
            ):
                call["status"] = "In service"
                call["call_attempts"] = int(public_call.get("attempt", 1))
                call["arrived_at"] = time.time()
                break
        state["public_call"] = None
        _record_activity(
            state,
            "Arrived",
            actor_label="Local staff",
            ticket_number=ticket_number,
            consultant_ids=[int(consultant["id"])],
            ticket_numbers=[ticket_number],
            details="Client marked in service",
        )
        return True

    return _update_state(update)


def advance_time(minutes: int):
    if minutes <= 0:
        return

    def update(state):
        affected_consultants = [
            consultant for consultant in state["consultants"]
            if int(consultant.get("busy_for", 0)) > 0
        ]
        completed_tickets = []
        for consultant in state["consultants"]:
            remaining = max(0, int(consultant.get("busy_for", 0)) - minutes)
            consultant["busy_for"] = remaining
            if remaining == 0:
                completed_ticket = consultant.get("ticket")
                if isinstance(completed_ticket, dict):
                    completed_tickets.append(int(completed_ticket.get("ticket_number", 0)))
                    for call in state["recent_calls"]:
                        if (
                            int(call.get("ticket_number", -1))
                            == int(completed_ticket.get("ticket_number", -2))
                            and int(call.get("consultant_id", -1))
                            == int(consultant.get("id", -2))
                        ):
                            call["status"] = "Completed"
                            break
                    public_call = state.get("public_call")
                    if public_call and (
                        int(public_call.get("ticket_number", -1))
                        == int(completed_ticket.get("ticket_number", -2))
                        and int(public_call.get("consultant_id", -1))
                        == int(consultant.get("id", -2))
                    ):
                        state["public_call"] = None
                consultant["ticket"] = None

        affected_ids = [int(consultant["id"]) for consultant in affected_consultants]
        _record_activity(
            state,
            "Advance time",
            actor_label="Local staff",
            consultant_ids=affected_ids,
            ticket_numbers=[
                int(consultant["ticket"]["ticket_number"])
                for consultant in affected_consultants
                if isinstance(consultant.get("ticket"), dict)
            ] + completed_tickets,
            details=(
                f"Advanced simulated time by {minutes} minute(s)"
                + (
                    "; completed tickets "
                    + ", ".join(f"{ticket_number:03}" for ticket_number in completed_tickets)
                    if completed_tickets
                    else ""
                )
            ),
        )

    _update_state(update)


def cancel_ticket(ticket_no: int) -> bool:
    def update(state):
        for index, ticket in enumerate(state["waiting_queue"]):
            try:
                if int(ticket.get("ticket_number", -1)) == ticket_no:
                    state["waiting_queue"].pop(index)
                    _record_activity(
                        state,
                        "Cancel ticket",
                        actor_label="Local staff",
                        ticket_number=int(ticket_no),
                        details="No consultant assigned; waiting ticket removed",
                    )
                    return True
            except (AttributeError, TypeError, ValueError):
                continue
        _record_activity(
            state,
            "Cancel ticket",
            actor_label="Local staff",
            ticket_number=int(ticket_no),
            details="Ticket is not in the waiting queue",
        )
        return False

    return _update_state(update)


def add_ticket(service_name: str):
    """Add a ticket and return its estimated delay before service begins."""
    def update(state):
        estimated_wait = _estimate_wait(state)
        new_ticket = {
            "ticket_number": state["ticket_number"],
            "service": service_name,
        }
        state["waiting_queue"].append(new_ticket)
        state["ticket_number"] += 1
        _record_activity(
            state,
            "Add ticket",
            ticket_number=int(new_ticket["ticket_number"]),
            details=f"Ticket added for {service_name}",
            actor_label="Local staff",
        )
        return new_ticket, estimated_wait

    return _update_state(update)


def get_next_public_call(now=None):
    """Return the current public call, advancing or closing its call cycle."""
    current_time = time.time() if now is None else float(now)

    def update(state):
        active_consultants = sorted(
            (
                consultant for consultant in state["consultants"]
                if isinstance(consultant.get("ticket"), dict)
                and consultant["ticket"].get("status") != "In service"
            ),
            key=lambda consultant: (
                int(consultant["ticket"].get("ticket_number", 0)),
                int(consultant.get("id", 0)),
            ),
        )
        public_call = state.get("public_call")
        assigned_consultant = None
        if public_call:
            assigned_consultant = next(
                (
                    consultant for consultant in active_consultants
                    if int(consultant.get("id", 0)) == int(public_call.get("consultant_id", -1))
                    and int(consultant["ticket"].get("ticket_number", 0))
                    == int(public_call.get("ticket_number", -1))
                ),
                None,
            )
            if assigned_consultant is None:
                public_call = None

        if public_call:
            due_at = float(public_call.get("next_attempt_at", current_time))
            if current_time >= due_at:
                attempts = int(public_call.get("attempt", 1))
                if attempts < PUBLIC_CALL_ATTEMPTS:
                    public_call["attempt"] = attempts + 1
                    delay = (
                        PUBLIC_CALL_GRACE_SECONDS
                        if attempts + 1 == PUBLIC_CALL_ATTEMPTS
                        else PUBLIC_CALL_INTERVAL_SECONDS
                    )
                    public_call["next_attempt_at"] = current_time + delay
                    for call in state["recent_calls"]:
                        if (
                            int(call.get("ticket_number", -1))
                            == int(public_call["ticket_number"])
                            and int(call.get("consultant_id", -1))
                            == int(public_call["consultant_id"])
                        ):
                            call["status"] = f"Calling ({attempts + 1}/{PUBLIC_CALL_ATTEMPTS})"
                            break
                else:
                    assigned_consultant["busy_for"] = 0
                    assigned_consultant["ticket"] = None
                    for call in state["recent_calls"]:
                        if (
                            int(call.get("ticket_number", -1))
                            == int(public_call["ticket_number"])
                            and int(call.get("consultant_id", -1))
                            == int(public_call["consultant_id"])
                        ):
                            call["status"] = "No-show"
                            call["call_attempts"] = PUBLIC_CALL_ATTEMPTS
                            break
                    _record_activity(
                        state,
                        "No-show",
                        ticket_number=int(public_call["ticket_number"]),
                        consultant_ids=[int(public_call["consultant_id"])],
                        ticket_numbers=[int(public_call["ticket_number"])],
                        details="Three calls unanswered; consultant released",
                        actor_label="Call timer",
                    )
                    public_call = None

        active_consultants = [
            consultant for consultant in active_consultants
            if isinstance(consultant.get("ticket"), dict)
            and consultant["ticket"].get("status") != "In service"
        ]
        if public_call is None and active_consultants:
            next_consultant = active_consultants[0]
            ticket = next_consultant["ticket"]
            public_call = {
                "consultant_id": int(next_consultant["id"]),
                "ticket_number": int(ticket["ticket_number"]),
                "attempt": 1,
                "next_attempt_at": current_time + PUBLIC_CALL_INTERVAL_SECONDS,
            }
            for call in state["recent_calls"]:
                if (
                    int(call.get("ticket_number", -1)) == public_call["ticket_number"]
                    and int(call.get("consultant_id", -1)) == public_call["consultant_id"]
                ):
                    call["status"] = f"Calling (1/{PUBLIC_CALL_ATTEMPTS})"
                    break

        state["public_call"] = public_call
        if public_call is None:
            return None
        return {
            "ticket_number": public_call["ticket_number"],
            "consultant_id": public_call["consultant_id"],
            "attempt": public_call["attempt"],
        }

    return _update_state(update)


consultants = default_consultants()
