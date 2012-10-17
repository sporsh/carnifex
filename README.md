Carnifex
========

Carnifex abstracts execution and running processes weither it be locally,
or remotely on another machine. Current implementations support local sub
processes and remote processes over ssh.


Inductor - control execution
----------------------------

Using Twisted framweork, it enables you to control execution of the process
with a process protocol. Define a protocol that handle communication with
the process, and carnifex will take care of running the process both locally
and/or remotely.

To create a inductor that will execute processes on the local machine:

>>> inductor = carnifex.LocalProcessInductor(reactor)

Similarly, a inductor that will execute processes on a remote machine:

>>> inductor = carnifex.SSHProcessInductor(reactor, 'remotehost', 22)

And for to run a command, the same api can be used for all types of inductors:

>>> # Simple example getting the exit code of the `false` command (should be 1)
>>> inductor.getExitCode('false')

>>> # Simple example getting output from echo
>>> argv = ('echo', 'hello world')
>>> inductor.getOutput(**commandArgs)

>>> # Slightly more complex example getting stdout, stderr and exit code from a python script
>>> commandArgs = carnifex.parseCommandLine("""\
... python -c "import sys
... sys.stdout.write('hello from python')
... """
...
>>> inductor.run(**commandArgs)


Endpoint - use a process as network transport
---------------------------------------------

A endpoint adaption is provided to make it possible to connect any Twisted
network protocol to a process. This mean you can have a process act as if
it is the network transport layer. This is ecpecially useful for captured
network data or live interaction via network tools like netcat.
