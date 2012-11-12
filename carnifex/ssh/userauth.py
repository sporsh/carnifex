"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

from twisted.internet import defer
from twisted.conch.ssh.userauth import SSHUserAuthClient

class AutomaticUserAuthClient(SSHUserAuthClient):
    """User Auth Client that automatically authenticate using stored credentials.
    """

    def __init__(self, user, connection,
                 password=None, privateKey=None, publicKey=None):
        SSHUserAuthClient.__init__(self, user, connection)
        self.password = password
        self.privateKey = privateKey
        self.publicKey = publicKey

    def getGenericAnswers(self, name, instruction, prompts):
        """Called when the server requests keyboard interactive authentication
        """
        responses = []
        for prompt, _echo in prompts:
            password = self.getPassword(prompt)
            responses.append(password)

        return defer.succeed(responses)

    def getPassword(self, prompt=None):
        if not self.password:
            return None # Return none to indicate we do not want to retry
        return defer.succeed(self.password)

    def getPrivateKey(self):
        if self.privateKey:
            return defer.succeed(self.privateKey)
        return defer.fail(None)

    def getPublicKey(self):
        if not self.publicKey:
            return None
        return defer.succeed(self.publicKey)
