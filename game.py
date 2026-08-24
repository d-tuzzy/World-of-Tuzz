import curses

from socket import socket
from threading import Thread
from messenger import Messenger


ip = input("IP: ")
name = input("Name: ")


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

        # World
        self.world_width = 300
        self.world_height = 100

        # Player position within the world
        self.x = 0
        self.y = 0

        # Camera position within the world (top-left corner)
        self.camera_x = 0
        self.camera_y = 0

        # Coordinates of all other players within the world
        self.player_coords = {}

        # Chat
        self.chat_mode = False
        self.chat_input = ""

        # Terminal and game window
        self.height = 0
        self.width = 0
        self.game = None

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

            if message["type"] == "position": # If a player has sent a position message
                name = message["name"]
                position = message["data"]

                self.player_coords[name] = position # Store the new position

            elif message["type"] in ("chat", "join"): # If a player has sent a chat or join message
                self.messages.append(message)

            elif message["type"] == "leave":
                self.messages.append(message)
                del self.player_coords[message["name"]] # Remove the player from the list of players

    def setup(self) -> None:
        """Set up the game screen."""
        curses.curs_set(0) # Hide terminal cursor
        self.screen.nodelay(True) # Make getch() non-blocking so the game keeps running

        self.height, self.width = self.screen.getmaxyx() # Get the size of the terminal
        self.game = curses.newwin(
            self.height,
            self.width,
            0,
            0
        ) # Create the game window

        # Start the player in the middle of the world
        self.x = self.world_width // 2
        self.y = self.world_height // 2

    def update_camera(self) -> None:
        """Update the camera to follow the player."""
        # Position the camera so the player is in the middle of the screen
        self.camera_x = self.x - self.width // 2
        self.camera_y = self.y - self.height // 2

        # Keep the camera's X position inside the world
        # The camera cannot go below 0 or beyond the world's right edge
        self.camera_x = max(
            0,
            min(self.camera_x, self.world_width - self.width)
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
        self.game.addstr(0, 2, " GAME ") # Add the game title

        # Player coordinates within the screen
        player_x = self.x - self.camera_x
        player_y = self.y - self.camera_y

        # Only draw the player if they are visible in the window
        if 1 <= player_x < self.width - 1:
            if 1 <= player_y < self.height - 1:
                self.game.addstr(player_y, player_x, "@")

        for name, position in self.player_coords.items():
            # Since the player has already been drawn, player_x and player_y are reused for other players
            player_x = position[0] - self.camera_x
            player_y = position[1] - self.camera_y

            if 1 <= player_x < self.width - 1:
                if 1 <= player_y < self.height - 1:
                    self.game.addstr(player_y, player_x, "#")

        for i, chat in enumerate(self.messages): # Use the message index for the y-coordinate
            self.game.addstr(
                i + 1,
                2,
                str(chat)
            ) # FOR TESTING: Display received messages in the game window

        if self.chat_mode:
            self.game.addstr(
                self.height - 2,
                2,
                f"> {self.chat_input}"
            ) # Show the message being typed

        self.game.refresh() # Update the game window

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