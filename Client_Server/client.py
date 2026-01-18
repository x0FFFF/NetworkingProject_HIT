import json
import socket

class Client:
    def __init__(self):
        # stores usernames of open chats
        self.open_chats = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # indicates if user is connected to the server
        self.is_connected = False
        # current users name
        self.username = None

    def connect(self, host, port, username):
        """
        Connects to a server with provided username
        :param host: server's ip address
        :param port: server's port
        :param username: username
        :return:
        """
        self.username = username

        if not self.is_connected:
            self.socket.connect((host, port))

    def disconnect(self):
        """
        Disconnects from server
        :return:
        """
        if self.is_connected:
            self.socket.close()

    def send_msg_to_chat(self, message, dst_user):
        """
        Sends message to specified user
        :param message:
        :param dst_user:
        :return:
        """
        packet = {"Action" : "SendMessage", "SrcUser" : self.username, "DestUser" : dst_user, "Content" : message}
        self.socket.send(json.dumps(packet).encode())

    def listen(self):
        while self.is_connected:
            data = self.socket.recv(1024)