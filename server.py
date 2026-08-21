import json

from socket import socket
from threading import Thread


clients = [] # List to store connected clients


def handle_client(connection: socket) -> None:
    """Handle communication with a connected client."""

    buffer = ""
    running = True

    while running:
        data = connection.recv(1024) # Receive up to 1024 bytes

        if not data: # If the client disconnects
            break

        buffer += data.decode() # Append decoded data to the buffer

        while "\n" in buffer: # While there is a complete message in the buffer
            message, buffer = buffer.split("\n", 1) # Split the buffer into a complete message and the remaining buffer
            message = json.loads(message) # Decode the JSON message from the client

            print(message) # FOR TESTING

            for client in clients:
                if client != connection:
                    json_data = json.dumps(message) + "\n" # Convert dictionary to JSON string and mark the end
                    encoded_data = json_data.encode() # Encode the JSON string to bytes

                    client.send(encoded_data) # Send the encoded JSON message to the client
                
            if message["message"] == "ESC":
                running = False # Break out of the outer loop

    clients.remove(connection) # Remove the client from the list
    connection.close() # Close the client connection


def main() -> None:
    server = socket()
    server.bind(("0.0.0.0", 5000)) # Bind to port 5000 and accept connections from any device
    server.listen() # Start listening for connection

    print("Waiting...")

    while True:
        connection, address = server.accept() # Wait for a client and return its connection socket + address tuple

        clients.append(connection)

        thread = Thread(
            target=handle_client, # The thread will run handle_client
            args=(connection,) # Pass the connection socket as the argument (in a single tuple)
        )
        thread.start() # The thread for this player will run independently


if __name__ == "__main__":
    main()