"""Measure the Nagle + delayed-ACK stall on loopback.

A client sends each request as a small header then a small body and waits for a 4-byte reply.
Four variants, 400 requests each on one persistent connection:
  A two writes, default socket options
  B two writes, TCP_NODELAY on the client (Nagle off)
  C one write (header and body joined), default options
  D two writes, default client; the server sets TCP_QUICKACK after every read (delayed ACK off)
Run: python3 nagle.py   -> results.json and results.csv beside this file
"""
import csv, json, pathlib, socket, statistics, threading, time

HERE = pathlib.Path(__file__).resolve().parent
HEADER, BODY, N = b"H" * 8, b"B" * 100, 400

def recv_exact(sock, n, quickack=False):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if quickack:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        if not chunk:
            raise ConnectionError
        buf += chunk
    return buf

def server(listener, quickack):
    conn, _ = listener.accept()
    with conn:
        try:
            while True:
                recv_exact(conn, len(HEADER) + len(BODY), quickack)
                conn.sendall(b"DONE")
        except ConnectionError:
            pass

def run(variant):
    two_writes = variant != "C"
    listener = socket.socket(); listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0)); listener.listen(1)
    th = threading.Thread(target=server, args=(listener, variant == "D"), daemon=True); th.start()
    c = socket.create_connection(listener.getsockname())
    if variant == "B":
        c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    lat = []
    for _ in range(N):
        t0 = time.perf_counter()
        if two_writes:
            c.sendall(HEADER); c.sendall(BODY)
        else:
            c.sendall(HEADER + BODY)
        recv_exact(c, 4)
        lat.append((time.perf_counter() - t0) * 1000)
    c.close(); th.join(2); listener.close()
    return lat

results = {}
for v in "ABCD":
    lat = run(v); s = sorted(lat)
    results[v] = {"n": N, "median_ms": round(statistics.median(lat), 3), "p10_ms": round(s[N // 10], 3),
                  "p90_ms": round(s[N * 9 // 10], 3), "max_ms": round(s[-1], 3), "total_s": round(sum(lat) / 1000, 3),
                  "first_20_ms": [round(x, 2) for x in lat[:20]], "share_over_30ms": round(sum(x > 30 for x in lat) / N, 3)}
    with open(HERE / f"latency_{v}.csv", "w", newline="") as f:
        csv.writer(f).writerows([[i, round(x, 4)] for i, x in enumerate(lat)])
(HERE / "results.json").write_text(json.dumps(results, indent=1))
for v, r in results.items():
    print(v, {k: r[k] for k in ("median_ms", "p10_ms", "p90_ms", "max_ms", "total_s", "share_over_30ms")})
print("first 20 of A:", results["A"]["first_20_ms"])
