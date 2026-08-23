import json

from socket import socket


class Messenger:
    """Handle sending and receiving JSON messages."""

    def __init__(self, connection: socket) -> None:
        """Initialise the Messenger with a connection socket and an empty buffer."""
        self.connection = connection
        self.buffer = "" # Stores incomplete messages until a full message is received

    def send_message(
            self,
            name: str,
            message_type: str,
            data: str | tuple[int, int] # Can be a string or a tuple of two integers (coordinates)
        ) -> None:
        """Send a JSON message."""
        message = {
            "name": name,
            "type": message_type,
            "data": data
        }

        json_message = json.dumps(message) + "\n" # Convert dictionary to JSON string and mark the end
        encoded_message = json_message.encode() # Encode the JSON string to UTF-8 bytes

        self.connection.send(encoded_message)

    def receive_message(self) -> dict:
        """Receive and decode one JSON message."""
        while "\n" not in self.buffer: # Keep receiving until a complete message is in the buffer
            try:
                data = self.connection.recv(1024) # Receive up to 1024 bytes
            except (ConnectionResetError, ConnectionAbortedError): # Handle the connection being forcibly closed
                return {}

            if not data: # If the client disconnects
                return {}

            self.buffer += data.decode() # Decode the UTF-8 bytes and append them to the buffer

        message, self.buffer = self.buffer.split("\n", 1) # Split the buffer into a complete message and the remaining buffer
        return json.loads(message) # Parse the JSON string into a dictionary and return it