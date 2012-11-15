from twisted.internet import defer
from twisted.trial import unittest
from carnifex.sshprocess import SSHProcessInductor
from twisted.internet.protocol import Protocol
from getpass import getpass
from carnifex.ssh.session import connectShell, connectExec
from twisted.internet.error import ConnectionDone

DEBUG = True
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

class SSHProcessInductorTest(unittest.TestCase):
    """This test need to authenticate the connect to an ssh server.
    """

    def setUp(self):
        from twisted.internet import reactor
        host, port = 'localhost', 22
        self.inductor = SSHProcessInductor(reactor, host, port)
        self.inductor.setCredentials(UID, PASSWORD)

    def test_connect_shell(self):
        stdoutText = "output out o text"
        stderrText = "error err e text"
        exitCode = 42
        pythonScript = ("import sys;"
                        "sys.stdout.write('%s');"
                        "sys.stderr.write('%s');"
                        "exit(%i);"
                        % (stdoutText, stderrText, exitCode))
        command = "%s -c %r" % (PYTHON_COMMAND, pythonScript)

        data = []
        disconnectedDeferred = defer.Deferred()
        protocol = Protocol()
        protocol.dataReceived = data.append
        protocol.connectionLost = disconnectedDeferred.callback
        connectionDeferred = self.inductor.getConnection(uid=UID)
        connectionDeferred.addCallback(connectShell, protocol)

        @connectionDeferred.addCallback
        def logout(result):
            print "RESULT", result
            print "PROTOCOL", protocol
            protocol.transport.loseConnection()

#        connectionDeferred.addCallback(connectExec, protocol, command)
        connectionDeferred.addErrback(self.fail)

        self.assertFailure(disconnectedDeferred, ConnectionDone)
        @disconnectedDeferred.addCallback
        def checkResult(reason):
            print "REASON", reason
            print "DATA", data
        return disconnectedDeferred

    def tearDown(self):
        inductor = self.inductor
        self.inductor = None
        inductor.disconnectAll()
