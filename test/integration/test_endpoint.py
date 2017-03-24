import sys
from twisted.trial.unittest import TestCase
from carnifex.localprocess import LocalProcessInductor
from twisted.internet.error import ConnectionDone
from twisted.internet import protocol, defer
from carnifex.endpoint import InductorEndpoint
from carnifex.sshprocess import SSHProcessInductor
from getpass import getpass


DEBUG = False
if DEBUG:
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)
    defer.Deferred.debug = True

UID = None # indicate that we want to run processes as the current user.
PASSWORD = None or getpass() # Set password here, or we will launch a prompt

ECHO_COMMAND = 'echo' # 'echo` should echo back on stdout
# `echo` return an additional newline after the given text to echo.
if sys.version_info.major <= 2:
    echoTransform = lambda text: text + '\n'
else:
    echoTransform = lambda text: bytes(text, 'ascii') + b'\n'

class GatherProtocol(protocol.Protocol):
    def __init__(self):
        self.resultDeferred = defer.Deferred()
        self.gatheredData = []

    def dataReceived (self, data):
        self.gatheredData.append(data)

    def connectionLost (self, reason):
        self.resultDeferred.callback((self.gatheredData, reason))


class InductorEndpointTestMixin(object):
    """Test connecting a twisted protocol to a process.
    """
    def test_real_endpoint(self):
        echoText = "hello world!"
        expectedGatheredData = [echoTransform(echoText)]
        expectedConnectionLostReason = ConnectionDone

        command = "%s %r" % (ECHO_COMMAND, echoText)
        endpoint = InductorEndpoint(self.inductor, command=command, timeout=1)

        protocolFactory = protocol.ClientFactory()
        protocolFactory.protocol = GatherProtocol
        clientDeferred = endpoint.connect(protocolFactory)

        @clientDeferred.addCallback
        def checkClient(client):
            self.assertIsInstance(client, GatherProtocol)
            return client.resultDeferred

        @clientDeferred.addCallback
        def checkGatheredData(res):
            gatheredData, connectionLostReason = res
            self.assertEqual(gatheredData, expectedGatheredData)
            return connectionLostReason

        # Check that the connection was lost as expected
        return self.assertFailure(clientDeferred, expectedConnectionLostReason)

        return clientDeferred


class LocalProcessInductorEndpointTest(TestCase, InductorEndpointTestMixin):
    def setUp(self):
        from twisted.internet import reactor
        self.inductor = LocalProcessInductor(reactor)


class SSHInductorEndpointTest(TestCase, InductorEndpointTestMixin):
    def setUp(self):
        from twisted.internet import reactor
        host, port = 'localhost', 22
        self.inductor = SSHProcessInductor(reactor, host, port)
        self.inductor.setCredentials(UID, PASSWORD)

    def tearDown(self):
        inductor = self.inductor
        self.inductor = None
        inductor.disconnectAll()
