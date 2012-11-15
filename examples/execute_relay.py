"""Example that run local and remote process concurrently and relay output.

A local process is started concurrently with a remote process.
All output from the two processes are relayed to the parent process (the
process executing this script).

The sub-processes we start is the execution of a simple python script that
print to stdout and stderr and exit with a exit code.
"""

import sys
from getpass import getpass
from twisted.internet import reactor, defer
from twisted.internet.protocol import ProcessProtocol
from carnifex.localprocess import LocalProcessInductor
from carnifex.sshprocess import SSHProcessInductor


# Setup parameters for SSH to connect to localhost with current user
remote_host, remote_port = 'localhost', 22
remote_user, remote_password = None, getpass()


# Describe a command to run (a simple python script that prints to stdout
# and stderr)
command = ["python", "-c", r"""
import sys
sys.stdout.write('standard output\n')    # Write stdout data
sys.stderr.write('standard error\n')     # Write stderr data
exit(42)                                 # We exit with exit code 42
"""]


class RelayProtocol(ProcessProtocol):
    """Trivial process protocol to relay stdout and stderr and report exit code
    from the child processes to our parent process (the process executing
    this program).
    """

    def __init__(self, data_precursor=''):
        """Set up the relay to map stdout and stderr to our parent process
        @param data_precursor: A precursor to tag where the data came from.
        """
        self.outReceived = lambda data: sys.stdout.write(data_precursor+data)
        self.errReceived = lambda data: sys.stderr.write(data_precursor+data)
        # Set up a deferred that will be triggered when the process ends
        self.deferred = defer.Deferred()

    def processEnded(self, reason):
        # Trigger the deferred with the exit code of the process
        exit_code = reason.value.exitCode
        self.deferred.callback(exit_code)


# Set up a local process inductor and run the process through our relay protocol
local_inductor = LocalProcessInductor(reactor)
local_protocol = RelayProtocol('Local process: ')
remote_process = local_inductor.execute(local_protocol, command)

# Set up a remote process inductor and run the same command
remote_inductor = SSHProcessInductor(reactor, remote_host, remote_port)
remote_inductor.setCredentials(remote_user, remote_password)
remote_protocol = RelayProtocol('Remote process: ')
remote_process = remote_inductor.execute(remote_protocol, command)

# Gather the results from the local and remote process
results = defer.DeferredList([local_protocol.deferred,
                              remote_process, remote_protocol.deferred],
                             fireOnOneErrback=True)
@results.addCallback
def get_exit_codes(deferredListResults):
    global exit_codes
    exit_codes = []
    for _, exit_code in deferredListResults:
        exit_codes.append(exit_code)

# Make sure we stop the twisted reactor when the processes are done
results.addBoth(lambda _: reactor.stop())
reactor.run()

# Relay the exit codes
exit(exit_codes[0] or exit_codes[1])
