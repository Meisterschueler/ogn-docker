# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import select
import socket
import sys
import queue
import time
import logging

from aprslib import parse, ParseError
from ognutils import getDDB, listTrackable


class privacyFilter:
    # Check packets from client
    def checkPacket(self, packet):
        if packet.decode('latin-1')[0] == '#':
            # Client Banner
            self.logger.info("FWD:  %s (station status)" % packet.decode('latin-1'))
            return True
        else:
            try:
                parsed = parse(packet)
                if parsed['from'] in self.trackable:
                    self.logger.info("FWD:  %s" % packet.decode('utf-8'))
                    return True
                else:
                    self.logger.info("DROP: %s (noTrack)" % packet.decode('utf-8'))
                    return False
            except ParseError:
                if packet.startswith(b'user'):
                    # Login phrase detected
                    callsign = packet.split(b' ')[1].decode('latin-1')
                    self.logger.info("Detected own callsign: %s" % callsign)
                    self.callsigns.append(callsign)
                    self.trackable.append(callsign)
                    return True
                else:
                    self.logger.info("DROP: %s (invalid packet)" % packet.decode('utf-8'))
                    return False

    # NOTE: Locks EventLoop during execution
    def updateDDB(self):
        self.trackable = listTrackable(getDDB())
        self.trackable.extend(self.callsigns)
        self.logger.info('Updated trackable list, %i entries.' % len(self.trackable))

    def connectToServer(self):
        connected = False
        while not connected:
            try:
                self.server = socket.create_connection(self.server_address, 15)
                connected = True
            except (socket.timeout, ConnectionRefusedError):
                # TODO: catch socket.gaierror
                self.logger.info("Server connect failed for %s:%s, retry..." % self.server_address)
                time.sleep(10)
        self.server.setblocking(0)
        self.logger.info("Connected to server %s:%s" % self.server.getpeername())

    def closeConnection(self, s):
        # No data received, closed connection
        self.inputs.remove(s)
        if s in self.outputs:
            self.outputs.remove(s)
        s.close()

        if s == self.server:
            # Server disconnected
            # TODO: Adjust error message
            self.logger.info("Server disconnected, can't forward packets, try reconnect...")
            del self.server
            self.connectToServer()
            self.inputs.append(self.server)
        else:
            # Client disconnected
            self.logger.info("Client disconnected, wait for reconnect...")
            self.client_connected = False

    def __init__(self, clients_address=('127.0.2.1', 14580), server_address=('aprs-pool.glidernet.org', 14580), ddbInterval=3600):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.clients = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients.setblocking(0)

        self.logger.info('Listen for new client at %s:%s' % clients_address)
        self.clients.bind(clients_address)
        self.clients.listen(1)

        self.interval = ddbInterval
        self.server_address = server_address

        self.callsigns = []

        # APRS Server Properties
        self.newline = b'\r\n'

    def run(self):
        self.connectToServer()

        self.inputs = [self.clients, self.server]
        self.outputs = []
        self.client_connected = False

        # Flow diagram:
        # station --> buf --> checkPacket() --> client_queue --> aprs-server
        # aprs-server --> server_queue --> station

        # Outgoing message queues
        client_queue = queue.Queue()
        server_queue = queue.Queue()

        # Incoming buffer
        buf = b''

        # Timer
        self.updateDDB()
        lasttime = time.time()

        while self.inputs:
            timeout = self.interval + lasttime - time.time()
            if timeout <= 0:
                self.updateDDB()
                lasttime = time.time()
                timeout = self.interval

            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs, timeout)

            if not (readable or writable or exceptional):
                self.updateDDB()
                lasttime = time.time()
                continue

            for s in readable:
                if s is self.clients:
                    if not self.client_connected:
                        # Accept new client connection
                        connection, client_address = s.accept()
                        connection.setblocking(0)
                        self.inputs.append(connection)
                        self.client = connection
                        self.client_connected = True
                        self.logger.info("New client at %s:%s" % client_address)
                        # TODO: Flush buffers, reconnect to server (to get a fresh banner)
                        self.closeConnection(self.server)
                    else:
                        # Refuse new client connection
                        # NOTE: Its not possible to directly refuse the connection
                        #       http://stackoverflow.com/questions/19214552/python-socket-server-reject-connection-from-address
                        connection, client_address = s.accept()
                        connection.close()
                        self.logger.info("Refuse new connection: A client is already connected.")
                else:
                    data = s.recv(1024)
                    self.logger.debug("RECV: %s (port %s)" % (data.rstrip().decode('utf-8'), s.getpeername()[1]))
                    if data:
                        # Received data
                        if s == self.server:
                            # from Server
                            server_queue.put(data)
                            if self.client_connected and self.client not in self.outputs:
                                self.outputs.append(self.client)
                        else:
                            # from Client
                            buf += data
                            if self.newline in buf:
                                lines = buf.split(self.newline)
                                buf = lines[-1]
                                for line in lines[:-1]:
                                    if self.checkPacket(line):
                                        client_queue.put(line + self.newline)
                            if self.server not in self.outputs:
                                self.outputs.append(self.server)
                    else:
                        # Received no data, close connection
                        self.closeConnection(s)

            # Handle Outputs
            for s in writable:
                if s == self.server:
                    # to Server
                    try:
                        next_msg = client_queue.get_nowait()
                    except queue.Empty:
                        self.outputs.remove(s)
                    else:
                        s.send(next_msg)
                        self.logger.debug("SEND: %s (port %s)" % (next_msg.rstrip().decode('utf-8'), s.getpeername()[1],))
                else:
                    # to Client
                    try:
                        next_msg = server_queue.get_nowait()
                    except queue.Empty:
                        self.outputs.remove(s)
                    else:
                        s.send(next_msg)
                        self.logger.debug("SEND: %s (port %s)" % (next_msg.rstrip().decode('utf-8'), s.getpeername()[1],))

            # Handle exceptional conditions
            for s in exceptional:
                self.closeConnection(s)


if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(levelname)-5s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    f = privacyFilter()
    f.run()
