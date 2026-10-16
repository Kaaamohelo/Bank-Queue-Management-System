# Bank Queue Management System

A Python-based queue management simulation for a bank branch. This repository contains a unified and refactored implementation that centralizes queue logic into a shared core so multiple scripts (final app, monitor, and prototypes) operate on the same state.

## What changed

This repository was refactored so all programs share a single source of truth:

- Added `queue_core.py` — shared core that implements:
  - persistent, safe state load/save to `queue_state.json` (atomic writes)
  - ticket generation and recovery (prevents duplicates)
  - queue and consultant state management
  - helper APIs: `add_ticket`, `serve_next_client`, `estimate_wait_for_new_client`, `cancel_ticket`, `advance_time`
- `Final Product_05.py` now uses the shared core (robust CLI, graceful shutdown).
- `Screen Monitor.py` reads the same `queue_state.json` produced by the core and displays the live state.
- Prototype scripts were adapted to import `queue_core.py` so they behave as small demos while sharing ticket numbering and queue state:
  - `Same Ticket Prototype_01.py`
  - `Increase Tickets Same Service_02.py`
  - `Unlimited Sequence Prototype_03.py`
  - `Estimate waiting times_04.py`

All code now uses the same JSON snapshot format so the monitor and any script see the same queue and consultant state.

## Files of interest

- queue_core.py — shared core implemented for reliability and alignment
- Final Product_05.py — main CLI program (uses the core)
- Screen Monitor.py — Tkinter-based display (reads `queue_state.json`)
- queue_state.json — runtime snapshot (created/updated at runtime)
- Same Ticket Prototype_01.py, Increase Tickets Same Service_02.py, Unlimited Sequence Prototype_03.py, Estimate waiting times_04.py — small demos built on the core

## Requirements

- Python 3.8+ recommended
- `tkinter` (only required to run `Screen Monitor.py`) — usually included with system Python on desktops

## Run the main queue app

From the repository directory:

python "Final Product_05.py"

If your system uses Python 3 explicitly:

python3 "Final Product_05.py"

Run the monitor in a second terminal (optional):

python "Screen Monitor.py"

Run a prototype demo (they share queue state):

python "Same Ticket Prototype_01.py"
python "Increase Tickets Same Service_02.py"
python "Unlimited Sequence Prototype_03.py"
python "Estimate waiting times_04.py"

## Notes & recommendations

- `queue_state.json` stores the runtime snapshot. The core uses atomic writes and performs a basic recovery if the file becomes corrupted.
- The core recovers the ticket counter to avoid duplicate ticket numbers after restarts.
- If you want a smaller surface for production, consider removing the prototype scripts or moving them into a `demos/` directory.
- I can add a `requirements.txt` or tests if you want—ask and I will add them.

## Author

Kaaamohelo
