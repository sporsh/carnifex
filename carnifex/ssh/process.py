"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

import struct
from zope.interface.declarations import implementer
from twisted.python import failure
from twisted.internet.interfaces import IProcessTransport
from twisted.internet.error import ProcessTerminated, ProcessDone
from twisted.conch.ssh import common, connection
from twisted.internet import defer
from carnifex.ssh.session import SSHSession


def connectProcess(connection, processProtocol, commandLine='', env={},
                   usePTY=None, childFDs=None, *args, **kwargs):
    """Opens a SSHSession channel and connects a ProcessProtocol to it

    @param connection: the SSH Connection to open the session channel on
    @param processProtocol: the ProcessProtocol instance to connect to the process
    @param commandLine: the command line to execute the process
    @param env: optional environment variables to set for the process
    @param usePTY: if set, request a PTY for the process
    @param childFDs: custom child file descriptors for the process
    """
    processOpenDeferred = defer.Deferred()
    process = SSHProcess(processProtocol, commandLine, env, usePTY, childFDs,
                         *args, **kwargs)
    process.processOpen = processOpenDeferred.callback
    process.openFailed = processOpenDeferred.errback

    connection.openChannel(process)
    return processOpenDeferred


@implementer(IProcessTransport)
class SSHProcess(SSHSession):

    status = -1
    pid = None

    _exitCode = None
    _signal = None

    def __init__(self, processProtocol, commandLine, env, usePTY, childFDs,
                 *args, **kwargs):
        """
        @param processProtocol: A instance of a ProcessProtocol
        @param childFDs: Custom child file descriptor mappings
        """
        SSHSession.__init__(self, env, usePTY, *args, **kwargs)
        self.processProtocol = processProtocol
        self.commandLine = commandLine
        self.childFDs = childFDs

    def closeStdin(self):
        self.closeChildFD(0)

    def closeStdout(self):
        self.closeChildFD(1)

    def closeStderr(self):
        self.closeChildFD(2)

    def closeChildFD(self, descriptor):
        if descriptor == 0:
            self.conn.sendEOF(self)

    def writeToChild(self, childFD, data):
        if childFD == 0:
            self.write(data)
        #TODO: does the following make sense?
#        elif childFD == 2:
#            self.writeExtended(connection.EXTENDED_DATA_STDERR, data)

    def loseConnection(self):
        self.closeStdin()
        self.closeStderr()
        self.closeStdout()
        SSHSession.loseConnection(self)

    def signalProcess(self, signal):
        """Deliver a _signal to the remote process/service.

        @param _signal: _signal name (without the "SIG" prefix)
        @warning: Some systems may not implement signals,
                  in which case they SHOULD ignore this message.
        """
        signal = common.NS(signal)
        return self.conn.sendRequest(self, '_signal', signal, wantReply=True)

    def processOpen(self, specificData):
        """Called when the command has executed the process
        """
        pass

    def sessionOpen(self, specificData):
        """Callback triggered when the session channel has opened
        """
        # Make sure the protocol use the session channel as transport
        self.processProtocol.makeConnection(self)
        # Request execution of the command line
        exec_d = self.requestExec(self.commandLine)
        exec_d.addCallbacks(self.processOpen, self.openFailed)

    def closed(self):
        if self._exitCode or self._signal:
            reason = failure.Failure(ProcessTerminated(self._exitCode,
                                                       self._signal,
                                                       self.status))
        else:
            reason = failure.Failure(ProcessDone(status=self.status))
        processProtocol = self.processProtocol
        del self.processProtocol
        processProtocol.processEnded(reason)

    def dataReceived(self, data):
            self.processProtocol.childDataReceived(1, data)

    def extReceived(self, dataType, data):
        if dataType == connection.EXTENDED_DATA_STDERR:
            self.processProtocol.childDataReceived(2, data)
        else:
            #TODO: Warn about dropped unrecognized data?!
            pass

    def request_exit_status(self, data):
        """Called when the command running at the other end terminates with an
        exit status.

        @param data: The ssh message

        byte      SSH_MSG_CHANNEL_REQUEST
        uint32    recipient channel
        string    "exit-status"
        boolean   FALSE
        uint32    exit_status
        """
        self._exitCode = int(struct.unpack('>L', data)[0])

    def request_exit_signal(self, data):
        """Called when remote command terminate violently due to a _signal.

        @param data:  The ssh message

        byte      SSH_MSG_CHANNEL_REQUEST
        uint32    recipient channel
        string    "exit-_signal"
        boolean   FALSE
        string    _signal name (without the "SIG" prefix)
        boolean   core dumped
        string    error message in ISO-10646 UTF-8 encoding
        string    language tag [RFC3066]
        """
        #TODO: Implement this properly
        self._signal = data
