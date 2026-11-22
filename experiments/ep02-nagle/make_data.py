"""Build ep02/data.json for the video from the measured files in this folder (results.json, latency_*.csv, trace.txt)."""
import csv, json, pathlib, re
HERE = pathlib.Path(__file__).resolve().parent
res = json.loads((HERE / "results.json").read_text())
lat = {v: [float(r[1]) for r in csv.reader((HERE / f"latency_{v}.csv").open())] for v in "ABCD"}
ports = {"47001": "A", "47002": "B", "47003": "C", "47004": "D"}
pk = {v: [] for v in "ABCD"}
for line in (HERE / "trace.txt").read_text().splitlines():
    m = re.match(r"(\d+\.\d+) IP 127\.0\.0\.1\.(\d+) > 127\.0\.0\.1\.(\d+): Flags \[([^\]]+)\].* length (\d+)", line)
    if not m: continue
    t, sp, dp, fl, n = float(m[1]), m[2], m[3], m[4], int(m[5])
    v = ports.get(dp) or ports.get(sp)
    pk[v].append({"t": t, "dir": "c2s" if dp in ports else "s2c", "flags": fl, "len": n})
def requests(v):
    """Split a variant's packets into requests: each starts with a client data packet after an idle gap."""
    out, cur = [], None
    for p in pk[v]:
        if "S" in p["flags"] or "F" in p["flags"]: continue
        if p["dir"] == "c2s" and p["len"] > 0 and (cur is None or p["t"] - cur[-1]["t"] > 0.1):
            cur = []; out.append(cur)
        if cur is not None: cur.append(p)
    return [[{"us": round((p["t"] - r[0]["t"]) * 1e6), "dir": p["dir"], "len": p["len"]} for p in r] for r in out]
trace = {v: requests(v) for v in "ABCD"}
data = {"results": res, "latA": [round(x, 3) for x in lat["A"]], "latB": [round(x, 4) for x in lat["B"]],
        "trace": trace,
        "trace_lines_A": [l for l in (HERE / "trace.txt").read_text().splitlines() if ".47001" in l][9:15]}
(HERE.parent.parent / "ep02" / "data.json").write_text(json.dumps(data))
for v in "ABCD":
    print(v, [[(p["us"], p["dir"], p["len"]) for p in r] for r in trace[v][:2]])
