"""
Simple prototype issuing tickets in sequence (any service chosen interactively)
Now uses the shared core to ensure consistent ticket numbering and queue behaviour.
"""

from queue_core import services, add_ticket

print("Unlimited sequence prototype — choose a service to begin issuing tickets.")
for k, v in services.items():
    print(f"{k}. {v}")
choice = input("Choose a service (1-5): ").strip()
if choice not in services:
    print("Invalid choice.")
else:
    try:
        while True:
            ticket, est = add_ticket(services[choice])
            print(f"Your ticket number for {services[choice]} is: {int(ticket['ticket_number']):03} (est start: {est} min)")
            cont = input("Press Enter to issue next, or type q to quit: ").strip().lower()
            if cont == "q":
                break
    except KeyboardInterrupt:
        print("Stopped.")
