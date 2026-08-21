import curses
import json

from socket import socket
from threading import Thread


ip = input("IP: ")
name = input("Name: ")

messages = [] # List to store received messages


def receive_messages(client: socket) -> None:
    """Receive and decode JSON messages from the connected server."""

    buffer = ""

    while True:
        data = client.recv(1024) # Receive up to 1024 bytes

        if not data: # If the server disconnects
            break

        buffer += data.decode() # Append decoded data to the buffer

        while "\n" in buffer: # While there is a complete message in the buffer
            message, buffer = buffer.split("\n", 1) # Split the buffer into a complete message and the remaining buffer
            message = json.loads(message) # Decode the JSON message from the server

            messages.append(message)


def send_message(client: socket, name: str, message: str) -> None:
    """Send a JSON message to the server."""

    data = {
        "name": name,
        "message": message
    }

    json_data = json.dumps(data) + "\n" # Convert dictionary to JSON string and mark the end
    encoded_data = json_data.encode() # Encode the JSON string to bytes

    client.send(encoded_data) # Send the encoded JSON message to the server


def main(screen) -> None:
    client = socket()
    client.connect((ip, 5000)) # Connect to the server on port 5000

    receive_thread = Thread(
        target=receive_messages, # The thread will run receive_messages
        args=(client,) # Pass the client socket as the argument (in a single tuple)
    )
    receive_thread.start() # The thread will receive messages from the server independently

    send_message(client, name, "JOIN")

    curses.curs_set(0) # Hide terminal cursor
    screen.nodelay(True) # Make getch() non-blocking so the game keeps running

    height, width = screen.getmaxyx() # Get the size of the terminal

    game = curses.newwin(height, width, 0, 0) # Create the game window

    x = width // 2 # Start the player in the middle of the window
    y = height // 2 

    while True:
        game.clear()

        game.box() # Draw a box around the window
        game.addstr(0, 2, " GAME ") # Add the game title
        game.addstr(y, x, "@") # Draw the player at their current position

        for i, message in enumerate(messages): # Use the message index for the y-coordinate
            game.addstr(i + 1, 2, str(message)) # FOR TESTING: Display received messages in the game window

        game.refresh() # Update the game window

        key = screen.getch() # Check for keyboard input (-1 if none)

        if key == -1:
            continue # No key pressed, start the loop again

        if key == 27: # Escape key
            send_message(client, name, "ESC")
            break

        elif key == curses.KEY_UP:
            y -= 1
            send_message(client, name, "UP")

        elif key == curses.KEY_DOWN:
            y += 1
            send_message(client, name, "DOWN")

        elif key == curses.KEY_LEFT:
            x -= 2 # Move 2 spaces to match vertical movement
            send_message(client, name, "LEFT")

        elif key == curses.KEY_RIGHT:
            x += 2
            send_message(client, name, "RIGHT")

    client.close()

curses.wrapper(main) # Start the game and handle terminal cleanup afterwards