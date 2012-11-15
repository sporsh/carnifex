"""
@author: Geir Sporsheim
@license: see LICENCE for details
"""

from twisted.internet.protocol import ProcessProtocol
class ProcessContext(object):
    def __init__(self, inductor, *args, **kwargs):
        self.inductor = inductor

    def __enter__(self):
        self.process = self.inductor.execute
        return self.process

    def __exit__(self):
        pass

class InteractiveProcess(ProcessProtocol):
    def connectionMade(self):
        ProcessProtocol.connectionMade(self)

    def processEnded(self, reason):
        ProcessProtocol.processEnded(self, reason)
