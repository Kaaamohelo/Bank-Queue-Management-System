"""
Estimate waiting times prototype — now uses shared core to compute estimates
"""

from queue_core import services, add_ticket, waiting_queue

print("Estimate waiting times demo")
for k, v in services.items():
    print(f"{k}. {v}")
choice = input("Choose a service (1-5): ").strip()
if choice not in services:
    print("Invalid choice.")
else:
    people_ahead = len(waiting_queue)
    ticket, est = add_ticket(services[choice])
    print(f"Ticket number: {int(ticket['ticket_number']):03}")
    print(f"Service: {ticket['service']}")
    print(f"People ahead: {people_ahead}")
    print(f"Estimated waiting time until start: {est} minutes")
