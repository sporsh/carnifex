import os
import pwd
import struct
from twisted.python import failure
from twisted.python.win32 import quoteArguments
from twisted.internet import defer
from twisted.internet.error import ProcessDone, ProcessTerminated
from twisted.internet.protocol import ClientFactory
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.conch.ssh import connection, common
from twisted.conch.ssh.connection import SSHConnection
from twisted.conch.ssh.transport import SSHClientTransport
from twisted.conch.ssh.channel import SSHChannel
from twisted.conch.client.default import SSHUserAuthClient
from twisted.conch.client.options import ConchOptions
from carnifex.inductor import ProcessInductor


class SSHProcessInductor(ProcessInductor):

    def __init__(self, reactor, host, port, timeout=30, bindAddress=None):
        self.reactor = reactor
        self._connections = {}
        self.endpoint = TCP4ClientEndpoint(reactor, host, port, timeout,
                                           bindAddress)

    def execute(self, processProtocol, executable, args=(), env={},
                path=None, uid=None, gid=None, usePTY=0, childFDs=None):
        """Execute a process on the remote machine using SSH

        @param processProtocol: the ProcessProtocol instance to connect
        @param executable: the executable program to run
        @param args: the arguments to pass to the process
        @param env: environment variables to request the remote ssh server to set
        @param path: the remote path to start the remote process on
        @param uid: user id or username to connect to the ssh server with
        @param gid: this is not used for remote ssh processes
        @param usePTY: wither to request a pty for the process
        @param childFDs: file descriptors to use for stdin, stdout and stderr
        """

        args = args or (executable,)
        cmdline = quoteArguments(args)

        # Get the username from a uid, or use current user
        uid = uid or os.getuid()
        if isinstance(uid, int):
            user = pwd.getpwuid(uid).pw_name
        else:
            user = uid

        sessionOpenDeferred = defer.Deferred()
        session = SSHSession(sessionOpenDeferred, processProtocol)

        # Get connection to ssh server
        connectionDeferred = self.getConnection(user)
        @connectionDeferred.addCallback
        def executeCommand(connection):
            connection.openChannel(session)
            @sessionOpenDeferred.addCallback
            def sessionOpened(specificData):
                # Send requests to set the environment variables
                for variable, value in env.iteritems():
                    data = common.NS(variable) + common.NS(value)
                    connection.sendRequest(session, 'env', data)
                # Send request to exec the command line
                return connection.sendRequest(session, 'exec',
                                              common.NS(cmdline),
                                              wantReply=True)
            return sessionOpenDeferred

        return session

    def getConnection(self, user):
        options = ConchOptions()
        verifyHostKey = lambda *a, **kwa: defer.succeed(True)

        serviceStartedDeferred = defer.Deferred()
        serviceStoppedDeferred = defer.Deferred()
        connection = SSHConnection()
        connection.serviceStarted = lambda: serviceStartedDeferred.callback(None)
        connection.serviceStopped = lambda: serviceStoppedDeferred.callback(None)
        @serviceStartedDeferred.addCallback
        def connectionServiceStarted(result):
            self._connections[user] = connection
            self._disconnectDeferred = serviceStoppedDeferred
            return connection
        @serviceStoppedDeferred.addCallback
        def connectionServiceStopped(result):
            del self._connections[user]

        userAuthObject = SSHUserAuthClient(user, options, connection)

        connectionLostDeferred = defer.Deferred()
        sshClientFactory = SSHClientFactory(verifyHostKey, userAuthObject)
        sshClientFactory.clientConnectionFailed = lambda _, reason: serviceStartedDeferred.errback(reason)
        sshClientFactory.clientConnectionLost = connectionLostDeferred.errback

        connectionDeferred = self.endpoint.connect(sshClientFactory)
        @connectionDeferred.addCallback
        def connected(transport):
            self._transport = transport
            return serviceStartedDeferred
        return connectionDeferred

    def disconnectAll(self):
        for connection in self._connections.values():
            connection.transport.loseConnection()

    def disconnectUser(self, user):
        connection = self._connections[user]
        connection.transport.loseConnection()

    def __del__(self):
        self.disconnectAll()


class SSHClientFactory(ClientFactory):
    def __init__(self, verifyHostKey, userAuthObject):
        self.verifyHostKey = verifyHostKey
        self.userAuthObject = userAuthObject

    def buildProtocol(self, addr):
        trans = SSHClientTransport()
        trans.verifyHostKey = self.verifyHostKey
        trans.connectionSecure = lambda: trans.requestService(self.userAuthObject)
        return trans


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
