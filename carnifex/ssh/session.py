"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

import os
from twisted.internet import defer
from twisted.conch.ssh import common
from twisted.conch.ssh.channel import SSHChannel
from twisted.internet.protocol import connectionDone
from twisted.conch.ssh.session import packRequest_pty_req


def connectExec(connection, protocol, commandLine):
    """Connect a Protocol to a ssh exec session
    """
    deferred = connectSession(connection, protocol)
    @deferred.addCallback
    def requestSubsystem(session):
        return session.requestExec(commandLine)
    return deferred

def connectShell(connection, protocol):
    """Connect a Protocol to a ssh shell session
    """
    deferred = connectSession(connection, protocol)
    @deferred.addCallback
    def requestSubsystem(session):
        return session.requestShell()
    return deferred

def connectSubsystem(connection, protocol, subsystem):
    """Connect a Protocol to a ssh subsystem channel
    """
    deferred = connectSession(connection, protocol)
    @deferred.addCallback
    def requestSubsystem(session):
        return session.requestSubsystem(subsystem)
    return deferred

def connectSession(connection, protocol, sessionFactory=None, *args, **kwargs):
    """Open a SSHSession channel and connect a Protocol to it

    @param connection: the SSH Connection to open the session channel on
    @param protocol: the Protocol instance to connect to the session
    @param sessionFactory: factory method to generate a SSHSession instance
    @note: :args: and :kwargs: are passed to the sessionFactory
    """
    factory = sessionFactory or defaultSessionFactory
    session = factory(*args, **kwargs)
    session.dataReceived = protocol.dataReceived
    session.closed = lambda: protocol.connectionLost(connectionDone)

    deferred = defer.Deferred()
    @deferred.addCallback
    def connectProtocolAndReturnSession(specificData):
        protocol.makeConnection(session)
        return session
    session.sessionOpen = deferred.callback
    session.openFailed = deferred.errback

    connection.openChannel(session)

    return deferred

def defaultSessionFactory(env={}, usePTY=False, *args, **kwargs):
    """Create a SSHChannel of the given :channelType: type
    """
    return SSHSession(env, usePTY, *args, **kwargs)


class SSHSession(SSHChannel):
    name = 'session'

    def __init__(self, env, usePTY, *args, **kwargs):
        SSHChannel.__init__(self, *args, **kwargs)
        self.env = env
        self.usePTY = usePTY

    def sessionOpen(self, specificData):
        """Called when the session opened successfully
        """

    def channelOpen(self, specificData):
        # Request environment variables for the session if specified
        self.requestEnv(self.env)
        # Request pty for the session if desired
        if self.usePTY:
            self.requestPty()

        self.sessionOpen(specificData)

    def requestShell(self):
        """Request a shell and return a deferred reply.
        """
        return self.sendRequest('shell', data='', wantReply=True)

    def requestExec(self, commandLine):
        """Request execution of :commandLine: and return a deferred reply.
        """
        data = common.NS(commandLine)
        return self.sendRequest('exec', data, wantReply=True)

    def requestSubsystem(self, subsystem):
        """Request a subsystem and return a deferred reply.
        """
        data = common.NS(subsystem)
        return self.sendRequest('subsystem', data, wantReply=True)

    def requestPty(self, term=None, rows=0, cols=0, xpixel=0, ypixel=0, modes=''):
        """Request allocation of a pseudo-terminal for a channel

        @param term: TERM environment variable value (e.g., vt100)
        @param columns: terminal width, characters (e.g., 80)
        @param rows: terminal height, rows (e.g., 24)
        @param width: terminal width, pixels (e.g., 640)
        @param height: terminal height, pixels (e.g., 480)
        @param modes: encoded terminal modes

        The dimension parameters are only informational.
        Zero dimension parameters are ignored. The columns/rows dimensions
        override the pixel dimensions (when nonzero). Pixel dimensions refer
        to the drawable area of the window.
        """
        #TODO: Needs testing!
        term = term or os.environ.get('TERM', '')
        data = packRequest_pty_req(term, (rows, cols, xpixel, ypixel), modes)
        return self.sendRequest('pty-req', data)

    def requestEnv(self, env={}):
        """Send requests to set the environment variables for the channel
        """
        for variable, value in env.items():
            data = common.NS(variable) + common.NS(value)
            self.sendRequest('env', data)

    def sendRequest(self, requestType, data, wantReply=False):
        assert self.conn, "Channel must be opened to send requests"
        return self.conn.sendRequest(self, requestType, data, wantReply)
