import curses

from threading import Thread
from json import dumps


class ServerUI:
    """Display the server interface."""

    def __init__(self, server) -> None:
        """Initialise the ServerUI."""
        self.server = server

    def start(self) -> None:
        """Start the server and server UI."""
        thread = Thread(
            target=self.server.start, # Run the server separately so the UI can run at the same time
            daemon=True # Stop the server thread automatically when the main program exits
        )
        thread.start()
        curses.wrapper(self.draw) # Start the UI and handle terminal cleanup afterwards

    def draw(self, screen) -> None:
        """Draw the server interface."""
        curses.curs_set(0) # Hide terminal cursor

        while True:
            screen.clear()

            height, width = screen.getmaxyx()

            # Split the screen 50/50
            left_width = width // 2
            right_width = width - left_width

            # Create the players window on the left side
            players = screen.derwin(
                height,
                left_width,
                0,
                0
            )

            # Create the messages window on the right side
            messages = screen.derwin(
                height,
                right_width,
                0,
                left_width
            )

            self.draw_players(players)
            self.draw_messages(messages)

            screen.refresh()

            screen.timeout(100) # Wait up to 100ms for keyboard input so the UI keeps updating

            if screen.getch() == 27: # Escape key
                break

    def draw_window(self, window, title: str) -> None:
        """Draw the border and title of a window."""
        window.clear()
        window.box()
        window.addstr(0, 2, f" {title} ")

    def draw_players(self, window) -> None:
        """Draw connected players."""
        self.draw_window(window, "PLAYERS")
        y = 1

        for messenger in self.server.client_messengers:
            if y >= window.getmaxyx()[0] - 1: # Stop if there is no more room in the window
                break

            window.addstr(
                y,
                2,
                f"{self.server.player_names[messenger]}: {messenger.connection.getpeername()[0]}" # Name: IP
            )

            y += 1

    def draw_messages(self, window) -> None:
        """Draw server messages."""
        self.draw_window(window, "MESSAGES")

        height, width = window.getmaxyx()
        y = 1

        # Draw the most recent messages that fit in the window
        for message in self.server.messages[-(height - 2):]:
            text = dumps(message)

            window.addstr(
                y,
                2,
                text[:width - 4] # Trim the message so it fits inside the window
            )

            y += 1