import socket
import cmd

class ServerCLI(cmd.Cmd):
    prompt = 'Server> '
    intro = "Starting up..."

    def __init__(self):
        super().__init__()

    def do_quit(self, line) -> bool:
        """Quit the server"""
        print("Closing server...")
        return True


def main():
    ServerCLI().cmdloop()


if __name__ == '__main__':
    main()