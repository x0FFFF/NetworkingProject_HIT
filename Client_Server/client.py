import json
import socket
import threading


class Client:
    def __init__(self):
        # stores usernames of open chats
        self.open_chats = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # indicates if user is connected to the server
        self.is_connected = False
        # current users name
        self.username = None
        self.listen_thread = None

    def connect(self, host, port, username):
        """
        Connects to a server with provided username
        :param host: server's ip address
        :param port: server's port
        :param username: username
        :return:
        """
        self.username = username

        if self.is_connected:
            print("Connection already established")
            return
        try:
            self.socket.connect((host, port))
            self.is_connected = True
        except socket.error:
            print("Could not connect to server")
            return

        print("Connected to server")
        self.socket.sendall(username.encode())
        self.listen_thread = threading.Thread(target=self.listen_for_messages)
        self.listen_thread.start()

    def disconnect(self):
        """
        Disconnects from server
        :return:
        """
        if not self.is_connected:
            print("Disconnected")
            return

        self.is_connected = False
        self.socket.close()
        self.listen_thread.join()


    def send_msg_to_chat(self, message, dst_user):
        """
        Sends message to specified user
        :param message:
        :param dst_user:
        :return:
        """
        if not self.is_connected:
            print("Not connected")
            return
        packet = {"Action" : "SendMessage", "SrcUser" : self.username, "DestUser" : dst_user, "Content" : message}
        self.socket.sendall(json.dumps(packet).encode())

    def get_active_users(self):
        """
        Sends a request for active users
        :return:
        """
        if not self.is_connected:
            print("Not connected")
            return
        packet = {"Action" : "GetActiveUsers", "SrcUser" : self.username}

        self.socket.sendall(json.dumps(packet).encode())

    def listen_for_messages(self):
        """
        Listens for incoming communication from the server
        :return:
        """
        while self.is_connected:
            data = self.socket.recv(1024)

            message_handlers = {
                "Error" : self._handle_error_message,
                "Message" : self._handle_user_message,
                "UserList" : self._handle_active_users
            }

            if not data:
                print("An error occurred")
                self.disconnect()
                return

            data = json.loads(data.decode())

            message_handlers[data["Action"]](data)

    @staticmethod
    def _handle_error_message(data):
        print("An error occurred: " + data["Content"])

    @staticmethod
    def _handle_user_message(data):
        print("From %s: %s" % (data["SrcUser"], data["Content"]))

    @staticmethod
    def _handle_active_users(data):
        for user in data["Content"]:
            print(user)