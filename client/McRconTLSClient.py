
# McRconTLS client

import ssl, socket
import threading
from mcrconTLS import *

class MCRCONTLSClient:

    host = None
    port = None
    client = None


    def __init__(self, host='localhost', port='25575'):
        self.host = host
        self.port = port

    def login(self, password=''):
        self.client = McRconTLS(self.host, self.port, password='')

        return True

    def command_send(self, ssock, cmd):
        self.client.packet_send(
            ssock,
            Packet(REQUEST_ID.MESSAGE, Packet.TYPE.COMMAND, cmd.encode())
        )
        # send message-terminating packet
        self.client.packet_send(
            ssock,
            Packet(REQUEST_ID.END_MESSAGE,Packet.TYPE.COMMAND)
        )

    def connect(self,verify_mode):
        '''Attempt to establish a secured connection to the server'''

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile='ssl/serverCert.crt')
        context.load_verify_locations('./ssl/serverCert.crt')
        context.check_hostname = False
        
        if verify_mode == 0:
            context.verify_mode = ssl.CERT_NONE
        elif verify_mode == 1:
            context.verify_mode = ssl.CERT_OPTIONAL
        elif verify_mode  == 2:
            context.verify_mode = ssl.CERT_REQUIRED


        try:
            ssock = context.wrap_socket(socket.create_connection((self.host, self.port)))

            # Enter login credentials
            if (ssock):
                if self.login():
                    print(f'logged into server. {self.host}:{self.port}')
                else:
                    return

                    # start a thread to receive output from the server
                    threading.Thread(target=self.receive_server_output, args=(ssock,), daemon=True)

            # with socket.create_connection((self.host, self.port)) as sock:
            #     with context.wrap_socket(sock) as ssock:
            while (ssock):
                if (command := input('> ')) != 'exit':
                    # send the command packet
                    self.command_send(ssock, command)

        except ConnectionResetError:
            print('Server closed the connection')
        except ConnectionAbortedError:
            print('Connection was aborted by the server')
        except ConnectionRefusedError:
            print('Connection was refused by the server.')

    def receive_server_output(self, ssock):
        while ssock:
            data, size = self.client.packet_recv()
            if size > 14:
                print(f'{data}\n')


if __name__ == '__main__':
    client = MCRCONTLSClient('192.168.56.1', 25576)

    client.connect(verify_mode=0)
