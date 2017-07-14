

![https://ci.appveyor.com/api/projects/status/github/wheeler-microfluidics/zeromq_service_plugin?branch=master&svg=true](https://ci.appveyor.com/api/projects/status/github/wheeler-microfluidics/zeromq_service_plugin?branch=master&svg=true)


![https://ci.appveyor.com/api/projects/status/github/wheeler-microfluidics/zeromq_service_plugin?branch=master&svg=true](https://ci.appveyor.com/api/projects/status/github/wheeler-microfluidics/zeromq_service_plugin?branch=master&svg=true)


![https://ci.appveyor.com/api/projects/status/github/wheeler-microfluidics/zeromq_service_plugin?branch=master&svg=true](https://ci.appveyor.com/api/projects/status/github/wheeler-microfluidics/zeromq_service_plugin?branch=master&svg=true)
# ZeroMQ service MicroDrop plugin #

This project implements a [MicroDrop][1] [plugin][2] to interface with a
[ZeroMQ][3] service.

The basic idea is to have a service exposed through a ZeroMQ interface,
responding on a `zmq.REP` socket to the following two messages:

 - `start` -> `started`
 - `notify_completion` -> `completed`

This provides a basic inter-process method for starting a service,
followed by a notification upon completion.  The plugin provides a
timeout option for each step in the DMF protocol to limit the amount of
time spent waiting for a service to complete.

__NB__ As of this commit, the MicroDrop app seems to freeze in the case
where the service times out, after the error message indicating the
protocol has failed is displayed.  This is likely due to threading
issues, which will be resolved after the plug-ins are ported to run in
separate processes.

[1]: http://microfluidics.utoronto.ca/microdrop
[2]: https://software.sandia.gov/trac/pyutilib/export/1831/pyutilib.component.doc/trunk/doc/plugin/pca.pdf
[3]: http://zeromq.org
