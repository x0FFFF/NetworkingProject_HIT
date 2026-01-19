import cmd
import server

class ServerCMD(cmd.Cmd):
    intro = "Welcome to the advanced chat server"
    server = server.Server('127.0.0.1', 5000)

    def do_start(self, arg):
        """
        Starts the server and begins listening on port 5000.
        :param arg:
        :return:
        """
        if not self.server.is_server_running():
            print("Starting server...")
            self.server.start_server()
        else:
            print("Server is already running!")

    def do_stop(self, arg):
        """
        Stops the server
        :param arg:
        :return:
        """
        if self.server.is_server_running():
            print("Stopping server...")
            self.server.stop_server()
        else:
            print("Server is not running!")

    def do_get_connected_clients(self, args):
        print(self.server.get_connected_clients())

if __name__ == "__main__":
    ServerCMD().cmdloop()