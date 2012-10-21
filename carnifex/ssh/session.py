import struct
from twisted.python import failure
from twisted.internet.error import ProcessTerminated, ProcessDone
from twisted.conch.ssh import connection
from twisted.conch.ssh.channel import SSHChannel


class SSHSession(SSHChannel):
    name = 'session'
    exitCode = None
    signal = None
    status = -1

    def __init__(self, deferred, protocol, *args, **kwargs):
        SSHChannel.__init__(self, *args, **kwargs)
        self.deferred = deferred
        self.protocol = protocol

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
