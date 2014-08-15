import time

import zmq


def main(service_addr, service_time):
    ctx = zmq.Context()
    sock = zmq.Socket(ctx, zmq.REP)

    sock.bind(service_addr)

    def listen(service_time=service_time):
        if sock.poll(timeout=100):
            request = sock.recv()
            if request == 'start':
                sock.send('started')
                time.sleep(service_time)
            elif request == 'notify_completion':
                sock.send('completed')
            else:
                sock.send('error')

    while True:
        listen(service_time)


if __name__ == '__main__':
    import sys

    if len(sys.argv) not in (2, 3):
        print >> sys.stderr, ('usage: %s <service bind addr> [service_time=1.]'
                              % sys.argv[0])
    else:
        if len(sys.argv) < 3:
            service_time = 1.
        else:
            service_time = float(sys.argv[2])
        main(sys.argv[1], service_time)
