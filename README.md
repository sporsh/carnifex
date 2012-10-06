carnifex
========

Enable execution of processes locally or on a remote machine (eg. over SSH) transparantly with the same API.
Carnifex is based on python twisted, and extend many of twisted's classes.


Endpoints
--------

An endpoint object is provided to enable connecting a twisted Protocol to a process.
This makes it possible to hook a network protocol to the process.

An example use case is to connect a network protocol to a netcat process (local or remote).
For example you can start a netcat process on a remote machine and connect a server or client protocol to it.
This will enable you to do forwarding/tunneling over ssh even if the ssh server does not allow it directly.
