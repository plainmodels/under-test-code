"""Write ep02/storyboard.json. Kept as a script so the beats stay readable and diffable."""
import json, pathlib
B = []
def beat(id, chapter, scene, p, text, visual, say=None, sfx=None):
    b = {"id": id, "chapter": chapter, "scene": scene, "p": p, "text": text, "visual": visual}
    if "Nagle" in (say or text): say = (say or text).replace("Nagle", "Naygle")   # the voice otherwise says it two ways
    if say: b["say"] = say
    if sfx: b["sfx"] = sfx
    B.append(b)

beat("b01", "", "latency", {"mode": "flat"},
     "Here are four hundred requests between two programs on the same laptop. No network cable. No Wi-Fi. The data never leaves the machine. Each one takes forty-one milliseconds.",
     "all 400 measured latencies of variant A, drawn point by point", sfx=[[0.8, "hit"]])
beat("b02", "", "latency", {"mode": "band"},
     "Not about forty. Forty-one, every time, to within a fraction of a millisecond. Now I change one line of the client. Same machine, same server, same requests.",
     "zoom on the band between the 10th and 90th percentile")
beat("b03", "", "latency", {"mode": "log", "head": "the same 400 requests, before and after one changed line"},
     "Thirty microseconds. That is fourteen hundred times faster. Four hundred requests went from sixteen seconds to fourteen thousandths of a second.",
     "both runs on a logarithmic scale, with totals", sfx=[[0.3, "whoosh"]])
beat("b04", "", "title", {"title": ["Why your fast network call", "takes exactly 40 milliseconds"], "sub": "two good ideas from the 1980s, waiting for each other"},
     "Why your fast network call takes exactly 40 milliseconds.", "title card",
     say="Why your fast network call takes exactly forty milliseconds.", sfx=[[0.1, "hit"]])
beat("b05", "The question", "bullets", {"head": "By the end you will be able to", "items": ["Name the two rules that collide", "Reproduce the stall on your own machine", "Choose the right fix out of three"]},
     "Nothing was broken in the slow version. No packet was lost. Two parts of TCP were each doing their job correctly, and politely waiting for each other. By the end of this video you will know which two, you will be able to reproduce the stall yourself, and you will know which of the three possible fixes is the right one.",
     "three outcomes", say="Nothing was broken in the slow version. No packet was lost. Two parts of T C P were each doing their job correctly, and politely waiting for each other. By the end of this video you will know which two, you will be able to reproduce the stall yourself, and you will know which of the three possible fixes is the right one.")

ch = "1 · Don't send tiny packets"
beat("b06", ch, "packet", {"data": 1, "head": "one keystroke, as it crosses the network", "big": "“This 4000% overhead”", "src": "John Nagle, RFC 896, 6 January 1984"},
     "In 1984, an engineer named John Nagle described a real problem. A person typing over a remote connection sends one keystroke at a time. Each keystroke is one byte. But every packet carries forty bytes of headers. One byte of cargo in a forty-one byte box. He called it four thousand percent overhead.",
     "a packet drawn to scale: 40 header bytes, 1 data byte", sfx=[[0.62, "tick"]])
beat("b07", ch, "quote", {"lines": ["…inhibit the sending of new TCP segments", "when new outgoing data arrives from the user", "if any previously transmitted data", "on the connection remains unacknowledged."], "hl": [3], "src": "RFC 896 · “The solution to the small-packet problem”"},
     "His fix is one sentence, and it is still in your operating system. If you have already sent data that has not been acknowledged yet, do not send another small packet.",
     "the rule, quoted from RFC 896")
beat("b07a", ch, "nagle", {},
     "Hold the new data until the acknowledgement comes back, and then send everything you have collected as one packet.",
     "bytes collecting at the sender and leaving together", sfx=[[0.74, "whoosh"]])
beat("b08", ch, "quote", {"lines": ["This inhibition is to be unconditional;", "no timers, tests for size of data received,", "or other conditions are required."], "hl": [1], "src": "RFC 896", "foot": "fast network: short wait · slow network: bigger batches"},
     "Notice what the rule does not need. No timer. No tuning. If the network is fast, acknowledgements come back fast and you barely wait. If it is slow, you naturally batch more. It is an elegant rule.",
     "the 'no timers' sentence from RFC 896")

ch = "2 · Don't send empty acknowledgements"
beat("b09", ch, "packet", {"data": 0, "head": "an acknowledgement on its own", "big": "all header, no cargo"},
     "Now the other side of the connection. Every time data arrives, the receiver owes the sender an acknowledgement. But an acknowledgement on its own is another packet that is all header and no cargo.",
     "an ACK packet: 40 header bytes, 0 data bytes")
beat("b10", ch, "quote", {"lines": ["A TCP SHOULD implement a delayed ACK,", "but an ACK should not be excessively delayed;", "in particular, the delay MUST be", "less than 0.5 seconds…"], "hl": [0, 3], "src": "RFC 1122, section 4.2.3.2, October 1989"},
     "So the receiver waits a moment. If the application is about to send a reply anyway, the acknowledgement can ride along inside the reply for free. The standard says a TCP should do this, and that the delay must be less than half a second.",
     "RFC 1122 section 4.2.3.2", say="So the receiver waits a moment. If the application is about to send a reply anyway, the acknowledgement can ride along inside the reply for free. The standard says a T C P should do this, and that the delay must be less than half a second.")
beat("b11", ch, "calc", {"label": "linux · include/net/tcp.h", "code": "#define TCP_DELACK_MIN  ((unsigned)(HZ/25))", "hl": "HZ/25", "steps": ["HZ = 1000 ticks per second on this kernel", "1000 / 25 = 40 ticks"], "big": "40 ms"},
     "Linux picks its own minimum for that wait. It is one line of the kernel source: the clock rate divided by twenty-five. On this kernel the clock ticks a thousand times a second. A thousand over twenty-five. Forty milliseconds.",
     "the kernel source line and the arithmetic", sfx=[[0.85, "hit"]])
beat("b12", ch, "statement", {"lines": ["Nagle's rule", "+ a delayed acknowledgement", "+ one innocent habit"], "accent": [2], "sub": "= 40 ms"},
     "There is our number. But a delayed acknowledgement alone does not hurt anybody. To get the stall, you need both ideas, and one innocent habit in the application.",
     "the three ingredients")

ch = "3 · The collision"
beat("b13", ch, "codehl", {"label": "nagle.py · the client (reformatted)", "lines": ["HEADER, BODY = b\"H\" * 8, b\"B\" * 100", "", "for _ in range(400):", "    t0 = time.perf_counter()", "    c.sendall(HEADER)", "    c.sendall(BODY)", "    recv_exact(c, 4)"], "hl": [4, 5], "at": 0.42, "caption": "one request, sent as two small writes"},
     "Here is the habit. My client builds a request in two parts: a small header, then a small body. And it sends them with two separate writes. Header first. Then body. Lots of real code does exactly this.",
     "the client loop; the two sendall calls highlighted")
beat("b14", ch, "seq", {"stage": 1},
     "Follow the packets. First write: the header. Nothing is waiting to be acknowledged, so Nagle's rule lets it go immediately.",
     "sequence diagram: the header crosses", sfx=[[0.3, "whoosh"]])
beat("b15", ch, "seq", {"stage": 2},
     "Second write: the body. Now there is unacknowledged data on the connection: the header. Nagle's rule says hold. The body sits in the client's kernel, waiting for an acknowledgement.",
     "the body parked on the client side")
beat("b16", ch, "seq", {"stage": 3},
     "On the server, the header has arrived. The server owes an acknowledgement. But it has nothing to say yet. It cannot answer a request it has only half received. So it does the efficient thing, and waits, hoping to attach the acknowledgement to a reply.",
     "the server holds its acknowledgement")
beat("b17", ch, "seq", {"stage": 4},
     "The client is waiting for an acknowledgement before it sends the body. The server is waiting for the body before it sends anything. Each is waiting for the other. Nobody is wrong.",
     "both sides frozen while a clock counts up")
beat("b18", ch, "seq", {"stage": 5},
     "Forty milliseconds later the server's timer runs out. It gives up and sends a bare acknowledgement. That releases the body. The server replies at once. The whole exchange took forty-one milliseconds, of which forty were both sides being polite.",
     "timer expires; ACK, body and reply cross", sfx=[[0.26, "tick"], [0.76, "hit"]])
beat("b18a", ch, "trace", {"variant": "A", "label": "tcpdump -i lo · one slow request · times from the first packet", "gap": 1, "gapText": "40.6 ms of silence", "hot": [1], "foot": "the body left 15 µs after the acknowledgement arrived"},
     "That is the theory. Here is what the kernel actually sent. I recorded every packet of one slow request. The header leaves at time zero. Then nothing, for forty point six milliseconds. Then a bare acknowledgement. And fifteen microseconds after it, the body.",
     "the real packet trace of one stalled request", sfx=[[0.5, "tick"]])
beat("b18b", ch, "terminal", {"label": "strace -T · the client's three calls for one slow request · shortened", "big": True, "lines": ["sendto(5, \"HHHHHHHH\", 8, ...)    = 8     <0.000183>", "sendto(5, \"BBBB\"..., 100, ...)   = 100   <0.000008>", "recvfrom(5, \"DONE\", 4, ...)      = 4     <0.042185>"], "hl": "<0.042185>", "note": "last column: seconds spent inside each call"},
     "One more thing the recording explains. Your program never sees the body being held. Both writes return within microseconds: the kernel accepts the data and says nothing. The whole forty milliseconds shows up in the read. So when you profile it, the server looks slow. It is not.",
     "the client's system calls with the time spent in each")

ch = "4 · Proving it"
beat("b19", ch, "variants", {"show": ["A"]},
     "An explanation like that is easy to believe and easy to get wrong, so here are the experiments that test it. If the stall is really those two rules meeting, then removing either one should remove the stall, and so should removing the habit.",
     "the four variants, results hidden")
beat("b20", ch, "variants", {"show": ["A", "B"]},
     "Turn off Nagle's rule on the client, with the option TCP_NODELAY. The body no longer waits. Thirty microseconds.",
     "variant B revealed", say="Turn off Nagle's rule on the client, with the option T C P no delay. The body no longer waits. Thirty microseconds.", sfx=[[0.6, "tick"]])
beat("b21", ch, "variants", {"show": ["A", "B", "D"]},
     "Leave Nagle on, but tell the server to acknowledge immediately. The stall goes away again. Thirty-two microseconds.",
     "variant D revealed", sfx=[[0.6, "tick"]])
beat("b21a", ch, "trace", {"variant": "D", "label": "tcpdump -i lo · two writes, server acknowledges at once", "hot": [1], "foot": "the same six packets, without the wait", "footColor": "good"},
     "In the packet trace, the acknowledgement now comes back after ninety-one microseconds instead of forty milliseconds, and the body follows nine microseconds later.",
     "the real packet trace with quick acknowledgement on the server")
beat("b22", ch, "variants", {"show": ["A", "B", "D", "C"]},
     "Or change nothing about the sockets, and simply join the header and body and send them with one write. Nineteen microseconds. The fastest of all.",
     "variant C revealed", sfx=[[0.6, "tick"]])
beat("b22a", ch, "trace", {"variant": "C", "label": "tcpdump -i lo · one request sent as a single write", "foot": "3 packets, where the slow version needed 6", "footColor": "good"},
     "And the packet trace shows why. One write is one packet. And look at the reply: the acknowledgement rides back inside it, exactly as the designers intended. Three packets, where the slow version needed six.",
     "the real packet trace of the single-write request")
beat("b23", ch, "variants", {"show": ["A", "B", "D", "C"], "all": True, "head": "remove any one ingredient and the stall is gone"},
     "Three different changes, each removing one ingredient, each removing the stall. That is as close to proof as one laptop gets. It is one machine and one kernel version, so I would like to know what yours says.",
     "all four results with the ingredient each one removes")
beat("b24", ch, "first20", {},
     "One loose end, and I want to be honest about it. In the slow run, the very first request was fast: a quarter of a millisecond. The packet trace shows what happened: on that first request, the server acknowledged the header immediately. The manual describes a quick-acknowledgement mode that the kernel enters and leaves on its own. I have not traced why it applied there, so I am not going to claim I have.",
     "first 20 latencies of variant A; the first one marked; the manual's sentence")

ch = "5 · Which fix is the right one"
beat("b25", ch, "quote", {"lines": ["This flag is not permanent, it only enables", "a switch to or from quickack mode.", "…", "This option should not be used", "in code intended to be portable."], "hl": [0, 3], "src": "Linux manual, tcp(7), TCP_QUICKACK"},
     "So which fix should you use? The quick-acknowledgement option is the weakest. The manual says it is not permanent: the kernel can switch back. And it says not to use it in portable code.",
     "tcp(7) on TCP_QUICKACK")
beat("b26", ch, "trace", {"variant": "B", "label": "tcpdump -i lo · two writes with TCP_NODELAY", "hot": [0, 1], "foot": "no wait, but still two small packets"},
     "TCP_NODELAY is the well-known fix, and it works. But look at what it does. The header and the body still travel as two packets. You have removed the wait by accepting the waste that Nagle was trying to prevent.",
     "the real packet trace with TCP_NODELAY", say="T C P no delay is the well-known fix, and it works. But look at what it does. The header and the body still travel as two packets. You have removed the wait by accepting the waste that Nagle was trying to prevent.")
beat("b27", ch, "quote", {"lines": ["If you do send, send, reply,", "there's a delay."], "hl": [0], "src": "John Nagle, writing on Hacker News, 14 February 2015", "foot": "build the whole message, then write it once"},
     "The best fix is the one that needed no socket option at all. Build the whole message, then write it once. John Nagle made the same point himself, thirty years later: if you do send, send, reply, there's a delay. In his view the real culprit is the delayed acknowledgement, not his rule.",
     "Nagle's own words, 2015")
beat("b28", ch, "compare", {"left": {"head": "In your code", "items": ["Build the whole message", "Write it once", "One packet, nothing to wait for"]}, "right": {"head": "On the socket", "items": ["Set TCP_NODELAY as well", "A stray small write then costs", "one packet, not 40 ms"]}, "foot": "Fix the writes first. The option is the safety net."},
     "In practice you do both. Buffer in your own code so that each message is one write, and set no delay so that a mistake elsewhere costs you a packet, not forty milliseconds.",
     "both recommendations side by side")

ch = "What to remember"
beat("b29", ch, "bullets", {"head": "Three things", "numbered": True, "items": ["A steady 40 ms on Linux: suspect this first", "Two small writes + Nagle + delayed ACK", "Fix the writes first, the option second"]},
     "Three things. First: a latency that sits at almost exactly forty milliseconds on Linux should make you suspect this before anything else. Second: it takes two small writes, Nagle's rule and a delayed acknowledgement, all three together. Third: fix the writes first, and the option second.",
     "three numbered points")
beat("b30", ch, "terminal", {"label": "output shortened to the medians", "big": True, "lines": ["$ python3 nagle.py", "A  median 41.005 ms", "B  median  0.029 ms", "C  median  0.019 ms", "D  median  0.032 ms"], "hl": "41.005 ms"},
     "The script that produced every number here is about sixty lines of Python. Run it, and see your own forty-one milliseconds.",
     "the command and its medians")
beat("b31", "", "endcard", {"next_label": "Next on Under Test", "next": ["Your laptop has two kinds of core.", "Does Linux use them well?"]},
     "Thanks for watching. This is Under Test: real systems, measured. Next time: your laptop has two kinds of processor core. Does Linux use them well?",
     "end card with space for YouTube end-screen elements")

sb = {"episode": "ep02", "title": "Why your fast network call takes exactly 40 milliseconds", "voice": "af_heart", "lang": "en-us", "speed": 0.93, "gap": 0.6, "tail": 11, "beats": B}
pathlib.Path(__file__).with_name("storyboard.json").write_text(json.dumps(sb, indent=1, ensure_ascii=False))
print(len(B), "beats", sum(len(b["text"].split()) for b in B), "words")
