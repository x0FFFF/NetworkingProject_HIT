import client
import cmd

class ClientCLI(cmd.Cmd):
    intro = "Welcome to the Client CLI. Type help or ? to list commands."
    prompt = "> "

    def __init__(self):
        super().__init__()
        self.client = client.Client()
        self.active_chat = None

    def do_connect(self, args):
        """
        Connects to server
        :param args: either (host, port, username) or just username, in case no host and port provided connects to the default server
        :return:
        """
        args = args.split(" ")
        if len(args) == 1:
            self.client.connect('127.0.0.1', 5000, args[0])

        elif len(args) == 3:
            self.client.connect(args[0], args[1], args[2])

        else:
            print("Not enough arguments, provide Username")

    def do_disconnect(self, args):
        self.client.disconnect()

    def do_online(self, args):
        self.client.get_active_users()

    def do_to(self, args):
        self.active_chat = args

    def default(self, line):
        if not self.active_chat:
            print("No active chat")
            return
        self.client.send_msg_to_chat(line, self.active_chat)


if __name__ == "__main__":
    ClientCLI().cmdloop()