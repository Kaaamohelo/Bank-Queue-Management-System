# Bank Queue Management System

A Python-based queue management simulation for a bank branch. This repository contains a unified and refactored implementation that centralizes queue logic into a shared core so multiple scripts (final app, monitor, and prototypes) operate on the same state.

This is an educational, single-PC simulation, not software for real banking operations.

## What changed

This repository was refactored so all programs share a single source of truth:

- Added `queue_core.py` — shared core that implements:
  - persistent, safe state load/save to `queue_state.json` (atomic writes)
  - ticket generation and recovery (prevents duplicates)
  - queue management and capacity for eight consultants
  - migration of older saved states to eight consultants while preserving assignments
  - helper APIs: `add_ticket`, `serve_next_client`, `estimate_wait_for_new_client`, `cancel_ticket`, `advance_time`
- `Final Product_05.py` now uses the shared core (robust CLI, graceful shutdown).
- `Screen Monitor.py` reads the same `queue_state.json` and displays the active ticket, consultant, and patience message.
- Prototype scripts were adapted to import `queue_core.py` so they behave as small demos while sharing ticket numbering and queue state:
  - `Same Ticket Prototype_01.py`
  - `Increase Tickets Same Service_02.py`
  - `Unlimited Sequence Prototype_03.py`
  - `Estimate waiting times_04.py`

All code now uses the same JSON snapshot format so the monitor and any script see the same queue and consultant state.

## Monitor Preview

The monitor displays the ticket currently being served, the consultant number, and a patience message.

![Bank queue monitor preview showing the active ticket and consultant](image-1792139293746.png)

When multiple consultants are serving clients, the current monitor displays the first active consultant only.

## Files of interest

- queue_core.py — shared core implemented for reliability and alignment
- Final Product_05.py — main CLI program (uses the core)
- Screen Monitor.py — Tkinter-based display (reads `queue_state.json`)
- queue_state.json — runtime snapshot (created/updated at runtime)
- image-1792139293746.png — monitor screenshot
- Same Ticket Prototype_01.py, Increase Tickets Same Service_02.py, Unlimited Sequence Prototype_03.py, Estimate waiting times_04.py — small demos built on the core

## Requirements

- Python 3.8+ recommended
- `tkinter` (only required to run `Screen Monitor.py`), usually included with desktop Python
- No third-party Python packages are required

## Run on Windows

Open two terminals in the repository directory. Start the queue controls in one:

```powershell
py ".\Final Product_05.py"
```

Start the public monitor in the other:

```powershell
py ".\Screen Monitor.py"
```

In the controls menu, choose a service from `1`-`5` to add a ticket, then choose `6` to call the next client. Use `7` to view the queue, `8` to view consultant status, `9` to advance simulated time, and `10` to cancel a waiting ticket. Choose `0` to exit.

On systems without the Windows `py` launcher, replace `py` with `python` or `python3`.

## Prototype Demos

These scripts share the same local queue state:

```powershell
py ".\Same Ticket Prototype_01.py"
py ".\Increase Tickets Same Service_02.py"
py ".\Unlimited Sequence Prototype_03.py"
py ".\Estimate waiting times_04.py"
```

## Notes & recommendations

- `queue_state.json` stores local runtime data. The core uses atomic writes, recovers the ticket counter, and adds missing consultants when loading older saved states.
- The controller and monitor share a local JSON file; this version does not share queue state across computers and has no authentication or production security controls.
- Use simulated data only. Do not enter real customer information.

## Author

Kaaamohelo
