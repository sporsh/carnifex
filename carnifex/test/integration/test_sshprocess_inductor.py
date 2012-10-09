from twisted.internet import defer, reactor
from twisted.trial.unittest import TestCase
from carnifex.sshprocess import SSHProcessInductor
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.error import ProcessTerminated, ProcessDone

USER = 'localuser'
HOST = 'localhost'
PORT = 22

SUCCEEDING_COMMAND = 'true'
FAILING_COMMAND = 'false'
ECHO_COMMAND = 'echo'

class InductorTest(TestCase):
    def setUp(self):
        self.inductor = SSHProcessInductor(reactor, USER, HOST, PORT)

    def tearDown(self):
        inductor = self.inductor
        self.inductor = None
        inductor.disconnectAll()

    def test_execute_exitcode_0(self):
        executable = SUCCEEDING_COMMAND
        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        self.inductor.execute(protocol, executable)
        return self.assertFailure(disconnectedDeferred, ProcessDone)

    def test_execute_nonzero_exitcode(self):
        executable = FAILING_COMMAND
        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        self.inductor.execute(protocol, executable)
        return self.assertFailure(disconnectedDeferred, ProcessTerminated)

    def test_execute_echo_return(self):
        executable = ECHO_COMMAND
        echoText = "some text to be echoed"
        expectedResult = (echoText + '\n', '', 0)

        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        resultDeferred = self.inductor.run(executable, (executable, echoText))
        @resultDeferred.addCallback
        def checkResult(result):
            self.assertEqual(result, expectedResult)

        return resultDeferred
