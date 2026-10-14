print("========================")
print(" BANK QUEUE MANAGEMENT")
print("========================")

print("Select your service")
print("1.Open an account")
print("2.Credit enquiry")
print("3.Funeral/Life Cover")
print("4.Business account")
print("5.General enquiries")

service_choice = input("Enter your choice (1-5): ")

if service_choice =="1":
    service = "Open an account"
    prefix = "GENERAL"
    service_time = 10

elif service_choice == "2":
    service = "Credit enquiry"
    prefix = "Credit"
    service_time = 15

elif service_choice == "3":
    servive = "Funeral/Life Cover"
    prefix =  "Funeral/Life"
    service_time = 10

elif service_choice == "4":
    service = "Business account"
    prefix = "Business"
    service_time = 8

elif service_choice == "5":
    service = "General enquiries"
    prefix = "INFO"
    service_time = 8 

else:
    print("Invalid choice. Please restart.")
    raise SystemExit

ticket_number = 1
people_ahead = 3

estimated_wait = people_ahead *service_time

print("\n========== YOUR TICKET ==========")
print(f"Ticket: {prefix}{ticket_number:03}")
print(f"Service: {service}")
print(f"People ahead:{people_ahead}")
print(f"Estimated wait:{estimated_wait} minutes")
print("Please wait until your number is called.")
print("===========================================")
