from twisted.trial.unittest import TestCase
from carnifex.inductor import ProcessInductor
from carnifex.localprocess import ReactorProcessFactory
from twisted.internet.error import ConnectionDone
from twisted.internet import protocol, defer
from carnifex.endpoint import InductorEndpoint


class MockProcess(object):
    def write(self, data):
        pass

    def writeSequence(self, sequence):
        pass

    def loseConnection(self):
        pass



class InductorEndpointTest(TestCase):
    """Test connecting a twisted protocol to a process.
    """

    def test_endpoint(self):
        relay_data = ['command output', 'info message']
        inductor = MockProcessInductor(fauxProcessData)
        #TODO: fix timeout
        endpoint = InductorEndpoint(inductor, 'foo', ('foo'), reactor, timeout=1)

        dataDeferred = defer.Deferred()
        connDeferred = defer.Deferred()
        class MockProtocol(protocol.Protocol):
            data = []
            def connectionMade(self):
                for data in relay_data:
                    self.transport.relayData(data)
                self.transport.loseConnection()
            def dataReceived (self, data):
                self.data.append(data)
            def connectionLost (self, reason):
                connDeferred.callback(reason)
                dataDeferred.callback(self.data)

        protocolFactory = protocol.ClientFactory()
        protocolFactory.protocol = MockProtocol
        clientDeferred = endpoint.connect(protocolFactory)

        @clientDeferred.addCallback
        def check_client(client):
            self.assertIsInstance(client, MockProtocol)

        @dataDeferred.addCallback
        def check_received_data(data):
            return self.assertEqual(data, relay_data)

        # Check that the connectionLost reason
        self.assertFailure(connDeferred, ConnectionDone)

        return defer.DeferredList([clientDeferred, dataDeferred, connDeferred],
                                  fireOnOneErrback=True)
