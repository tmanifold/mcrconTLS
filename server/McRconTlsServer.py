# mcrconTLS.py

import subprocess
import threading
import socket
import ssl
import queue
import re
import sys

from mcrconTLS import *

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

        IP = socket.gethostbyname(socket.gethostname())

        ssock = context.wrap_socket(
            socket.create_server((IP, self.RCON_PORT)),
            server_side=True
        )

        if (ssock):
            # IP = socket.gethostbyname(socket.gethostname())
            # sock.bind((IP, self.RCON_PORT))
            print(f'Listening for RCON connections on {IP}:{self.RCON_PORT}')
            # sock.listen()
            while True:
        #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        #         IP = socket.gethostbyname(socket.gethostname())
        #         sock.bind((IP, self.RCON_PORT))
        #         print(f'Listening for RCON connections on {IP}:{self.RCON_PORT}')
        #         sock.listen()

        #         with context.wrap_socket(sock, server_side=True) as ssock:
                conn, addr = ssock.accept()
                print (f'TLS connection from {addr}')

                rcon = McRconTLS(addr[0], addr[1])

                self.connections.append((rcon, conn))

                # start a thread with a new rcon session.
                threading.Thread(target=self.rcon_session, args=(rcon, conn), daemon=True).start()
    
    # begin a session with the given rcon object on the specified connection
    def rcon_session(self, rcon, conn):
        '''Start threads for sending to and receiving from client'''
        threading.Thread(target=self.rcon_session_recv, args=(rcon, conn)).start()
        threading.Thread(target=self.rcon_session_send, args=(rcon, conn), daemon=True).start()

    def rcon_session_recv(self, rcon, conn):
        '''Routine to recieve incoming messages from a client'''
        try:
            while conn and self.minecraft.poll() == None:
                p, size = rcon.packet_recv(conn)
                #print(f'{p.id}, {p.ptype}, {p.payload.decode()}')
                if size > 14:
                    with self.command_queue_condition:
                        self.command_queue.put(p.payload.decode())
                        #print(f'[{__name__}] put {p.payload} in queue')

                        self.command_queue_condition.notifyAll()
            print(f'RCON Connection to {rcon.host}:{rcon.port} closed.')
        except ConnectionResetError:
            print(f'[{rcon.host}:{rcon.port}] connection closed by client.')


    def rcon_session_send(self, rcon, conn):
        '''Routine to send the server stdout to the client'''
        try:
            while conn and self.minecraft.poll() == None:
                rcon.packet_send(
                    conn,
                    Packet(REQUEST_ID.MESSAGE, Packet.TYPE.MULTI, self.minecraft.stdout.readline().encode())
                )
        except ConnectionResetError:
            print(f'[{rcon.host}:{rcon.port}] connection closed by client.')

    def start(self):
        self.start_minecraft('java -jar ./minecraft_server.jar nogui')

  
    def start_minecraft(self, command):
        '''Start the Minecraft server a subprocess, then start rcon threads'''
        print(command)

        self.minecraft = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE,
                                    text=True)

        self.start_rcon_server()

        threading.Thread(target=self.read_stdout, daemon=True).start()

    def start_rcon_server(self):
            '''Starts the main RCON server thread, as well as the thread that writes to the RCON command queue'''
            threading.Thread(target=self.rcon_server, name="RCONServer").start()
            threading.Thread(target=self.rcon_queueWriter, name='rcon_queueWriter', daemon=True).start()


if __name__ == "__main__":
    #print(mcrconTLS.__doc__)

    server = MCRCONTLSServer()
    server.start()

    