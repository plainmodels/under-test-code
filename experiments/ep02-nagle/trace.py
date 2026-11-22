"""Send a few requests on a fixed loopback port so tcpdump can record the packets.

    python3 trace.py A 47001     two writes, default sockets (the stall)
    python3 trace.py C 47003     one write, default sockets
Variants as in nagle.py. Capture with:  tcpdump -i lo -nn -tt 'tcp portrange 47001-47004'
"""
import socket, sys, threading, time

HEADER, BODY = b"H" * 8, b"B" * 100
variant, port, n = sys.argv[1], int(sys.argv[2]), 5

def recv_exact(sock, k, quickack=False):
    buf = b""
    while len(buf) < k:
        chunk = sock.recv(k - len(buf))
        if quickack:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        if not chunk:
            raise ConnectionError
        buf += chunk
    return buf

def server(listener):
    conn, _ = listener.accept()
    with conn:
        try:
            while True:
                recv_exact(conn, len(HEADER) + len(BODY), variant == "D")
                conn.sendall(b"DONE")
        except ConnectionError:
            pass

listener = socket.socket(); listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("127.0.0.1", port)); listener.listen(1)
th = threading.Thread(target=server, args=(listener,), daemon=True); th.start()
c = socket.create_connection(("127.0.0.1", port))
if variant == "B":
    c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
for i in range(n):
    time.sleep(0.2)                      # idle gap so each request is easy to tell apart in the trace
    t0 = time.perf_counter()
    if variant == "C":
        c.sendall(HEADER + BODY)
    else:
        c.sendall(HEADER); c.sendall(BODY)
    recv_exact(c, 4)
    print(f"{variant} request {i}: {(time.perf_counter() - t0) * 1000:.3f} ms")
c.close(); th.join(2); listener.close()
