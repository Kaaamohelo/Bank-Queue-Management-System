import math

# Bank Queue Management System (Final Product)

ticket_number = 1
waiting_queue = []

service_times = {
    "Open an account": 10,
    "Credit enquiry": 15,
    "Funeral/Life Cover": 10,
    "Business account": 8,
    "General enquiries": 8,
}

available_consultants = 3
# Track each consultant's remaining busy time (in minutes). 0 means free.
consultants = [{"id": i + 1, "busy_for": 0} for i in range(available_consultants)]

services = {
    "1": "Open an account",
    "2": "Credit enquiry",
    "3": "Funeral/Life Cover",
    "4": "Business account",
    "5": "General enquiries",
}


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


def estimate_wait_for_new_client():
    """Estimate how many minutes until a newly arriving client will start being served.
    Calculation includes remaining busy time for consultants plus total queued service time,
    divided evenly across consultants (ceil).
    """
    total_busy = sum(c["busy_for"] for c in consultants)
    queued_work = sum(service_times[client["service"]] for client in waiting_queue)
    total_work = total_busy + queued_work
    if available_consultants > 0:
        return math.ceil(total_work / available_consultants)
    return math.ceil(total_work)


def find_free_consultant():
    for c in consultants:
        if c["busy_for"] == 0:
            return c
    return None


def serve_next_client():
    """Serve the oldest ticket only if a consultant is free.
    Returns (ticket, consultant) if served, or (None, reason_string) if not.
    """
    if not waiting_queue:
        return None, "No clients in the queue."

    free = find_free_consultant()
    if not free:
        return None, "No available consultants right now. Please wait or advance time."

    # Serve the oldest ticket (lowest ticket number)
    oldest_ticket = min(waiting_queue, key=lambda t: t["ticket_number"])
    waiting_queue.remove(oldest_ticket)
    service_time = service_times.get(oldest_ticket["service"], 0)
    free["busy_for"] = service_time
    return oldest_ticket, free


def print_full_queue():
    if not waiting_queue:
        print("\nQueue is empty.")
        return

    sorted_queue = sorted(waiting_queue, key=lambda ticket: ticket["ticket_number"])
    print("\n===== FULL QUEUE =====")
    print(f"{'Pos':>3}  {'Ticket':>6}  {'Service'}")
    print("-------------------------------")
    for position, ticket in enumerate(sorted_queue, start=1):
        print(f"{position:>3}   {ticket['ticket_number']:03}     {ticket['service']}")
    print("-------------------------------")
    print(f"Total waiting: {len(waiting_queue)}")


def print_consultants():
    print("\n===== CONSULTANTS =====")
    for c in consultants:
        status = f"Idle" if c["busy_for"] == 0 else f"Busy ({c['busy_for']} min left)"
        print(f"Consultant {c['id']}: {status}")
    print("=======================")


def advance_time(minutes):
    if minutes <= 0:
        return
    for c in consultants:
        c["busy_for"] = max(0, c["busy_for"] - minutes)


def cancel_ticket(ticket_no):
    for t in waiting_queue:
        if t["ticket_number"] == ticket_no:
            waiting_queue.remove(t)
            return True
    return False


while True:
    print_menu()
    try:
        choice = input("Choose your service: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        break

    # Exit the queue system
    if choice == "0":
        print("Queue system exited.")
        break

    # Consultant calls the next client in the queue (oldest ticket)
    if choice == "6":
        ticket, info = serve_next_client()
        if ticket:
            consultant = info
            print("\n===== CALLING NEXT CLIENT =====")
            print(f"Ticket number: {ticket['ticket_number']:03}")
            print(f"Service: {ticket['service']}")
            print(f"Assigned to consultant: {consultant['id']}")
            print("Clients waiting in the queue:", len(waiting_queue))
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
