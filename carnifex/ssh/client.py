from twisted.internet.protocol import ClientFactory
from twisted.conch.ssh.transport import SSHClientTransport


class SSHClientFactory(ClientFactory):
    def __init__(self, verifyHostKey, userAuthObject):
        self.verifyHostKey = verifyHostKey
        self.userAuthObject = userAuthObject

    def buildProtocol(self, addr):
        trans = SSHClientTransport()
        trans.verifyHostKey = self.verifyHostKey
        trans.connectionSecure = lambda: trans.requestService(self.userAuthObject)
        return trans
