from server import Server
from server_ui import ServerUI


server = Server()
server_ui = ServerUI(server)
server_ui.start()