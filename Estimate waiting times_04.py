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

while True:
    print("\n===== BANK QUEUE MANAGEMENT =====")

    print("Select your service")
    
    print("1. Open an account")
    print("2. Credit enquiry")
    print("3. Funeral/Life Cover")
    print("4. Business account")
    print("5. General enquiries")
    print("0. Exit")

    choice = input("Choose your service: ")

    if choice == "0":
        print("Queue system exited.")
        break

    elif choice == "1":
        service = "Open an account"

    elif choice == "2":
        service = "Credit enquiry"

    elif choice == "3":
        service = "Funeral/Life Cover"

    elif choice == "4":
        service = "Business account"

    elif choice == "5":
        service = "General enquiries"

    else:
        print("Invalid choice. Please try again.")
        continue

    people_ahead = len(waiting_queue)

    estimated_waiting_time = 0

    for ticket in waiting_queue:
        estimated_waiting_time += service_times[ticket["service"]]

    if available_consultants > 0:
        estimated_waiting_time = estimated_waiting_time / available_consultants

    waiting_queue.append({"ticket_number": ticket_number, "service": service
    })                      

    print("\n=======================================")
    print("            BANK QUEUE TICKET")
    print("=========================================")
    print(f"Ticket number: {ticket_number:03}")
    print(f"Service: {service}")
    print(f"People ahead: {people_ahead}")
    print(f"Estimated waiting time: {estimated_waiting_time:.1f} minutes")
    print("------------------------------------------")
    print("Please wait until your number is called.")
    print("Thank you for your patience.")
    print("===========================================")

    print("Total clients waiting in the queue:", len(waiting_queue))


    print("=================================")

    ticket_number += 1