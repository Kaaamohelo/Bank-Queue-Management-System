# Bank-Queue-Management-System

## Project Overview:

The Bank Queue Management System is a Python-based project designed to improve the customer queuing experience in the branch.The system allows clients to select the banking service they require,receive a unique queue ticket and view an estimated waiting time before being assisted.

The goal is to develop a simple,practical queue management solution that helps organise customers,reduce confusion and support a first-come,first-served queuing process.

## Objectives:

-Generate unique ticket numbers for clients.

-Allow clients to select their required banking service.

-Display ticket details clearly.

-Calculate estimated waiting times.

-Maintain an organised queue based on customer arrivals.

-Develop a foundation for a future graphical ticket-printing system.

## Technology Stack:

-Python

-Visual Studio Code

-Git and GitHub Desktop

-GitHub for source-code management and project documentation

## How does it work work?

1.The client selects a banking service.

2.The system identifies the selected service.

3.A unique ticket number is assigned.

4.The system calculates an estimated waiting time.

5.The ticket details are displayed for the client.

The intended numbering system uses one sequence across all services, ensuring that each newly issued ticket receives a different number.

## Current Features:

-Service selection: Clients can select open an account,credit enquiries,funeral/life cover,business account or general enquiries.

-Unique ticket numbering: Each client receives a sequential ticket number shared across all banking services.

-Service-specific queue tracking: The system maintains a separate waiting-client count for each banking service.

-Estimated waiting times: The system estimates the waiting time based on the number of clients already waiting for the selected service and its configured average service duration.

-Ticket display: The system displays the ticket number,selected service,number of people ahead in that service queue and estimated waiting time.

-Continuous operation: The system can issue tickets to multiple clients during one program run.

## Current Limitation:

-Waiting counts are not yet reduced when clients are assisted.

-Ticket numbers and queue counts reset when the program restarts.

-Waiting times are simplified estimates based on configured service durations.

-The system does not yet account for multiple consultants,actual service durations or delays.

-Tickets are displayed in the terminal; physical ticket printing has not yet been implemented.

## Future Improvements:

-Add a staff function to call and complete tickets.

-Update queue counts and waiting-time estimates as clients are assisted.

-Save ticket numbers and queue data between program restarts.

-Introduce a graphical interface and printable ticket layout.

-Support multiple consultants and more realistic waiting-time calculations.

## Learning Goals:

This project is also part of my practical journey into software development.Through building it I am developing my understanding of Python fundamentals,including variables,data types,conditional statements,loops,user input,formatted output and basic program logic.

## Note: This is an educational prototype.It is not yet a production-ready banking system and does not process real customer information or banking transactions.


This project is developed as a personal programming project to practise Python and build practical software development skills.

Status : In development 
