# Bank Queue Management System

ticket_number = 1

waiting_queue = []

service_times = {
    "Open an account": 10,
    "Credit enquiry": 15,
    "Funeral/Life Cover": 10,
    "Business account": 8,
    "General enquiries": 8
}

available_consultants = 3 

def serve_oldest_ticket():
    if not waiting_queue:
        return None

    oldest_ticket = min(
        waiting_queue, key=lambda ticket: ticket["ticket_number"]
    )

    waiting_queue.remove(oldest_ticket)
    return oldest_ticket
            
while True:
    print("\n===== BANK QUEUE MANAGEMENT =====")

    print("Select your service")

    print("1. Open an account")
    print("2. Credit enquiry")
    print("3. Funeral/Life Cover")
    print("4. Business account")
    print("5. General enquiries")
    print("6. Call next client")
    print("7. View full queue")
    print("0. Exit")

    print("=================================")

    choice = input("Choose your service: ").strip()

    # Exit the queue system

    if choice == "0":
        print("Queue system exited.")
        break

    # Consultant calls the next client in the queue

    elif choice == "6":
        if len(waiting_queue) > 0:
            next_ticket = waiting_queue.pop(0)

            print("\n===== CALLING NEXT CLIENT =====")
            print(f"Ticket number: {next_ticket['ticket_number']:03}")
            print(f"Service: {next_ticket['service']}")

            print("Clients waiting in the queue:", len(waiting_queue))

        else:
            print("No clients in the queue.")

            # Return to the main menu without generating a ticket number

            continue

    elif choice =="7":
        if waiting_queue:
            print("\n===== FULL WAITING QUEUE ======")

            sorted_queue = sorted(
                waiting_queue, key=lambda ticket: ticket["ticket_number"]
            )

            for position, ticket in enumerate(sorted_queue, start=1):
                print(f"Position:{position}")
                print(f"Ticket:{ticket['ticket_number']:03}")
                print(f"Service:{ticket['service']}")

            print("Total clients waiting:", len(waiting_queue))

            print("========================================")

        else:
            print("There are no clients waiting.")

        continue

        # Client selects a service and generates a ticket number

    elif choice in ("1", "2", "3", "4", "5"):
        services = {
            "1": "Open an account",
            "2": "Credit enquiry",
            "3": "Funeral/Life Cover",
            "4": "Business account",
            "5": "General enquiries"
        }
        service = services[choice]

        # Count clients already waiting in the queue for the selected service

        people_ahead =len(waiting_queue)

        # Estimate waiting time based on the number of clients ahead and the service time for the selected service

        total_waiting_minutes = sum(service_times[client["service"]] for client in waiting_queue)

        estimated_waiting_time = (total_waiting_minutes / available_consultants)

        # Add the new client to the queue with their ticket number and selected service

        new_ticket = {"ticket_number": ticket_number, "service": service}

        waiting_queue.append(new_ticket)

        print("\n=======================================")
        print("            BANK QUEUE TICKET")
        print("=========================================")
        print(f"Ticket number: {ticket_number:03}")
        print(f"Service: {new_ticket['service']}")
        print(f"People ahead: {people_ahead}")
        print(f"Estimated waiting time: {estimated_waiting_time:.0f} minutes")
        print("------------------------------------------")
        print("Please wait until your number is called.")
        print("Thank you for your patience.")
        print("===========================================")

        print("Total clients waiting in the queue:", len(waiting_queue))
        print("=================================")

        ticket_number += 1