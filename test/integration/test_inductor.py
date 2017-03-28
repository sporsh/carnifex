from twisted.internet import defer
from twisted.trial.unittest import TestCase
from carnifex.sshprocess import SSHProcessInductor
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.error import ProcessTerminated, ProcessDone,\
    ConnectionRefusedError
from carnifex.localprocess import LocalProcessInductor
from getpass import getpass
from carnifex.ssh.client import TooManyAuthFailures

DEBUG = False
if DEBUG:
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)
    defer.Deferred.debug = True

UID = None # indicate that we want to run processes as the current user.
PASSWORD = None or getpass() # Set password here, or we will launch a prompt
# These credentials should fail:
WRONG_USER, WRONG_PASSWORD = 'nouser', 'wrongpassword'

SUCCEEDING_COMMAND = 'true' # `true`should return exitcode 0
FAILING_COMMAND = 'false' # `false`should return a nonzero exitcode
PYTHON_COMMAND = 'python'


class InductorTestMixin(object):
    def test_execute_exitcode_0(self):
        """Check that we get the expected reason failure object
        when a process exits with exit code 0.
        """
        processEndedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = processEndedDeferred.callback
        processDeferred = self.inductor.execute(protocol, SUCCEEDING_COMMAND,
                                                uid=UID)
        self.assertFailure(processEndedDeferred, ProcessDone)
        return defer.DeferredList([processDeferred, processEndedDeferred],
                                  fireOnOneErrback=True)

    def test_execute_nonzero_exitcode(self):
        """Check that we get the expected failure when a process exits
        with a nonzero exit code.
        """
        processEndedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = processEndedDeferred.callback
        processDeferred = self.inductor.execute(protocol, FAILING_COMMAND,
                                                uid=UID)
        # Process should return a ProcessTerminated failure
        # when it exits with a nonzero exit code
        self.assertFailure(processEndedDeferred, ProcessTerminated)
        @processEndedDeferred.addErrback
        def checkExitCode(failure):
            exitCode = failure.value.exitCode
            self.assertNotEqual(exitCode, 0)
        return defer.DeferredList([processDeferred, processEndedDeferred],
                                  fireOnOneErrback=True)

    def test_run_stdout_stderr_exit(self):
        """Check that we get the expected stdout, stderr and exit code
        """
        stdoutText = "output out o text"
        stderrText = "error err e text"
        exitCode = 42
        pythonScript = ("import sys;"
                        "sys.stdout.write('%s');"
                        "sys.stderr.write('%s');"
                        "exit(%i);"
                        % (stdoutText, stderrText, exitCode))
        command = "%s -c %r" % (PYTHON_COMMAND, pythonScript)

        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        resultDeferred = self.inductor.run(command, uid=UID)
        resultDeferred.addErrback(self.fail)
        @resultDeferred.addCallback
        def checkResult(res):
            r_stdoutText, r_stderrText, r_exitCode = res
            self.assertEqual(r_stdoutText, stdoutText, "stdout not as expected")
            self.assertEqual(r_stderrText, stderrText, "stderr not as expected")
            self.assertEqual(r_exitCode, exitCode, "unexpected exit code")
        return resultDeferred

class LocalProcessInductorTest(TestCase, InductorTestMixin):
    def setUp(self):
        from twisted.internet import reactor
        self.inductor = LocalProcessInductor(reactor)


class SSHProcessInductorTest(TestCase, InductorTestMixin):
    """This test need to authenticate the connect to an ssh server.
    """

    def setUp(self):
        from twisted.internet import reactor
        host, port = 'localhost', 22
        self.inductor = SSHProcessInductor(reactor, host, port)
        self.inductor.setCredentials(UID, PASSWORD)

    def test_authentication_failure(self):
        """Check that we get auth failure with wring credentials.
        """
        self.inductor.setCredentials(WRONG_USER, WRONG_PASSWORD)
        protocol = ProcessProtocol()
        processDeferred = self.inductor.execute(protocol, SUCCEEDING_COMMAND,
                                                uid=WRONG_USER)
        return self.assertFailure(processDeferred, TooManyAuthFailures)

    def test_connection_refused(self):
        """Check that connection refused errors are handeled correctly.
        """
        from twisted.internet import reactor
        host, port = 'localhost', 1 # Use a port that is not open for connection
        self.inductor = SSHProcessInductor(reactor, host, port)
        deferred = self.inductor.getConnection()
        return self.assertFailure(deferred, ConnectionRefusedError)

    def tearDown(self):
        inductor = self.inductor
        self.inductor = None
        inductor.disconnectAll()
