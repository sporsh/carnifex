import struct
from twisted.internet import defer
from twisted.conch.ssh import common
from twisted.conch.ssh.channel import SSHChannel


def execSession(connection, protocol, commandLine, env={}, usePTY=None):
    return connectSession(connection, protocol, 'exec', common.NS(commandLine),
                          env, usePTY)

def connectSession(connection, protocol, sessionType, sessionData='',
                   env={}, usePTY=None):
    sessionOpenDeferred = defer.Deferred()
    session = SSHSession(protocol)
    connection.openChannel(session)
    def sessionOpened(specificData):
        protocol.makeConnection(session)
        requestEnv(connection, session, env)
        if usePTY:
            requestPty(connection, session)
        deferred = connection.sendRequest(session, sessionType, sessionData,
                                          wantReply=True)
        deferred.chainDeferred(sessionOpenDeferred)
    session.channelOpen = sessionOpened
    session.openFailed = sessionOpenDeferred.errback
    return sessionOpenDeferred

def requestPty(connection, session, term='vt100', columns=0, rows=0, width=0,
               height=0, modes=''):
    """Request allocation of a pseudo-terminal for a session

    @param session: recipient session channel
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
    dimensions = common.NS(struct.pack('>4L', columns, rows, width, height))
    data = common.NS(term) + dimensions + common.NS(modes)
    connection.sendRequest(session, 'pty-req', data, wantReply=False)

def requestEnv(connection, session, env={}):
    """Send requests to set the environment variables
    """
    for variable, value in env.iteritems():
        data = common.NS(variable) + common.NS(value)
        connection.sendRequest(session, 'env', data)


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

    def requestPty(self, term='vt100', columns=0, rows=0, width=0, height=0, modes=''):
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
        dimensions = common.NS(struct.pack('>4L', columns, rows, width, height))
        data = common.NS(term) + dimensions + common.NS(modes)
        return self.sendRequest('pty-req', data)

    def requestEnv(self, env={}):
        """Send requests to set the environment variables for the channel
        """
        for variable, value in env.iteritems():
            data = common.NS(variable) + common.NS(value)
            self.sendRequest('env', data)

    def sendRequest(self, requestType, data, wantReply=False):
        assert self.conn, "Channel must be opened to send requests"
        return self.conn.sendRequest(self, requestType, data, wantReply)
