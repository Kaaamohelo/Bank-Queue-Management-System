"""
Prototype: repeatedly issue tickets for Credit enquiry using shared core.
"""

from queue_core import add_ticket

print("Press Enter to issue the next Credit enquiry ticket. Ctrl+C to exit.")
try:
    while True:
        input()
        ticket, est = add_ticket("Credit enquiry")
        print(f"Issued ticket {int(ticket['ticket_number']):03} (est start: {est} min)")
except KeyboardInterrupt:
    print("Stopped.")
