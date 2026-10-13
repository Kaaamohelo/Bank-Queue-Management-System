ticket_number = 1

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

    print(f"\nYour ticket number for {service} is: {ticket_number:03}")
    ticket_number += 1