# mcrconTLS.py

import asyncio
import subprocess
import threading
import socket
import ssl

class mcrconTLS:
    '''A wrapper for minecraft server that supports RCON over TLS.'''

    RCON_PORT = 25576 # default port number is 25575. Using 25576 for encrypted comms

    def __init__(self):
        print("Initialized mcrconTLS")

        
        asyncio.run(self.start_rcon_server())

        asyncio.run(self.start_minecraft('java -jar ./minecraft_server.jar nogui'))
    
    async def start_minecraft(self, command):

        print('Booting up minecraft server...')

        self.server = await asyncio.create_subprocess_shell(command,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)

        await asyncio.gather(
            self.read(self.server.stdout),
            self.write(self.server.stdin)
        )
    
    async def start_rcon_server(self):
        t_rcon = threading.Thread(target=self.rcon_server, name="RCONServer")
        t_rcon.start()

    def rcon_server(self):
        print('Opening TLS encrypted channel')
        # https://docs.python.org/3/library/ssl.html
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
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

                    try:
                        while (data := conn.recv(1024)):
                            self.server.stdin.write(data)
                    except ConnectionResetError:
                        print(f'[{addr}] connection closed by client.')

            
                    print(data.decode())
                print(f'RCON Connection to {IP} closed.')

    async def read(self, stream):
        # will need to modify this to send to client
        while True:
            buffer = await stream.readline()
            if not buffer:
                break
            
            print(f'[stdout] ' + buffer.decode(), end='')
    
    async def write(self, stream):
        # do stuff when a request is received here
        print('in write')

if __name__ == "__main__":
    #print(mcrconTLS.__doc__)

    mcrconTLS()

    