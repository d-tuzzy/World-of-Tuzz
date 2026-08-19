import socket

ip = input("IP: ")

client = socket.socket()
client.connect((ip, 5000))

client.send(b"hello")