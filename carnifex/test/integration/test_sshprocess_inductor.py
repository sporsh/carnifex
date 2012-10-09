from twisted.internet import defer
from twisted.trial.unittest import TestCase
from carnifex.sshprocess import SSHProcessInductor
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.error import ProcessTerminated, ProcessDone

UID = None # indicate that we want to run processes as the current user.

SUCCEEDING_COMMAND = 'true' # `true`should return exitcode 0
FAILING_COMMAND = 'false' # `false`should return a nonzero exitcode
ECHO_COMMAND = 'echo' # 'echo` should echo back on stdout

# `echo` return an additional newline after the given text to echo.
echoTransform = lambda text: text + '\n'


class InductorTestMixin(object):
    def test_execute_exitcode_0(self):
        """Check that we get the expected reason failure object
        when a process exits with exit code 0.
        """
        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        self.inductor.execute(protocol, SUCCEEDING_COMMAND, uid=UID)
        return self.assertFailure(disconnectedDeferred, ProcessDone)

    def test_execute_nonzero_exitcode(self):
        """Check that we get the expected failure when a process exits
        with a nonzero exit code.
        """
        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        self.inductor.execute(protocol, FAILING_COMMAND, uid=UID)
        # Process should return a ProcessTerminated failure
        # when it exits with a nonzero exit code
        return self.assertFailure(disconnectedDeferred, ProcessTerminated)

    def test_execute_echo_return(self):
        """Check that we get the expected stdout, stderr and exit code
        """
        executable = ECHO_COMMAND
        echoText = "some text to be echoed"
        args = (executable, echoText)

        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        resultDeferred = self.inductor.run(executable, args, uid=self.uid)
        @resultDeferred.addCallback
        def checkResult((stdin, stderr, exitCode)):
            self.assertEqual(stdin, echoTransform(echoText), "stdout not as expected")
            self.assertEqual(stderr, '', "unexpected data on stderr")
            self.assertEqual(exitCode, 0, "nonzero exit code")

        return resultDeferred
class SSHProcessInductorTest(TestCase, InductorTestMixin):
    """This test need to authenticate the connect to an ssh server.
    """
    def setUp(self):
        from twisted.internet import reactor
        self.uid = None # indicate that we want to run as the current user.
        self.host = 'localhost'
        self.port = 22
        self.inductor = SSHProcessInductor(reactor, self.host, self.port)

    def tearDown(self):
        InductorTestMixin
        inductor = self.inductor
        self.inductor = None
        inductor.disconnectAll()
