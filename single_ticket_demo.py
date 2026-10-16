"""
Legacy prototype converted to a short example that uses the shared queue_core.
This script demonstrates issuing a single ticket and printing the result.
"""

from queue_core import services, add_ticket

print("Simple prototype: issue one ticket using the shared core")
for k, v in services.items():
    print(f"{k}. {v}")
choice = input("Choose a service (1-5): ").strip()
if choice not in services:
    print("Invalid choice.")
else:
    ticket, estimated = add_ticket(services[choice])
    print(f"Issued ticket {int(ticket['ticket_number']):03} for {ticket['service']}")
    print(f"Estimated wait (minutes until start): {estimated}")
