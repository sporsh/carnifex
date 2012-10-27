# Carnifex

Carnifex provides an api for executing commands. The processes can be started locally or remotely on another machine with minimal effort for the user.
Current implementations support local sub processes and remote processes over ssh.

## Running commands and starting processes
All the fun is abstracted in what is called the Process Inductor.
It lets you 'induce' processes locally or remote with `run`, `getOutput`, `getExitCode` and the slightly more complex method `execute`.

It's super simple to use:
```python
inductor.run('echo "hello world")
```
This will work exactly the same for local and remote processes.
You will gather stdout, stderr, exit code or signal if the process was terminated

Here is a more complex example:
```python
complex_command_line = """\
python -c
"import sys
sys.stdout.write('hello stdout\\n')
sys.stderr.write('whops, we err\\'d'\\n)
exit(1)
"
"""
inductor.run(complex_command_line)
```

Which will launch a python process that outputs `hello stdout` on standard output, 
`whops, we err'd` on standard error, and exits with exitcode `1`

* `Inductor.run`: execute and a command and run the process until completed (or terminated), then return stdout, stderr and exit code of the process
* `Inductor.getOutput`: just like run, but only gather output (stdout and/or stderr can be specified)
* `Inductor.getExitCode`: like the other two, but only return the exit code of the process
* `Inductor.execute`: execute the command and let you bind a Twisted ProcessProtocol to the process to further control how the process is run. You can have the ProcessProtocol interact with the file descriptors of the process and send signals to terminate it.

All of these ways of running processes can be used in the same way both for starting a local sub process, or a remote process on another machine.


### Setting up a local processes inductor
For running commands locally, you will use a `LocalProcessInductor`:
```python
from twisted.internet import reactor
inductor = carnifex.LocalProcessInductor(reactor)
```

### Setting up a remote processes inductor
It is just as simple for remote process inductor, but you can in addition specify credentials for users
```python
from twisted.internet import reactor
inductor = carnifex.SSHProcessInductor(reactor, 'localhost', 22)
inductor.addCredentials(user='remoteuser', password='remotepass')
```
You can set up credentials for different users by using the `addCredentials` method, and both `password` and `privateKey`, `publicKey` authentication is possible.
By using `addKnownHost` you can choose to only allow connecting to servers with keys you have validated as well!


To run a remote process as a different user, simply specify the `uid` attribute:
```python
inductor.run('echo "hello world", uid='remoteuser')
```

## Endpoint - use a process as network transport

A endpoint adaption is provided to make it possible to connect any Twisted
network protocol to a process. This mean you can have a process act as if
it is the network transport layer. This is ecpecially useful for captured
network data or live interaction via network tools like netcat.
