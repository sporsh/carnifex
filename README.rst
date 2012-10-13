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


Endpoint - use a process as network transport
---------------------------------------------

A endpoint adaption is provided to make it possible to connect any Twisted
network protocol to a process. This mean you can have a process act as if
it is the network transport layer. This is ecpecially useful for captured
network data or live interaction via network tools like netcat.
