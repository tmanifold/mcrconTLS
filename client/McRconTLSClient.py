
# McRconTLS client

import ssl
from mcrconTLS import McRconTLS

if __name__ == '__main__':
    client = McRconTLS('192.168.56.1', 25576, 'Testing123')

    client.connect(ssl.Purpose.SERVER_AUTH, 0)
