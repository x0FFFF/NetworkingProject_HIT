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
            try:
                # This blocks until a client connects OR the socket is closed
                conn, addr = self.socket.accept()

                if not self.is_running:
                    conn.close()
                    break

                print("New client connected from", addr)
                thread = threading.Thread(target=self._handle_client, args=(conn,))
                thread.start()

            except OSError:
                # This exception is expected when stop_server() calls self.socket.close()
                if not self.is_running:
                    print("Server socket closed. Stopping listener thread.")
                else:
                    print("Unexpected socket error occurred.")
                break



    def _assign_user(self, username, conn):
        if username in self.client_connections:
            # username already taken
            self._send_error_to_client("Username already taken. Please choose another.", conn)
            return False
        self.client_connections[username] = conn
        print(f"{username} has connected.")
        return True

    def _disconnect_user(self, username):
        del self.client_connections[username]
        print(f"{username} has disconnected.")

    #runs as a thread
    def _handle_client(self, conn):
        current_user = None

        try:
            username_valid = False
            while not username_valid:
                # waiting for client to send its username as first message
                data = conn.recv(1024)
                if not data:
                    conn.close()
                    return

                current_user = data.decode().strip()
                username_valid = self._assign_user(current_user, conn)


            # handle messages from client
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    self._handle_action_from_client(data)

                except (ConnectionResetError, BrokenPipeError):
                    break
                except Exception as e:
                    print(f"Error handling message from {current_user}: {e}")
        finally:
            if current_user:
                self._disconnect_user(current_user)
            else:
                conn.close()


    #checks active users and send them to _send_messages
    def _send_active_users_to_client(self, json_data):
        source_user = json_data.get("SrcUser")

        if source_user not in self.client_connections:
            print(f"Error: User {source_user} not found in active connections")
            return

        response = {
        "Action": "UserList",
        "Content": list(self.client_connections.keys())
        }

        json_payload = json.dumps(response)

        self._send_message_to_client(json_payload, source_user)



    # handles action messages sent by the client
    def _handle_action_from_client(self, data):
        json_data = json.loads(data.decode())

        match json_data:
            case {"Action" : "GetActiveUsers"}:
                self._send_active_users_to_client(json_data)
            case {"Action" : "SendMessage"}:
                self._handle_client2client_message(json_data)
            # start chat
            # stop chat


    """
    {"Action":"GetActiveUsers | SendMessage", "SrcUser" : "user", "DestUser" : "user", "Content" : "content"}
    """


    # handles client-to-client message
    def _handle_client2client_message(self, json_data):
        parsed = self._parse_for_message(json_data)
        if not parsed:
            # error logging handled by the message parser
            # also sends message to client about the message failing to arrive
            return

        source_user, target_user, msg = parsed

        output_dict = {
            "Action" : "Message",
            "SrcUser" : source_user,
            "Content" : msg
        }

        json_data = json.dumps(output_dict)
        success = self._send_message_to_client(json_data, target_user)
        if not success:
            self._send_error_to_client("Message delivery failed.", source_user)


    # send error to a specific client
    def _send_error_to_client(self, error, target_user):
        error_dict = {
            "Action" : "Error",
            "Content" : error
        }
        self._send_message_to_client(json.dumps(error_dict), target_user)


    # send any message to a specific client
    def _send_message_to_client(self, json_data, target_user):

        if isinstance(target_user, str): # check if target_user is the username
            target_conn = self.client_connections.get(target_user)
        else:
            target_conn = target_user # assume target_user is already a connection object

        if not target_conn:
            print(f"Failed to send message to {target_user} - user isn't online")
            return False

        try:
            target_conn.sendall(json_data.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Failed to send message to {target_user}: {e}")
            if isinstance(target_user, str):
                self._disconnect_user(target_user)
            else:
                target_conn.close()
            return False



    def _parse_for_message(self, json_data):
        match json_data:
            case {"SrcUser" : source_user, "DestUser" : target_user, "Content" : msg}:
                if not source_user in self.client_connections:
                    print(f"Server Error: {source_user} not found.")
                    return None

                if not target_user in self.client_connections:
                    # Send message to client that user doesn't exist
                    print(f"Routing Error: {target_user} is offline.")
                    self._send_error_to_client(f"User {target_user} is offline.", source_user)
                    return None

                if not msg.strip():
                    print("Ignored empty message")
                    self._send_error_to_client("Cannot send empty message.", source_user)
                    return None

                return source_user, target_user, msg

            case _:
                print(f"Missing data in message parsing: {json_data}")
                return None
