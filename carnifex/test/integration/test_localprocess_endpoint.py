from twisted.trial.unittest import TestCase
from carnifex.localprocess import LocalProcessInductor
from twisted.internet.error import ConnectionDone
from twisted.internet import protocol, reactor, defer
from carnifex.endpoint import InductorEndpoint


class GatherProtocol(protocol.Protocol):
    def __init__(self):
        self.resultDeferred = defer.Deferred()
        self.gatheredData = []

    def dataReceived (self, data):
        self.gatheredData.append(data)

    def connectionLost (self, reason):
        self.resultDeferred.callback((self.gatheredData, reason))


class InductorEndpointTest(TestCase):
    """Test connecting a twisted protocol to a process.
    """

    def test_real_endpoint(self):
        executable = 'echo'
        echoText = "hello world!"
        expectedGatheredData = [echoText + '\n']
        expectedConnectionLostReason = ConnectionDone

        inductor = LocalProcessInductor(reactor)
        endpoint = InductorEndpoint(inductor, executable=executable,
                                    args=(executable, echoText), timeout=1)

        protocolFactory = protocol.ClientFactory()
        protocolFactory.protocol = GatherProtocol
        clientDeferred = endpoint.connect(protocolFactory)

        @clientDeferred.addCallback
        def checkClient(client):
            self.assertIsInstance(client, GatherProtocol)
            return client.resultDeferred

        @clientDeferred.addCallback
        def checkGatheredData((gatheredData, connectionLostReason)):
            self.assertEqual(gatheredData, expectedGatheredData)
            return connectionLostReason

        # Check that the connection was lost as expected
        return self.assertFailure(clientDeferred, expectedConnectionLostReason)

        return clientDeferred
