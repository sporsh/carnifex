import os
import pwd
from twisted.internet import defer
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.conch.ssh import connection, common
from twisted.conch.ssh.connection import SSHConnection
from twisted.conch.client.default import SSHUserAuthClient
from twisted.conch.client.options import ConchOptions
from carnifex.inductor import ProcessInductor
from carnifex.ssh.client import SSHClientFactory
from carnifex.ssh.session import SSHSession
from carnifex.ssh.command import SSHCommand


class SSHProcessInductor(ProcessInductor):
    _sep = ';' # '&&' to fail fast or ';' to continue on fails
    _cd = 'cd'

    def __init__(self, reactor, host, port, timeout=30, bindAddress=None,
                 precursor=None):
        self._connections = {}
        self.reactor = reactor
        self.endpoint = TCP4ClientEndpoint(reactor, host, port, timeout,
                                           bindAddress)
        self.precursor = precursor # 'source /etc/profile'

    def execute(self, processProtocol, command, env={},
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

        sshCommand = (command if isinstance(command, SSHCommand)
                      else SSHCommand(command, self.precursor, path))
        commandLine = sshCommand.getCommandLine()

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
                                              common.NS(commandLine),
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
