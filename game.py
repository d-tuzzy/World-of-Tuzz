import curses
from socket import socket


ip = input("IP: ")

def main(screen):
    client = socket()
    client.connect((ip, 5000)) # Connect to the server on port 5000

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

        game.refresh() # Update the game window

        key = screen.getch() # Check for keyboard input (-1 if none)

        if key == -1:
            continue # No key pressed, start the loop again

        if key == 27: # Escape key
            client.send(b"ESC") # Send "ESC" as bytes to the server
            break

        elif key == curses.KEY_UP:
            y -= 1
            client.send(b"UP")

        elif key == curses.KEY_DOWN:
            y += 1
            client.send(b"DOWN")

        elif key == curses.KEY_LEFT:
            x -= 2 # Move 2 spaces to match vertical movement
            client.send(b"LEFT")

        elif key == curses.KEY_RIGHT:
            x += 2
            client.send(b"RIGHT")

    client.close()

curses.wrapper(main) # Start the game and handle terminal cleanup afterwards