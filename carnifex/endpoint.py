from twisted.internet.endpoints import _WrappingFactory
from twisted.internet.base import BaseConnector
from twisted.internet.protocol import ProcessProtocol, connectionDone
from twisted.internet import defer
from twisted.python.failure import Failure


class InductorEndpoint(object):
    """Endpoint that connects to a process spawned by an inductor.
    """
    def __init__(self, inductor, executable, args=(), env={}, path=None,
                 uid=None, gid=None, usePTY=0, childFDs=None, timeout=None):
        self.inductor = inductor
        self.timeout = timeout
        self.inductorArgs = (executable, args, env, path, uid, gid, usePTY, childFDs)

    def connect(self, protocolFactory):
        """Starts a process and connect a protocol to it.
        """
        deferred = self._startProcess()
        deferred.addCallback(self._connectRelay, protocolFactory)
        deferred.addCallback(self._startRelay)
        return deferred

    def _startProcess(self):
        """Use the inductor to start the process we want to relay data from.
        """
        connectedDeferred = defer.Deferred()
        processProtocol = RelayProcessProtocol(connectedDeferred)
        self.inductor.execute(processProtocol, *self.inductorArgs)
        return connectedDeferred

    def _connectRelay(self, process, protocolFactory):
        """Set up and connect the protocol we want to relay to the process.
        This method is automatically called when the process is started,
        and we are ready to relay through it.
        """
        try:
            wf = _WrappingFactory(protocolFactory)
            connector = RelayConnector(process, wf, self.timeout,
                                       self.inductor.reactor)
            connector.connect()
        except:
            return defer.fail()
        # Return a deferred that is called back when the protocol is connected.
        return wf._onConnection

    def _startRelay(self, client):
        """Start relaying data between the process and the protocol.
        This method is called when the protocol is connected.
        """
        process = client.transport.connector.process
        # Relay any buffered data that was received from the process before
        # we got connected and started relaying.
        for _, data in process.data:
            client.dataReceived(data)
        process.protocol = client

        @process._endedDeferred.addBoth
        def stopRelay(reason):
            """Stop relaying data. Called when the process has ended.
            """
            relay = client.transport
            relay.loseConnection(reason)
            connector = relay.connector
            connector.connectionLost(reason)

        # Pass through the client protocol.
        return client


class RelayTransport(object):
    """A protocol transport that relays to another transport.
    """
    connected = False
    disconnected = False

    def __init__(self, connector, reactor):
        self.connector = connector
        reactor.callLater(0, self.connectRelay)

    def connectRelay(self):
        """Builds the target protocol and connects it to the relay transport.
        """
        self.protocol = self.connector.buildProtocol(None)
        self.connected = True
        self.protocol.makeConnection(self)

    def _getTransport(self):
        return getattr(self.connector.proces, 'transport')

    def write(self, data):
        transport = self._getTransport()
        transport.write(data)

    def writeSequence(self, data):
        transport = self._getTransport()
        transport.writeSequence(data)

    def loseConnection(self, reason=connectionDone):
        protocol = getattr(self, 'protocol', None)
        if protocol:
            del self.protocol
            protocol.connectionLost(reason)
        self.disconnected = True

    def failIfNotConnected(self, err):
        if (self.connected or self.disconnected or
            not hasattr(self, "connector")):
            return

        self.connector.connectionFailed(Failure(err))
        del self.connector


class RelayConnector(BaseConnector):
    """Connect a protocol to a relaying transport.
    """
    def __init__(self, process, factory, timeout, reactor):
        if timeout:
            assert not reactor is None, "Need an reactor to use timeout."
        BaseConnector.__init__(self, factory, timeout, reactor)
        self.process = process

    def _makeTransport(self):
        relay = RelayTransport(self, self.reactor)
        self.process.relay = relay
        return relay


class RelayProcessProtocol(ProcessProtocol):
    """A process protocol that relays to a regular protocol.
    """
    def __init__(self, connectedDeferred):
        self._connectedDeferred = connectedDeferred
        self._endedDeferred = defer.Deferred()
        self.data = []

    def connectionMade(self):
        # We're connected to the process, so fire a deferred to connect the
        # target protocol and start relaying.
        self._connectedDeferred.callback(self)

    def childDataReceived(self, childFD, data):
        """Relay data received on any file descriptor to the process
        """
        protocol = getattr(self, 'protocol', None)
        if protocol:
            protocol.dataReceived(data)
        else:
            self.data.append((childFD, data))

    def processEnded(self, reason):
        # The process has ended, so we need to stop relaying.
        self._endedDeferred.callback(reason)
