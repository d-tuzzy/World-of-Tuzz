from socket import socket
from threading import Thread
from messenger import Messenger


class Server:
    """Handle the server and connected clients."""

    def __init__(self) -> None:
        """Initialise the Server with a server socket and its connected clients."""
        self.socket = socket()
        self.player_coords = {} # Coordinates of all players

        # Each client has a Messenger that stores its connection and buffer.
        # Storing Messengers (instead of just the connections) lets us identify clients while reusing the same Messenger.
        # Otherwise, we would have to create a new Messenger for each message sent.
        self.client_messengers = []

    def broadcast_message(self, message: dict, sender: socket | None) -> None:
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
        player_name = None

        while True:
            message = messenger.receive_message()

            if not message: # If the client has disconnected
                if player_name != None:
                    self.remove_player(player_name, connection)

                break # Break before broadcasting so the other clients don't get a blank message

            if message["type"] == "position": # If a player has sent a position message
                name = message["name"]
                position = message["data"]

                self.player_coords[name] = position # Store the new position

            elif message["type"] == "join": # If a player has sent a join message
                player_name = message["name"] # Will be used to identify the player if they disconnect abruptly

                # Send existing player positions to the new player
                for name, position in self.player_coords.items():
                    messenger.send_message(name, "position", position)

            elif message["type"] == "leave": # If a player has sent a leave message
                self.remove_player(message["name"], connection)
                break

            if message["type"] == "chat":
                self.broadcast_message(message, sender=None) # Let players see their own chat message
            else:
                self.broadcast_message(message, sender=connection)

            print(message) # FOR TESTING

        self.client_messengers.remove(messenger) # Remove the client from the list
        connection.close() # Close the client connection

    def remove_player(self, player_name: str, connection: socket) -> None:
        """Remove a player and tell the other clients."""
        if player_name in self.player_coords:
            del self.player_coords[player_name]

        message = {
            "name": player_name,
            "type": "leave",
            "data": ""
        }

        print(message)
        self.broadcast_message(message, sender=connection)

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
            thread.start() # The thread for this player will run separately from the main thread


if __name__ == "__main__":
    server = Server()
    server.start()