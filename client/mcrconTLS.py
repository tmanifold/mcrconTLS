
import socket
import ssl
import struct
import collections
import getpass

# https://docs.python.org/3/library/argparse.html
# https://docs.python.org/3/library/asyncio.html
# https://docs.python.org/3/library/ssl.html
# https://docs.python.org/3/library/struct.html
# https://docs.python.org/3/library/socket.html


class McRconTLS:

    def __init__(self, host, port, password='', verify=0):
        
        self.host = host
        self.port = port
        self.password = password

        self.connect(verify)

    def connect(self, verify_mode):

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile='ssl/serverCert.crt')
        context.load_verify_locations('./ssl/serverCert.crt')
        
        if verify_mode == 0:
            context.verify_mode = ssl.CERT_NONE
        elif verify_mode == 1:
            context.verify_mode = ssl.CERT_OPTIONAL
        elif verify_mode  == 2:
            context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((self.host, self.port)) as sock:
            with context.wrap_socket(sock, server_hostname='ManiteeCraft') as ssock:
                print(f'TLS connection established. {self.host}:{self.port}')

                while (command := self.console()) != 'exit':
                    self.send(ssock, command + '\n')
    
    # construct a packet as a struct and return it
    def mkpacket(self, id, pktype, payload):
        data = struct.pack('<iii', id, pktype, payload.encode()) + b'\x00\x00'
        return struct.pack('<i', len(data)) + data

    def console(self):
         return input('> ')
    
    def send(self, sock, data):
        sock.sendall(data.encode())


if __name__ == '__main__':
    client = McRconTLS('192.168.56.1', 25576, 'Testing123', 2)