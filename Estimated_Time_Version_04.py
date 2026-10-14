ticket_number = 1

waiting_clients = {
    "Open an account": 0,
    "Credit enquiry": 0,
    "Funeral/Life Cover": 0,
    "Business account": 0,
    "General enquiries": 0
}

service_times = {
    "Open an account": 10,
    "Credit enquiry": 15,
    "Funeral/Life Cover": 10,
    "Business account": 8,
    "General enquiries": 8
}

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

    people_ahead = waiting_clients[service]
    estimated_wait = people_ahead * service_times[service]

    waiting_clients[service] += 1

    print("\n========== YOUR TICKET ==========")
    print(f"Ticket number:{ticket_number:03}")
    print(f"Service: {service}")
    print(f"People ahead in this service: {people_ahead}")
    print(f"Estimated wait time: {estimated_wait} minutes")


    print("Please wait until your number is called.")

    print("Current waiting clients for each service:")


    for service, count in waiting_clients.items():
        print(f"  {service}: {count}")


        print("=================================")

    ticket_number += 1