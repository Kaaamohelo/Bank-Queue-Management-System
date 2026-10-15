# Bank Queue Management System

A Python-based queue management simulation for a bank branch.The system allows clients to select a service,receive a ticket number and wait in a shared queue while staff monitor consultant availability and advance time to simulate service completion.

## Project Overview

This project was designed to model a simple bank service desk where:

- clients choose a banking service,
- tickets are generated in sequence,
- waiting times are estimated,
- and staff can call the next client and monitor consultant status.

The current version focuses on queue logic and basic simulation behavior using a command-line interface.

## Main File

- `Final Product_05.py`

## Features

- Service selection menu
- Unique ticket number generation
- Shared waiting queue for all services
- Estimated waiting time before service begins
- Consultant availability tracking
- Queue viewing functionality
- Time simulation for completed service work
- Ticket cancellation from the waiting queue
- Oldest-ticket-first service priority

## Banking Services Included

1. Open an account
2. Credit enquiry
3. Funeral/Life Cover
4. Business account
5. General enquiries

## How It Works

1. A client chooses a service from the menu.
2. A ticket number is assigned.
3. The client is added to the shared queue.
4. The system estimates how long the client may wait before being served.
5. Staff can view the queue,check consultant status,or call the next client.
6. Time can be advanced to simulate the completion of consultant work.

## Screenshot

N/A

## Technology Stack

- Python 3
- Visual Studio Code
- Git and GitHub

## Requirements

- Python 3.x

## Run the Project

From the project directory, run:

python "Final Product_05.py"

If your system uses Python 3 explicitly:

python3 "Final Product_05.py"

## Example Menu

===== BANK QUEUE MANAGEMENT =====

Select your service

1. Open an account
2. Credit enquiry
3. Funeral/Life Cover
4. Business account
5. General enquiries
6. Call next client
7. View full queue
8. View consultants status
9. Advance time (simulate minutes)
10. Cancel a ticket
0. Exit

=================================

## Project Status

Status: In development

This project is an educational prototype focused on queue management, ticket generation,waiting estimates and basic service simulation.

## Future Improvements

- Add more realistic queue logic for multiple service types and consultant workloads
- Improve waiting-time calculations based on active consultants and client demand
- Implement a graphical user interface
- Save queue state between program runs
- Add staff authentication and administrative controls
- Introduce ticket printing or digital queue display

## Learning Goals

This project supports learning in:

- Python programming fundamentals
- Lists and dictionaries
- Control flow and loops
- User input handling
- Basic simulation logic
- Queue management concepts

## Notes

This project is intended for educational practice and simulation purposes. It does not process real banking transactions or customer financial records.

## Author

Kaaamohelo
