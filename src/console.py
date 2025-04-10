#!/usr/bin/python3

""" Console component for access to Siren functionality. """

import code
import errno
import io
import socket
import sys
import threading
import time


def dump_trace():
    """ Utility function to dump the trace of all active threads. """
    import faulthandler
    FILE = '/tmp/trace.log'
    f = open(FILE, 'w')
    faulthandler.dump_traceback(file=f)
    f.close()
    f = open(FILE, 'r')
    data = f.read()
    f.close()
    print(data)


class OutputCapture(io.StringIO):
    """ Interceptor for stdout or stderr to redirect to a socket. """

    def __init__(self, conn, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conn = conn

    def write(self, text):
        self._conn.send(text.encode())
        super().write(text)
        sys.__stdout__.write(text)


class Console:
    """ Console over TCP/IP. """

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._thread = None
        self._socket = None

    def listen(self, locals={}):
        """ Open a port and crete a console connection.

        This function will not block, and will spawn a thread to run the
        console.  To close the console, delete the `Console` object.

        Args:
            locals: Dictionary of name/values to include in the interactive
                    console.
        """

        locals['dump_trace'] = dump_trace
    
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

        def thread():
            self._socket.bind((self._host, self._port))
            self._socket.listen()
            print('Console listening on %s:%d' % (
                self._host, self._port))
            conn, addr = self._socket.accept()
            orig_stdout = sys.stdout
            orig_stderr = sys.stderr
            try:
                with conn:
                    print("Connection by", addr)
                    sys.stdout = OutputCapture(conn)
                    sys.stderr = OutputCapture(conn)
                    console = code.InteractiveConsole(locals=locals)
                    conn.send(">>> ".encode())
                    while True:
                        data = conn.recv(1024).decode()
                        if len(data) == 0:
                            break
                        need_more = console.push(data.rstrip())
                        if need_more:
                            conn.send("... ".encode())
                        else:
                            conn.send(">>> ".encode())
            finally:
                self._socket.shutdown(1)
                self._socket.close()
                self._socket = None
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr
                print("Client disconnected.")
        self._thread = threading.Thread(target=thread)
        self._thread.start()

    def run_server(self, locals={}):
        """ Blocking form of `listen()`. """
        self.listen(locals)
        self._thread.join()

    def __del__(self):
        if self._socket:
            self._socket.shutdown(1)
            self._socket.close()
        if self._thread:
            self._thread.join()


if __name__ == '__main__':
    c = Console('127.0.0.1', 12345)
    while True:
        c.run_server({'c': c})
