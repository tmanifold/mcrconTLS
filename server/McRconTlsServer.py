# mcrconTLS.py

import subprocess
import threading
import socket
import ssl
import queue
import re
import sys

from mcrconTLS import McRconTLS, Packet

class MCRCONTLSServer:
    '''A wrapper for minecraft server that supports RCON over TLS.'''

    connections = []
    command_queue = queue.Queue()
    command_queue_condition = threading.Condition()

    RCON_PORT = 25576 # default port number is 25575. Using 25576 for encrypted comms

    CERT = './ssl/serverCert.crt'
    KEY  = './ssl/serverKey.key'

    def __init__(self, cert=None, key=None):
        print("Initialized mcrconTLS")

        if cert:
            self.CERT = cert
        
        if key:
            self.KEY = key
    
    # def send_response(self):
    #     '''Send server response and send it to the client'''

    def read_stdout(self):
        while True:
            out = self.minecraft.stdout.readline()
            if out:
                print(f'[stdout]' + out, end='')

    def rcon_queueWriter(self):
        while self.minecraft.poll() == None:

            with self.command_queue_condition:

                while self.command_queue.empty():
                    self.command_queue_condition.wait()

                cmd = self.command_queue.get()
                #print(f'[{__name__}] writing {cmd} to mcstdin -> {cmd.encode()}')
                
                print(cmd, file=self.minecraft.stdin)
                #self.minecraft.stdin.write(cmd.encode())
                self.minecraft.stdin.flush()
                
    def rcon_server(self):
        print('Opening TLS encrypted channel')
        # https://docs.python.org/3/library/ssl.html
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(certfile='./ssl/serverCert.crt', keyfile='./ssl/serverKey.key') # REPLACE WITH VALID CERT SIGNED BY CA

        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
                IP = socket.gethostbyname(socket.gethostname())
                sock.bind((IP, self.RCON_PORT))
                print(f'Listening for RCON connections on {IP}:{self.RCON_PORT}')
                sock.listen()

                with context.wrap_socket(sock, server_side=True) as ssock:
                    conn, addr = ssock.accept()
                    print (f'TLS connection from {addr}')

                    rcon = McRconTLS(addr[0], addr[1])

                    try:
                            while self.minecraft.poll() == None:
                                p, size = rcon.packet_recv(conn)
                                #print(f'{p.id}, {p.ptype}, {p.payload.decode()}')
                                if size > 14:
                                    with self.command_queue_condition:
                                        self.command_queue.put(p.payload.decode())
                                        #print(f'[{__name__}] put {p.payload} in queue')

                                        self.command_queue_condition.notifyAll()
                                
                        
                    except ConnectionResetError:
                        print(f'[{addr}] connection closed by client.')

            print(f'RCON Connection to {IP} closed.')

    def start(self):
        self.start_minecraft('java -jar ./minecraft_server.jar nogui')

  
    def start_minecraft(self, command):

        print(command)

        self.minecraft = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE,
                                    text=True)

        self.start_rcon_server()

        threading.Thread(target=self.read_stdout, daemon=True).start()

        #rcon_started = False

        # while self.minecraft.poll() == None:
        #     out = self.minecraft.stdout.readline().decode()

        #     # if not rcon_started:
        #     #     match = re.match('Done \([0-9]+\.[0-9]+s\)', out)
        #     #     print(f'match={match}')
        #     #     if match:
        #     #         rcon_started = True
        #     #         threading.Thread(target=self.start_rcon_server)

        #     if out:
        #         print(f'[stdout] ' + out, end='')

    def start_rcon_server(self):
            threading.Thread(target=self.rcon_server, name="RCONServer").start()
            threading.Thread(target=self.rcon_queueWriter, name='rcon_queueWriter', daemon=True).start()


if __name__ == "__main__":
    #print(mcrconTLS.__doc__)

    server = MCRCONTLSServer()
    server.start()

    