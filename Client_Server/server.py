import socket
import threading
import json

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = False
        self.listening_thread = None
        self.MAX_CLIENTS = 5

        # stores the chats between clients
        self.active_chats = {}

        # stores the connection objects per connected client
        self.client_connections = {}

        # stores the active threads
        # self.thread_pool = []
    def is_server_running(self):
        return self.is_running

    def start_server(self):
        if self.is_running:
            print("Server is already running.")
            return

        self.is_running = True
        self._bind_addr()
        self.listening_thread = threading.Thread(target=self._listen_for_clients)
        self.listening_thread.start()

    def stop_server(self):
        if not self.is_running:
            print("Server is not running.")
            return

        self.is_running = False
        self.socket.close()
        self.listening_thread.join()

    def get_connected_clients(self):
        return self.client_connections.keys()

    def _bind_addr(self):
        self.socket.bind((self.host, self.port))

    # runs as a thread
    def _listen_for_clients(self):
        self.socket.listen(self.MAX_CLIENTS)
        print("Server is listening for new clients.")

        while self.is_running:
            # listening for any client to connect
            conn, addr = self.socket.accept()
            print("New client connected from", addr)
            thread = threading.Thread(target=self._handle_client, args=(conn,))
            thread.start()
            # self.thread_pool.append(thread)

    def _assign_user(self, username, conn):
        self.active_chats[username] = []
        self.client_connections[username] = conn

    def _disconnect_user(self, username):
        del self.client_connections[username]
        del self.active_chats[username]
        print(f"{username} has disconnected.")

    #runs as a thread
    def _handle_client(self, conn):
        current_user = None
        data = None

        # waiting for client to send its username as first message
        data = conn.recv(1024)
        if not data:
            conn.close()
            return

        current_user = data.decode()
        self._assign_user(current_user, conn)

        while True:
            data = conn.recv(1024)

            if not data:
                # handle user disconnection
                self._disconnect_user(current_user)
                return

            self._handle_action_from_client(data)



    def _handle_action_from_client(self, data):
        json_data = json.loads(data.decode())

        match json_data:
            case {"Action" : "GetActiveUsers"}:
                pass
            case {"Action" : "SendMessage"}:
                self._send_message(json_data)
            # start chat
            # stop chat




    """
    {"Action":"GetActiveUsers | StartChat | StopChat | SendMessage", "SrcUser" : "user", "DestUser" : "user", "Content" : "content"}
    """

    # handles another client-to-client message
    def _send_message(self, json_data):
        parsed = self._parse_for_message(json_data)
        if not parsed:
            # error logging handled by the message parser
            return

        source_user, target_user, msg = parsed

        output_dict = {
            "SrcUser" : source_user,
            "Msg" : msg
        }

        try:
            encoded_data = json.dumps(output_dict).encode('utf-8')

            target_conn = self.client_connections[target_user]
            target_conn.sendall(encoded_data)
        except Exception as e:
            print(f"Failed to send message to {target_user}: {e}")
            self._disconnect_user(target_user)


    def _parse_for_message(self, json_data):
        match json_data:
            case {"SrcUser" : source_user, "DestUser" : target_user, "Content" : msg}:
                if not source_user in self.client_connections:
                    print(f"Server Error: {source_user} not found.")
                    return None

                if not target_user in self.client_connections:
                    # Send message to client that user doesn't exist
                    print(f"Routing Error: {target_user} is offline.")
                    return None

                if not msg.strip():
                    print("Ignored empty message")
                    return None

                return source_user, target_user, msg

            case _:
                print(f"Missing data in message parsing: {json_data}")
                return None
