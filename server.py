from socket import socket
from threading import Thread
from messenger import Messenger


class Server:
    """Handle the server and connected clients."""

    def __init__(self) -> None:
        """Initialise the Server with a server socket and its connected clients."""
        self.socket = socket()
        self.players = {} # Coordinates of all other players

        # Each client has a Messenger that stores its connection and buffer.
        # Storing Messengers (instead of just the connections) lets us identify clients while reusing the same Messenger.
        # Otherwise, we would have to create a new Messenger for each message sent.
        self.client_messengers = []

    def broadcast_message(self, message: dict, sender: socket) -> None:
        """Send a message to every client except the sender."""
        for messenger in self.client_messengers:
            if messenger.connection != sender: # Ignore the sender
                messenger.send_message(
                    message["name"], # Use the name from the dictionary
                    message["type"], # Use the message type from the dictionary
                    message["data"]  # Use the data from the dictionary
                )

    def handle_client(self, messenger: Messenger) -> None:
        """Handle communication with a connected client in its own thread."""
        connection = messenger.connection # Use the connection to identify the client

        while True:
            message = messenger.receive_message()

            if not message: # If the client has disconnected
                break # Break before broadcasting so the other clients don't get a blank message

            if message["type"] == "position": # If a player has sent a position message
                name = message["name"]
                position = message["data"]

                self.players[name] = position # Store the new position

            print(message) # FOR TESTING
            self.broadcast_message(message, sender=connection)

            if message["type"] == "leave": # If the client has sent a leave message
                break

        self.client_messengers.remove(messenger) # Remove the client from the list
        connection.close() # Close the client connection

    def start(self) -> None:
        """Start the server, accept connections, and make threads."""
        self.socket.bind(("0.0.0.0", 5000)) # Bind to port 5000 and accept connections from any device
        self.socket.listen() # Start listening for connection

        print("Waiting...")

        while True:
            connection, address = self.socket.accept() # Wait for a client and return its connection socket + address tuple

            messenger = Messenger(connection) # Make a unique Messenger for this client
            self.client_messengers.append(messenger)

            thread = Thread(
                target=self.handle_client, # The thread will run handle_client
                args=(messenger,) # Pass the client's Messenger as the argument (in a single tuple)
            )
            thread.start() # The thread for this player will run separately from the main thread.


if __name__ == "__main__":
    server = Server()
    server.start()