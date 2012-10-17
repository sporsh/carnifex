# Carnifex

Carnifex provides an api for executing commands. The processes can be started locally or remotely on another machine with minimal effort for the user.
Current implementations support local sub processes and remote processes over ssh.

## The Process Inductor
The process inductor classes abstract execution of processes. It lets you induce processes via `run`, `getOutput`, `getExitCode` and the slightly more complex method `execute` processes.

* `Inductor.run`: execute and a command and run the process until completed (or terminated), then return stdout, stderr and exit code of the process
* `Inductor.getOutput`: just like run, but only gather output (stdout and/or stderr can be specified)
* `Inductor.getExitCode`: like the other two, but only return the exit code of the process
* `Inductor.execute`: execute the command and let you bind a Twisted ProcessProtocol to the process to further control how the process is run. You can have the ProcessProtocol interact with the file descriptors of the process and send signals to terminate it.

All of these ways of running processes can be used in the same way both for starting a local sub process, or a remote process on another machine.

### Local processes
```python
import carnifex
from twisted.internet import reactor
inductor = carnifex.LocalProcessInductor(reactor)
```

### Remote processes
```python
import carnifex
from twisted.internet import reactor
inductor = carnifex.SSHProcessInductor(reactor, 'localhost', 22)
```

### Building commands

To start a process with carnifex, you need to supply at least one parameter, which is the `executable` to launch.
This is the bare minimum, and does not give you any flexibility to specify arguments to the executable. To do that, you'll need to specify one more argument `args`, which basically is the argument list that is passed to the process. The argument list consist of the name of the process and subsequent arguments to it. The name is usually the same as the `executable`

One usual use case is the following
```python
args = ['echo', 'hello world']
inductor.run(args[0], args)
```

This can be a quite tedious way of specifying the command line to run, so we have the convenience method `parseCommandLine` to assist us. `parseCommandLine` will take a command line string - like you would type it in a shell - and parse it to a dictionary, suitable for the keyword arguments to the inductor methods.

Here is a more complex example, to illustrate the usefulness of the `parseCommandLine` function:
```python
complex_command_line = """\
python -c
"import sys
sys.stdout.write('hello stdout\\n')
sys.stderr.write('whops, we err\\'d'\\n)
exit(1)
"
"""
exec_args = parseCommandLine(complex_command_line)
inductor.run(**exec_args)
```

Which will launch a python process that outputs `hello stdout` on standard output, 
`whops, we err'd` on standard error, and exits with exitcode `1`


## Endpoint - use a process as network transport

A endpoint adaption is provided to make it possible to connect any Twisted
network protocol to a process. This mean you can have a process act as if
it is the network transport layer. This is ecpecially useful for captured
network data or live interaction via network tools like netcat.
