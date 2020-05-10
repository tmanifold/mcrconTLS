
import socket
import ssl
import struct
import collections
import getpass

class McRconTLS:

    # send
    # recv
    # encode
    # decode
    # connect
    # disconnect

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
                print(f'TLS connection established. {self.host}:{self.port}, {ssock.getpeercert()}')
                print(ssock.version)


if __name__ == '__main__':
    client = McRconTLS('192.168.56.1', 25576, 'Testing123', 1)