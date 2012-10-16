from twisted.internet import defer
from twisted.trial.unittest import TestCase
from carnifex.sshprocess import SSHProcessInductor
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.error import ProcessTerminated, ProcessDone
from carnifex.localprocess import LocalProcessInductor

UID = None # indicate that we want to run processes as the current user.

SUCCEEDING_COMMAND = 'true' # `true`should return exitcode 0
FAILING_COMMAND = 'false' # `false`should return a nonzero exitcode
PYTHON_COMMAND = 'python'


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
        @disconnectedDeferred.addErrback
        def checkExitCode(failure):
            exitCode = failure.value.exitCode
            self.assertNotEqual(exitCode, 0)
            return failure
        return self.assertFailure(disconnectedDeferred, ProcessTerminated)

    def test_run_stdout_stderr_exit(self):
        """Check that we get the expected stdout, stderr and exit code
        """
        stdoutText = "output out o text"
        stderrText = "error err e text"
        exitCode = 47
        pythonScript = ("import sys;"
                        "sys.stdout.write('%s');"
                        "sys.stderr.write('%s');"
                        "exit(%i);"
                        % (stdoutText, stderrText, exitCode))
        args = (PYTHON_COMMAND, '-c', pythonScript)

        disconnectedDeferred = defer.Deferred()
        protocol = ProcessProtocol()
        protocol.processEnded = disconnectedDeferred.callback
        resultDeferred = self.inductor.run(args[0], args, uid=UID)
        @resultDeferred.addCallback
        def checkResult((r_stdoutText, r_stderrText, r_exitCode)):
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

    def tearDown(self):
        inductor = self.inductor
        self.inductor = None
        inductor.disconnectAll()
