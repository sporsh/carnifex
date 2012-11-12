"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

from twisted.internet.protocol import ClientFactory
from twisted.conch.ssh.transport import SSHClientTransport,\
    DISCONNECT_PROTOCOL_ERROR
from twisted.internet.error import ConnectionClosed


class DisconnectError(ConnectionClosed):
    def __init__(self, reasonCode, description):
        ConnectionClosed.__init__(self, description)
        self.reasonCode = reasonCode
        self.description = description

class TooManyAuthFailures(DisconnectError):
    """Too many authentication failures for user
    """

# Mapping of reason codes to sensible disconnect error types
disconnectErrors = {DISCONNECT_PROTOCOL_ERROR: TooManyAuthFailures}


class SSHClientFactory(ClientFactory):
    def __init__(self, deferred, verifyHostKey, userAuthObject):
        self.deferred = deferred
        self.verifyHostKey = verifyHostKey
        self.userAuthObject = userAuthObject

    def buildProtocol(self, addr):
        transport = SSHTransport(self.deferred, self.userAuthObject,
                             self.verifyHostKey)
        return transport


class SSHTransport(SSHClientTransport):
    def __init__(self, deferred, userAuthObject, verifyHostKey):
        self.deferred = deferred
        self.userAuthObject = userAuthObject
        self.verifyHostKey = verifyHostKey

    def receiveError(self, reasonCode, description):
        """
        Called when we receive a disconnect error message from the other
        side.
        """
        error = disconnectErrors.get(reasonCode, DisconnectError)
        self.connectionClosed(error(reasonCode, description))
        SSHClientTransport.receiveError(self, reasonCode, description)

    def connectionLost(self, reason):
        SSHClientTransport.connectionLost(self, reason)
        self.connectionClosed(reason)

    def connectionSecure(self):
        self.requestService(self.userAuthObject)

    def connectionClosed(self, reason):
        self.deferred.called or self.deferred.callback(reason)
