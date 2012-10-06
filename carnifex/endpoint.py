from twisted.internet.endpoints import _WrappingFactory
from twisted.internet.base import BaseConnector
from twisted.internet.protocol import ProcessProtocol, connectionDone


class InductorEndpoint(object):
    """Endpoint that connects to a process spawned by an inductor.
    """
    def __init__(self, inductor, executable, args, timeout=None, reactor=None):
        self._inductor = inductor
        self._executable = executable
        self._args = args
        self._timeout = timeout
        self._reactor = reactor

    def connect(self, protocolFactory):
        relay = RelayTransport()
        wf = _WrappingFactory(protocolFactory)
        connector = RelayConnector(relay, wf, self._timeout, self._reactor)
        processProtocol = _RelayTransportProcessProtocol(relay, connector)
        _process = self._inductor.execute(processProtocol, self._executable, self._args)
        return wf._onConnection


class RelayTransport(object):
    """A protocol transport that relays to another transport.
    """
    connected = False
    disconnected = False

    def __init__(self, data=None):
        self.data = data or []

    def start(self, transport):
        self.transport = transport
        self.write = transport.write
        self.writeSequence = transport.writeSequence
        self.connected = True

    def loseConnection(self, reason=connectionDone):
        protocol = self.protocol
        del self.protocol
        protocol.connectionLost(reason)
        self.transport.loseConnection()
        self.disconnected = True

    def relayData(self, data):
        if hasattr(self, 'protocol'):
            self.protocol.dataReceived(data)
        else:
            self.data.append(data)

    def failIfNotConnected(self, err):
        if (self.connected or self.disconnected or
            not hasattr(self, "connector")):
            return


class RelayConnector(BaseConnector):
    """Connect a protocol to a relaying transport.
    """
    def __init__(self, relay, factory, timeout, reactor):
        if timeout:
            assert not reactor is None, "Need an reactor to use timeout."
        BaseConnector.__init__(self, factory, timeout, reactor)
        self.relay = relay
        relay.connector = self

    def _makeTransport(self):
        protocol = self.buildProtocol(None)
        self.relay.protocol = protocol
        protocol.makeConnection(self.relay)
        return self.relay

    def cancelTimeout(self):
        BaseConnector.cancelTimeout(self)


class _RelayTransportProcessProtocol(ProcessProtocol):
    """A process protocol that relays to a regular protocol.
    """
    def __init__(self, relay, connector):
        self.relay = relay
        self.connector = connector

    def connectionMade(self):
        self.relay.start(self.transport)
        self.connector.connect()

    def childDataReceived(self, childFD, data):
        """Relay data received on any file descriptor to the process
        """
        #TODO: we might want to enable configuration of which fds to relay.
        self.relay.relayData(data)

    def processEnded(self, reason):
        self.relay.loseConnection(reason)
        self.connector.connectionLost(reason)
