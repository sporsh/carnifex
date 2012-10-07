from twisted.internet.endpoints import _WrappingFactory
from twisted.internet.base import BaseConnector
from twisted.internet.protocol import ProcessProtocol, connectionDone
from twisted.internet import defer
from twisted.python.failure import Failure


class InductorEndpoint(object):
    """Endpoint that connects to a process spawned by an inductor.
    """
    def __init__(self, inductor, executable, args, reactor, timeout=None):
        self._inductor = inductor
        self._executable = executable
        self._args = args
        self._timeout = timeout
        self._reactor = reactor

    def connect(self, protocolFactory):
        deferred = self._startProcess()
        deferred.addCallback(self._connectRelay, protocolFactory)
        deferred.addCallback(self._startRelay)
        return deferred

    def _startProcess(self):
        connectedDeferred = defer.Deferred()
        processProtocol = RelayProcessProtocol(connectedDeferred)
        self._inductor.execute(processProtocol, self._executable, self._args)
        return connectedDeferred

    def _connectRelay(self, process, protocolFactory):
        # We're the process transport is open, so start the connection.
        try:
            wf = _WrappingFactory(protocolFactory)
            connector = RelayConnector(process, wf, self._timeout, self._reactor)
            connector.connect()
        except:
            return defer.fail()
        return wf._onConnection

    def _startRelay(self, client):
        pp = client.transport.connector.process
        for _, data in pp.data:
            client.dataReceived(data)
        pp.protocol = client

        @pp._endedDeferred.addBoth
        def stopRelay(reason):
            relay = client.transport
            connector = relay.connector
            relay.loseConnection(reason)
            connector.connectionLost(reason)

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
        print "FAIL IF NOT CONN"
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
        print "MAKE TRANSPORT"
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
        """""Process has started and we are ready to relay to the protocol.
        """
        # Connection to the process is made, so callback to start relaying.
        self._connectedDeferred.callback(self)

    def childDataReceived(self, childFD, data):
        """Relay data received on any file descriptor to the process
        """
        #TODO: we might want to enable configuration of which fds to relay.
        protocol = getattr(self, 'protocol', None)
        if protocol:
            protocol.dataReceived(data)
        else:
            self.data.append((childFD, data))

    def processEnded(self, reason):
        # The process has ended, so we need to stop relaying.
        self._endedDeferred.callback(reason)
