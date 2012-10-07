from twisted.trial.unittest import TestCase
from carnifex.localprocess import LocalProcessInductor
from twisted.internet.error import ConnectionDone
from twisted.internet import protocol, reactor, defer
from carnifex.endpoint import InductorEndpoint


class InductorEndpointTest(TestCase):
    """Test connecting a twisted protocol to a process.
    """

    def test_real_endpoint(self):
        executable = 'echo'
        echo_text = "hello world!"
        expected_data = echo_text + '\n'
        #TODO: fix timeout
        endpoint = InductorEndpoint(inductor, executable, args=(executable, echo_text))

        dataDeferred = defer.Deferred()
        connDeferred = defer.Deferred()
        class MockProtocol(protocol.Protocol):
            def dataReceived (self, data):
                dataDeferred.callback(data)
            def connectionLost (self, reason):
                connDeferred.callback(reason)

        protocolFactory = protocol.ClientFactory()
        protocolFactory.protocol = MockProtocol
        clientDeferred = endpoint.connect(protocolFactory)

        @clientDeferred.addCallback
        def check_client(client):
            self.assertIsInstance(client, MockProtocol)

        @dataDeferred.addCallback
        def check_received_data(data):
            return self.assertEqual(data, expected_data)

        # Check that the connectionLost reason
        self.assertFailure(connDeferred, ConnectionDone)

        return defer.DeferredList([clientDeferred, dataDeferred, connDeferred],
                                  fireOnOneErrback=True)
