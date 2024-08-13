This project is a library management system designed with a microservices architecture, ensuring modularity and scalability.

The system includes:

Books Service: Manages the catalog of books, handling operations like adding, updating, and retrieving book details.

Loans Service: Tracks book loans, including borrowers, due dates, and returns.

The architecture utilizes:

NGINX: Acts as a reverse proxy, efficiently routing requests to the appropriate services and managing traffic.

MongoDB: Serves as the database for storing book and loan information, providing flexibility and scalability.

Docker & Docker Compose: The application is fully containerized, with Docker Compose managing the deployment of the multi-container setup, making it easy to start and maintain the system.

How to Run:
Clone the repository.
Ensure Docker and Docker Compose are installed.
Run docker-compose up to start all services.
This setup provides a scalable, easy-to-deploy library management system suitable for various environments
