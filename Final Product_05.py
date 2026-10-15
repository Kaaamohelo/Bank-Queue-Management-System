import math

# Bank Queue Management System

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
    print("0. Exit")
    print("=================================")


def estimate_wait_for_new_client():
    """Estimate the wait time for a new client joining the queue."""
    total_waiting_minutes = sum(service_times[client["service"]] for client in waiting_queue)
    if available_consultants > 0:
        return math.ceil(total_waiting_minutes / available_consultants)
    return math.ceil(total_waiting_minutes)


def serve_oldest_ticket():
    """Serve the oldest ticket in the queue (lowest ticket number)."""
    if not waiting_queue:
        return None
    oldest_ticket = min(waiting_queue, key=lambda ticket: ticket["ticket_number"])
    waiting_queue.remove(oldest_ticket)
    return oldest_ticket


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


while True:
    print_menu()
    choice = input("Choose your service: ").strip()

    # Exit the queue system
    if choice == "0":
        print("Queue system exited.")
        break

    # Consultant calls the next client in the queue (oldest ticket)
    if choice == "6":
        next_ticket = serve_oldest_ticket()
        if next_ticket:
            print("\n===== CALLING NEXT CLIENT =====")
            print(f"Ticket number: {next_ticket['ticket_number']:03}")
            print(f"Service: {next_ticket['service']}")
            print("Clients waiting in the queue:", len(waiting_queue))
        else:
            print("No clients in the queue.")
        continue

    # View the full queue
    if choice == "7":
        print_full_queue()
        continue

    # Client selects a service and generates a ticket number
    if choice in services:
        service = services[choice]

        # Number of clients already waiting in the shared queue
        people_ahead = len(waiting_queue)

        # Estimate waiting time based on the total queued service time shared by all consultants.
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
        print(f"Estimated waiting time: {estimated_waiting_time} minutes")
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
