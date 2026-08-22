import curses

from socket import socket
from threading import Thread
from messenger import Messenger


ip = input("IP: ")
name = input("Name: ")

messages = [] # List to store received messages


def main(screen) -> None:
    client = socket()
    client.connect((ip, 5000)) # Connect to the server on port 5000
    messenger = Messenger(client) # Create a Messenger for this client

    receive_thread = Thread(
        target=messenger.receive_messages,
        args=(messages,)
    )
    receive_thread.start() # The thread will run independently and continuously receive messages from the server

    messenger.send_message(name, "JOIN")

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
            messenger.send_message(name, "ESC")
            break

        elif key == curses.KEY_UP:
            y -= 1
            messenger.send_message(name, "UP")

        elif key == curses.KEY_DOWN:
            y += 1
            messenger.send_message(name, "DOWN")

        elif key == curses.KEY_LEFT:
            x -= 2 # Move 2 spaces to match vertical movement
            messenger.send_message(name, "LEFT")

        elif key == curses.KEY_RIGHT:
            x += 2
            messenger.send_message(name, "RIGHT")

    client.close()

curses.wrapper(main) # Start the game and handle terminal cleanup afterwards