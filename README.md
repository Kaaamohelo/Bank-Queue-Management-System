# Bank-Queue-Management-System

## Project Overview:

The Bank Queue Management System is a Python-based project designed to issue client queue tickets,estimate waiting times and manage clients waiting to be served in a bank branch.

The goal is to develop a simple,practical queue management solution that helps organise customers,reduce confusion,focus on ticket generation and queue management rather than processing banking transactions.

## Objectives:

-Generate unique ticket numbers for clients.

-Allow clients to select their required banking service.

-Display ticket details clearly.

-Calculate estimated waiting times.

-Maintain an organised queue based on client arrivals.

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

## Current Features:

-Service selection: Clients can select open an account,credit enquiries,funeral/life cover,business account or general enquiries.

-Unique ticket numbering: Each client receives a sequential ticket number shared across all banking services.

-Service-specific queue tracking: The system maintains a shared queue across different service types.

-Estimated waiting times: The system uses a configurable service times to estimate customer waiting times.

-Account for the number of available consultants when calculating estimates waiting times.

-Display the total number of clients waiting. 

-Allow consultants to call the next ticket.

-Ticket display: The system displays the ticket number,selected service,number of people ahead in that service queue and estimated waiting time.

-Continuous operation: The system continues issuing tickets util the system is closed.

## Current Limitation:

-Waiting counts are not yet reduced when clients are assisted.

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

## Note: This is an educational prototype that focuses on client ticket generation,queue tracking,basic queue managment and does not process real customer information or banking transactions.


This project is developed as a personal programming project to practise Python and build practical software development skills.

Status : In development 

LATEST UPDATE : 14 OCTOBER 2026
