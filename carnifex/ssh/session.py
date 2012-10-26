import struct
from twisted.python import failure
from twisted.internet.error import ProcessTerminated, ProcessDone
from twisted.conch.ssh import common, connection
from twisted.conch.ssh.channel import SSHChannel
from twisted.internet.interfaces import IProcessTransport
from zope.interface.declarations import implements


class SSHSession(SSHChannel):
    implements(IProcessTransport)

    name = 'session'
    exitCode = None
    signal = None
    status = -1
    pid = None

    def __init__(self, deferred, protocol, *args, **kwargs):
        SSHChannel.__init__(self, *args, **kwargs)
        self.deferred = deferred
        self.protocol = protocol

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

    def loseConnection(self):
        self.closeStdin()
        self.closeStderr()
        self.closeStdout()
        SSHChannel.loseConnection(self)

    def signalProcess(self, signal):
        """Deliver a signal to the remote process/service.

        @param signal: signal name (without the "SIG" prefix)
        @warning: Some systems may not implement signals,
                  in which case they SHOULD ignore this message.
        """
        signal = common.NS(signal)
        return self.conn.sendRequest(self, 'signal', signal, wantReply=True)

    def channelOpen(self, specificData):
        # Connect the SSHSessionProcessProtocol
        self.protocol.makeConnection(self)
        # Signal that we are opened
        self.deferred.callback(specificData)

    def openFailed(self, reason):
        self.deferred.errback(reason)

    def closed(self):
        if self.exitCode or self.signal:
            reason = failure.Failure(ProcessTerminated(self.exitCode,
                                                       self.signal,
                                                       self.status))
        else:
            reason = failure.Failure(ProcessDone(status=self.status))
        protocol = self.protocol
        del self.protocol
        protocol.processEnded(reason)

    def dataReceived(self, data):
            self.protocol.childDataReceived(1, data)

    def extReceived(self, dataType, data):
        if dataType == connection.EXTENDED_DATA_STDERR:
            self.protocol.childDataReceived(2, data)
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
        self.exitCode = int(struct.unpack('>L', data)[0])

    def request_exit_signal(self, data):
        """Called when remote command terminate violently due to a signal.

        @param data:  The ssh message

        byte      SSH_MSG_CHANNEL_REQUEST
        uint32    recipient channel
        string    "exit-signal"
        boolean   FALSE
        string    signal name (without the "SIG" prefix)
        boolean   core dumped
        string    error message in ISO-10646 UTF-8 encoding
        string    language tag [RFC3066]
        """
        #TODO: Implement this properly
        self.signal = data
