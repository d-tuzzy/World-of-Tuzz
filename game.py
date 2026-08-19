import curses
import socket


ip = input("IP: ")

def main(screen):
    client = socket.socket()
    client.connect((ip, 5000))

    x = 0
    y = 0

    while True:
        screen.clear()
        screen.addstr(y, x, "@")
        screen.refresh()

        key = screen.getch()

        if key == 27: # Escape key
            client.send(b"ESC")
            break

        elif key == curses.KEY_UP:
            y -= 1
            client.send(b"UP")

        elif key == curses.KEY_DOWN:
            y += 1
            client.send(b"DOWN")

        elif key == curses.KEY_LEFT:
            x -= 1
            client.send(b"LEFT")

        elif key == curses.KEY_RIGHT:
            x += 1
            client.send(b"RIGHT")

    client.close()

curses.wrapper(main)