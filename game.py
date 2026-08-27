import curses

from socket import socket
from threading import Thread
from textwrap import wrap
from messenger import Messenger


ip = input("IP: ")

while True:
    name = input("Name: ")

    if 1 <= len(name) <= 16:
        break

    print("Name must be between 1 and 16 characters.")


class Game:
    """Handle the game client."""

    def __init__(self, screen) -> None:
        """Initialise the game client and its attributes."""
        self.screen = screen
        self.ip = ip
        self.name = name

        # Network and received messages
        self.client = socket()
        self.messenger = Messenger(self.client)
        self.messages = []

        # Terminal and game windows
        self.height = 0
        self.width = 0
        self.game_width = 0
        self.chat_width = 0
        self.game = None
        self.chat = None

        # World
        self.world_width = 300
        self.world_height = 100

        # Player position within the world
        self.x = 0
        self.y = 0

        # Camera position within the world
        self.camera_x = 0
        self.camera_y = 0

        # Coordinates of all other players within the world
        self.player_coords = {}

        # Chat
        self.chat_mode = False
        self.chat_input = ""

    def connect(self) -> None:
        """Connect to the server and start receiving messages."""
        self.client.connect((self.ip, 5000)) # Connect to the server on port 5000

        thread = Thread(target=self.receive_messages)
        thread.start() # The thread will run independently and continuously receive messages from the server

        self.messenger.send_message(self.name, "join", "")

    def receive_messages(self) -> None:
        """Continuously receive and process JSON messages."""
        while True:
            message = self.messenger.receive_message()

            if not message:
                break

            if message["type"] == "position":
                name = message["name"]
                position = message["data"]

                self.player_coords[name] = position # Store the new position

            elif message["type"] in ("chat", "join"):
                self.messages.append(message)

            elif message["type"] == "leave":
                self.messages.append(message)
                del self.player_coords[message["name"]] # Remove the player from the list of players

    def setup(self) -> None:
        """Set up the game screen."""
        curses.curs_set(0) # Hide terminal cursor
        self.screen.nodelay(True) # Make getch() non-blocking so the game keeps running

        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK) # Blue text on black background
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Yellow text on black background

        self.height, self.width = self.screen.getmaxyx() # Get the size of the terminal

        # Split the terminal into a game and chat window (70/30)
        self.game_width = int(self.width * 0.7)
        self.chat_width = self.width - self.game_width

        # Create the game window
        self.game = curses.newwin(
            self.height,
            self.game_width,
            0,
            0
        )

        # Create the chat window
        self.chat = curses.newwin(
            self.height,
            self.chat_width,
            0,
            self.game_width
        )

        # Start the player in the middle of the world
        self.x = self.world_width // 2
        self.y = self.world_height // 2

    def update_camera(self) -> None:
        """Update the camera to follow the player."""
        # Position the camera so the player is in the middle of the screen
        self.camera_x = self.x - self.game_width // 2
        self.camera_y = self.y - self.height // 2

        # Keep the camera's X position inside the world
        # The camera cannot go below 0 or beyond the world's right edge
        self.camera_x = max(
            0,
            min(self.camera_x, self.world_width - self.game_width)
        )

        # Keep the camera's Y position inside the world
        # The camera cannot go below 0 or beyond the world's bottom edge
        self.camera_y = max(
            0,
            min(self.camera_y, self.world_height - self.height)
        )

    def draw(self) -> None:
        """Draw the game."""
        assert self.game is not None # Keeps PyLance happy
        
        self.game.clear()
        self.game.box() # Draw a box around the window
        self.game.addstr(0, 2, " GAME ")

        self.draw_players()
        self.draw_chat()

        self.game.refresh()

    def draw_players(self) -> None:
        """Draw the player and other players."""
        assert self.game is not None  # Keeps PyLance happy

        # Player coordinates within the screen
        player_x = self.x - self.camera_x
        player_y = self.y - self.camera_y

        # Only draw the player if they are visible
        if 1 <= player_x < self.game_width - 1:
            if 1 <= player_y < self.height - 1:
                self.game.addstr(player_y, player_x, "@")

        for name, position in self.player_coords.items():
            player_x = position[0] - self.camera_x
            player_y = position[1] - self.camera_y

            if 1 <= player_x < self.game_width - 1:
                if 1 <= player_y < self.height - 1:
                    self.game.addstr(player_y, player_x, "#")

    def draw_chat(self) -> None:
        """Draw the chat window, including messages and the player's current input."""
        assert self.chat is not None

        self.chat.clear()
        self.chat.box()
        self.chat.addstr(0, 2, " CHAT ")

        chat_lines = self.get_chat_lines()
        self.draw_chat_lines(chat_lines)

        if self.chat_mode:
            self.draw_chat_input()

        self.chat.refresh()

    def get_chat_lines(self) -> list:
        """Format chat messages into lines that can be displayed."""
        max_width = self.chat_width - 4
        chat_lines = []

        for message in self.messages:
            if message["type"] == "chat":
                chat_lines.extend(
                    self.get_chat_message_lines(message, max_width)
                )

            elif message["type"] == "join":
                chat_lines.extend(
                    self.get_server_message_lines(
                        f"[SERVER] {message['name']} joined the game.",
                        max_width
                    )
                )

            elif message["type"] == "leave":
                chat_lines.extend(
                    self.get_server_message_lines(
                        f"[SERVER] {message['name']} left the game.",
                        max_width
                    )
                )

        return chat_lines[-(self.height - 3):]

    def get_chat_message_lines(self, message: dict, max_width: int) -> list:
        """Format a chat message into displayable lines."""
        name = message["name"]
        data = message["data"]

        if len(f"{name}: {data}") <= max_width:
            return [
                ("chat", name, f": {data}")
            ]

        # Splits the message into smaller strings that are no longer than max_width
        lines = wrap(f"{name}: {data}", max_width)
        chat_lines = []

        for line_number, line in enumerate(lines):
            if line_number == 0: # This line contains the player's name
                chat_lines.append(
                    ("chat", name, line[len(name):])
                )

            else:
                chat_lines.append(
                    ("normal", None, line)
                )

        return chat_lines

    def get_server_message_lines(self, text: str, max_width: int) -> list:
        """Format a server message into displayable lines."""
        lines = wrap(text, max_width) # Split the server message into lines if too long
        chat_lines = []

        for line in lines:
            chat_lines.append(
                ("server", None, line)
            )

        return chat_lines

    def draw_chat_lines(self, chat_lines: list) -> None:
        """Draw the chat messages."""
        assert self.chat is not None
        y = 1

        for line_type, name, text in chat_lines:
            if line_type == "chat":
                self.chat.addstr(
                    y,
                    2,
                    name,
                    curses.color_pair(1) | curses.A_BOLD # Name is blue and bold
                )

                self.chat.addstr(
                    y,
                    2 + len(name), # Rest is white
                    text
                )

            elif line_type == "server":
                self.chat.addstr(
                    y,
                    2,
                    text,
                    curses.color_pair(2) | curses.A_BOLD # Whole message is yellow and bold
                )

            else:
                self.chat.addstr(
                    y,
                    2,
                    text
                )

            y += 1

    def draw_chat_input(self) -> None:
        """Draw the player's current chat input."""
        assert self.chat is not None

        max_input_width = self.chat_width - 4

        # Trim the input if it is too long to fit
        chat_input = self.chat_input[:max_input_width - 2] # -2 leaves room for the "> " at the beginning

        # Display the text the player is currently typing
        self.chat.addstr(
            self.height - 2,
            2,
            f"> {chat_input}"
        )

    def handle_key(self, key: int) -> bool:
        """Handle a key press and return whether the game should continue."""
        if key == 27:
            return self.handle_escape()

        if key == ord("/"):
            self.chat_mode = True
            return True

        if self.chat_mode:
            self.handle_chat_key(key)
            return True

        self.handle_movement(key)
        return True

    def handle_escape(self) -> bool:
        """Exit chat mode or close the game."""
        if self.chat_mode:
            self.chat_mode = False
            self.chat_input = ""
            return True

        self.messenger.send_message(self.name, "leave", "")
        return False

    def handle_chat_key(self, key: int) -> None:
        """Handle a key press while in chat mode."""
        if key in (curses.KEY_ENTER, 10, 13): # Handle different key codes used by different terminals
            if self.chat_input: # Only send the message if it contains text
                self.messenger.send_message(
                    self.name,
                    "chat",
                    self.chat_input
                )
                self.chat_input = "" # Clear the input after sending

            self.chat_mode = False

        elif key in (curses.KEY_BACKSPACE, 8, 127): # Handle different key codes used by different terminals
            self.chat_input = self.chat_input[:-1] # Remove the last character from the input

        elif 32 <= key <= 126: # Only add printable characters to the input
            self.chat_input += chr(key)

    def handle_movement(self, key: int) -> None:
        """Handle movement keys."""
        old_position = (self.x, self.y)

        if key == curses.KEY_UP:
            self.y -= 1

        elif key == curses.KEY_DOWN:
            self.y += 1

        elif key == curses.KEY_LEFT:
            self.x -= 2 # Move 2 spaces to match vertical movement

        elif key == curses.KEY_RIGHT:
            self.x += 2

        # Keep the player's X position between 1 and world_width - 2.
        self.x = max(1, min(self.x, self.world_width - 2))
        
        # Keep the player's Y position between 1 and world_height - 2.
        self.y = max(1, min(self.y, self.world_height - 2))

        new_position = (self.x, self.y)

        if new_position != old_position: # Prevents sending position messages when bumped against world boundary
            self.messenger.send_message(
                self.name,
                "position",
                new_position
            )

    def run(self) -> None:
        """Run the game loop."""
        self.connect()
        self.setup()
        self.messenger.send_message(
            self.name,
            "position",
            (self.x, self.y)
        ) # Send the initial position so that existing players can see the new player

        while True:
            self.update_camera()
            self.draw()

            key = self.screen.getch() # Check for keyboard input (-1 if none)

            if key == -1:
                continue # No key pressed, start the loop again

            if not self.handle_key(key):
                break

        self.client.shutdown(1) # Shutdown the socket for sending data
        self.client.close()


def main(screen) -> None:
    """Start the game."""
    game = Game(screen)
    game.run()


curses.wrapper(main) # Start the game and handle terminal cleanup afterwards