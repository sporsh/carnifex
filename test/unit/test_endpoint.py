from twisted.trial.unittest import TestCase
from twisted.internet.error import ConnectionDone
from twisted.internet import protocol, defer, reactor
from carnifex.endpoint import InductorEndpoint
from .mocks import MockProcessInductor

stdout, stderr = 1, 2


class InductorEndpointTest(TestCase):
    """Test connecting a twisted protocol to a process.
    """

    def test_endpoint(self):
        fauxProcessData = [(stdout, 'some output'),
                           (stderr, 'error message'),
                           (stdout, 'info message'),
                           (stderr, 'os failure')]

        inductor = MockProcessInductor(reactor, fauxProcessData)
        endpoint = InductorEndpoint(inductor, 'foo', ('foo'), timeout=1)

        dataDeferred = defer.Deferred()
        connDeferred = defer.Deferred()
        class MockProtocol(protocol.Protocol):
            data = []
            def dataReceived (self, data):
                self.transport.write(data)
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
            expected = [d for _, d in fauxProcessData]
            return self.assertEqual(data, expected)

        # Check that the connectionLost reason
        self.assertFailure(connDeferred, ConnectionDone)

        return defer.DeferredList([clientDeferred, dataDeferred, connDeferred],
                                  fireOnOneErrback=True)
