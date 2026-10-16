import signal
import sys
from queue_core import (
    services,
    add_ticket,
    serve_next_client,
    estimate_wait_for_new_client,
    cancel_ticket,
    advance_time,
    load_state,
    mark_client_arrived,
    record_staff_action,
    waiting_queue,
    consultants,
)


def graceful_exit(signum=None, frame=None):
    print("\nState saved. Exiting.")
    sys.exit(0)


signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)


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
    print("11. Confirm client arrived")
    print("0. Exit")
    print("=================================")


def print_full_queue():
    if not waiting_queue:
        print("\nQueue is empty.")
        return

    sorted_queue = sorted(waiting_queue, key=lambda ticket: int(ticket.get("ticket_number", 0)))
    print("\n===== FULL QUEUE =====")
    print(f"{'Pos':>3}  {'Ticket':>6}  {'Service'}")
    print("-------------------------------")
    for position, ticket in enumerate(sorted_queue, start=1):
        print(f"{position:>3}   {int(ticket['ticket_number']):03}     {ticket['service']}")
    print("-------------------------------")
    print(f"Total waiting: {len(waiting_queue)}")


def print_consultants():
    print("\n===== CONSULTANTS =====")
    for c in consultants:
        status = "Idle" if int(c.get("busy_for", 0)) == 0 else f"Busy ({int(c.get('busy_for',0))} min left)"
        ticket = c.get("ticket")
        ticket_info = "" if not ticket else f" - Ticket {int(ticket.get('ticket_number')):03} ({ticket.get('service')})"
        print(f"Consultant {c.get('id')}: {status}{ticket_info}")
    print("=======================")


if __name__ == "__main__":
    while True:
        load_state()
        print_menu()
        try:
            choice = input("Choose your service: ").strip()
        except (EOFError, KeyboardInterrupt):
            graceful_exit()

        if choice == "0":
            graceful_exit()

        if choice == "6":
            ticket, info = serve_next_client()
            if ticket:
                consultant = info
                print("\n===== CALLING NEXT CLIENT =====")
                print(f"Ticket number: {int(ticket['ticket_number']):03}")
                print(f"Service: {ticket['service']}")
                print(f"Assigned to consultant: {consultant['id']}")
                print("Clients waiting in the queue:", len(waiting_queue))
            else:
                print(info)
            continue

        if choice == "7":
            record_staff_action("Viewed waiting queue")
            print_full_queue()
            continue

        if choice == "8":
            record_staff_action("Viewed consultant status")
            print_consultants()
            continue

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

        if choice == "11":
            try:
                tno = int(input("Enter the ticket number shown on the monitor: ").strip())
            except ValueError:
                print("Please enter a valid ticket number.")
                continue
            if mark_client_arrived(tno):
                print(f"Ticket {tno:03} marked in service.")
            else:
                print(f"Ticket {tno:03} is not the current public call.")
            continue

        if choice in services:
            service = services[choice]
            people_ahead = len(waiting_queue)
            ticket, estimated_waiting_time = add_ticket(service)

            print("\n=======================================")
            print("            BANK QUEUE TICKET")
            print("=======================================")
            print(f"Ticket number: {int(ticket['ticket_number']):03}")
            print(f"Service: {service}")
            print(f"People ahead: {people_ahead}")
            print(f"Estimated waiting time until start: {estimated_waiting_time} minutes")
            print("---------------------------------------")
            print("Please wait until your number is called.")
            print("Thank you for your patience.")
            print("=======================================")
            print("Total clients waiting in the queue:", len(waiting_queue))
            print("=================================")

            continue

        print("Invalid selection. Please choose a valid option.")
