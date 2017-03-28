"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

import sys
import getpass
from twisted.python import failure
from twisted.internet import defer
from twisted.internet.endpoints import clientFromString
from twisted.conch.ssh.connection import SSHConnection
from carnifex.inductor import ProcessInductor
from carnifex.ssh.client import SSHClientFactory
from carnifex.ssh.command import SSHCommand
from carnifex.ssh.userauth import AutomaticUserAuthClient
from carnifex.ssh.process import connectProcess

if sys.version_info.major > 2:
    basestring = str

class UnknownHostKey(Exception):
    """Raised when we reject validation of a server's host key
    """
    pass


class AllHostKeys(object):
    """Placeholder for known hosts container to allow all host keys.
    """
    def __contains__(self, key):
        return True
allHostKeys = AllHostKeys()


class SSHProcessInductor(ProcessInductor):
    _sep = ';' # '&&' to fail fast or ';' to continue on fails
    _cd = 'cd'
    _defaultUser = None
    knownHosts = allHostKeys

    def __init__(self, reactor, host, port, timeout=30, bindAddress=None,
                 precursor=None, credentials=None):
        self._connections = {}
        self.reactor = reactor
        description = 'tcp:host=%s:port=%i:timeout=%i' % (host, port, timeout)
        if bindAddress:
            description += ':bindAddress=%s' % bindAddress
        self.endpoint = clientFromString(reactor, description)
        self.precursor = precursor # 'source /etc/profile'
        self.credentials = credentials or {}

    def setCredentials(self, uid, password=None, privateKey=None, publicKey=None):
        user = self._getUser(uid)
        credentials = self.credentials.setdefault(user, {})
        credentials['password'] = password
        credentials['privateKey'] = privateKey
        credentials['publicKey'] = publicKey

    def addKnownHost(self, hostKey, fingerprint):
        if self.knownHosts == allHostKeys:
            self.knownHosts = {}
        self.knownHosts[fingerprint] = hostKey

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

        # Get connection to ssh server
        connectionDeferred = self.getConnection(uid)
        # spawn the remote process
        connectionDeferred.addCallback(connectProcess, processProtocol,
                                       commandLine, env, usePTY, childFDs)
        return connectionDeferred

    def getConnection(self, uid=None):
        #TODO: Fix case where we try to get another connection to the same user
        # before the first has connected...
        user = self._getUser(uid)
        connection = self._connections.get(user, None)
        if connection:
            return defer.succeed(connection)
        # This will be called back if we already started connecting the user
        self._connections[user] = failure.Failure(Exception("Already trying to "
                                                            "connect %r" % user))
        return self.startConnection(user)

    def startConnection(self, user):
        serviceStartedDeferred = defer.Deferred()
        connectionService = SSHConnection()
        def serviceStarted():
            self._connections[user] = connectionService
            serviceStartedDeferred.callback(connectionService)
        connectionService.serviceStarted = serviceStarted

        connectionLostDeferred = defer.Deferred()
        userAuthObject = self._getUserAuthObject(user, connectionService)
        sshClientFactory = SSHClientFactory(connectionLostDeferred,
                                            self._verifyHostKey, userAuthObject)

        def connectionEnded(reason):
            self._connections[user] = None
            serviceStartedDeferred.called or serviceStartedDeferred.errback(reason)
        connectionLostDeferred.addBoth(connectionEnded)
        connectionMadeDeferred = self.endpoint.connect(sshClientFactory)
        connectionMadeDeferred.addErrback(connectionEnded)

        return serviceStartedDeferred

    def disconnectAll(self):
        for connection in self._connections.values():
            if hasattr(connection, 'transport'):
                connection.transport.loseConnection()

    def _getUser(self, uid=None):
        user = uid or self._defaultUser or getpass.getuser()
        assert isinstance(user, basestring), \
            "uid (%r) must be a username for SSH" % uid
        return user

    def _getCredentials(self, user):
        return self.credentials.get(user, dict(password=None,
                                               privateKey=None,
                                               publicKey=None))

    def _getUserAuthObject(self, user, connection):
        """Get a SSHUserAuthClient object to use for authentication

        @param user: The username to authenticate for
        @param connection: The connection service to start after authentication
        """
        credentials = self._getCredentials(user)
        userAuthObject = AutomaticUserAuthClient(user, connection, **credentials)
        return userAuthObject

    def _verifyHostKey(self, hostKey, fingerprint):
        """Called when ssh transport requests us to verify a given host key.
        Return a deferred that callback if we accept the key or errback if we
        decide to reject it.
        """
        if fingerprint in self.knownHosts:
            return defer.succeed(True)
        return defer.fail(UnknownHostKey(hostKey, fingerprint))

    def __del__(self):
        self.disconnectAll()
