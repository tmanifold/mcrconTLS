
# Implementation of Minecraft RCON supporting TLS
# Based on barneygale's implementation: https://github.com/barneygale/MCRcon/blob/master/mcrcon.py

import socket
import ssl
import struct
from collections import namedtuple


# https://docs.python.org/3/library/argparse.html
# https://docs.python.org/3/library/asyncio.html
# https://docs.python.org/3/library/ssl.html
# https://docs.python.org/3/library/struct.html
# https://docs.python.org/3/library/socket.html


class IncompletePacketException(Exception):
    '''RCON packet is not formatted correctly'''
    def __init__(self, m):
        self.minimum = m
    pass

class REQUEST_ID:
    MESSAGE     = 0
    END_MESSAGE = 1

class Packet:
    '''
    A symple RCON packet
    Specification: https://wiki.vg/RCON
    '''
    class TYPE:
        LOGIN   = 3
        COMMAND = 2
        MULTI   = 0

    def __init__(self, id, ptype, payload=b''):
        self.id = id
        self.ptype = ptype
        self.payload = payload

class McRconTLS:
    '''Communicate via RCON over TLS'''
    def __init__(self, host, port, password=''):
        
        # if mode == 0:
        #     self.init_client()
        # else:
        #     self.init_server()

        self.host = host
        self.port = port
        self.password = password

    def connect(self, purpose, verify_mode):
        '''Attempt to establish a secured connection to the server'''

        context = ssl.create_default_context(purpose, cafile='ssl/serverCert.crt')
        context.load_verify_locations('./ssl/serverCert.crt')
        context.check_hostname = False
        
        if verify_mode == 0:
            context.verify_mode = ssl.CERT_NONE
        elif verify_mode == 1:
            context.verify_mode = ssl.CERT_OPTIONAL
        elif verify_mode  == 2:
            context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((self.host, self.port)) as sock:
            with context.wrap_socket(sock) as ssock:
                print(f'TLS connection established. {self.host}:{self.port}')

                # Enter login credentials
                # if self.login():

                try :
                    while (command := self.console()) != 'exit':
                        # send the command packet
                        self.packet_send(
                            ssock,
                            Packet(REQUEST_ID.MESSAGE, Packet.TYPE.COMMAND, command.encode())
                        )
                        # send message-terminating packet
                        self.packet_send(
                            ssock,
                            Packet(REQUEST_ID.END_MESSAGE,Packet.TYPE.COMMAND)
                        )
                except ConnectionResetError:
                    print('Server closed the connection')
    
    def console(self):
        '''Simple prompt for user input'''
        return input('> ')
    
    # construct a packet as a struct and return it
    def packet_encode(self, packet):
        '''Encode an RCON packet'''

        data = struct.pack('<ii', packet.id, packet.ptype) + packet.payload + b'\x00\x00'
        return struct.pack('<i', len(data)) + data
    
    def packet_decode(self, data):
        '''Decode an RCON packet'''

        if len(data) < 14:
            # minimum packet size (empty payload) is 14 bytes
            raise IncompletePacketException(14)

        pklen = struct.unpack('<i', data[0:4])[0]+4
        #print(f'pklen={pklen}')

        if len(data) < pklen:
            # received less data than the packet header states
            raise IncompletePacketException(pklen)
        
        pkid, pktype = struct.unpack('<ii', data[4:12])
        payload = data[12:pklen-2]
        padding = data[pklen-2:]
        
        #print(f'Packet: {pklen}, {pkid}, {pktype}, {payload}, {padding}')
        
        assert padding == b'\x00\x00'

        return Packet(pkid, pktype, payload)
    
    def packet_recv(self, sock):
        '''Receive packets from the given socket. Returns a Packet object'''

        data  = b''

        while True:
            try:
                return self.packet_decode(data), len(data)
            except IncompletePacketException as e:
                while len(data) < e.minimum:
                    data += sock.recv(e.minimum - len(data))
        # data = sock.recv(4096)
        # print(f'data={data}')

        # return self.decode(data)


    def packet_send(self, sock, packet):
        '''Send the packet over the given socket.'''

        enc = self.packet_encode(packet)
        sock.sendall(enc)
