#!/usr/bin/env python3
"""Cloud Checker — Cloudflare IP Scanner for restricted networks."""

import socket, ssl, time, random, ipaddress, os, sys, io, threading
import statistics, json, re, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import parse_qs, unquote
import urllib.request

from rich.console import Console, Group
from rich.table import Table as RTable
from rich.text import Text as RText
from rich.progress_bar import ProgressBar
from rich.live import Live

try:
    import autoupgrader as au
    au.set_url("https://github.com/Pytholearn/CloudChecker")
    au.set_current_version("1.0.0")
except ImportError:
    au = None

VERSION = "1.0.0"
GITHUB = "github.com/Pytholearn"
console = Console()

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.system("chcp 65001 >nul 2>&1")
    os.system("")

# ─── Key input ────────────────────────────────────────────────────
if sys.platform == "win32":
    import msvcrt
    def _read_key():
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return {"H":"UP","P":"DOWN","K":"LEFT","M":"RIGHT"}.get(ch2,"")
        if ch == "\r": return "ENTER"
        if ch == "\x1b": return "ESC"
        if ch == "\x08": return "BS"
        if ch == "\x03": raise KeyboardInterrupt
        return ch
    def _kbhit(): return msvcrt.kbhit()
else:
    import tty, termios, select as _sel
    def _read_key():
        fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd); ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    return {"A":"UP","B":"DOWN","C":"RIGHT","D":"LEFT"}.get(ch3,"")
                return "ESC"
            if ch in ("\r","\n"): return "ENTER"
            if ch == "\x7f": return "BS"
            if ch == "\x03": raise KeyboardInterrupt
            return ch
        finally: termios.tcsetattr(fd, termios.TCSADRAIN, old)
    def _kbhit(): return bool(_sel.select([sys.stdin],[],[],0)[0])

# ─── ANSI ─────────────────────────────────────────────────────────
E = lambda c: f"\033[{c}m"
RST=E(0); BOLD=E(1); DIM=E(2); ITAL=E(3)
RED=E(91); GRN=E(92); YEL=E(93); BLU=E(94); MAG=E(95); CYN=E(96); WHT=E(97); GRY=E(90)
def rgb(r,g,b): return f"\033[38;2;{r};{g};{b}m"
ORA=rgb(255,140,0)

def cls(): sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()
def cur_hide(): sys.stdout.write("\033[?25l"); sys.stdout.flush()
def cur_show(): sys.stdout.write("\033[?25h"); sys.stdout.flush()
def goto(r,c): sys.stdout.write(f"\033[{r};{c}H"); sys.stdout.flush()

# ─── Banner ───────────────────────────────────────────────────────
CLOUD = r"""
          ☁                                                     ☁
                .~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
          .~~~~'                                               '~~~.
      .~~'                                                         '~~.
    .'                                                                 '.
   /   ██████╗██╗      ██████╗ ██╗   ██╗██████╗                          \
  |   ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗                          |
  |   ██║     ██║     ██║   ██║██║   ██║██║  ██║                          |
  |   ██║     ██║     ██║   ██║██║   ██║██║  ██║                          |
  |   ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝                         |
  |    ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝                          |
  |        ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗███████╗██████╗         |
  |       ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔══██╗       |
  |       ██║     ███████║█████╗  ██║     █████╔╝ █████╗  ██████╔╝       |
  |       ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗ ██╔══╝  ██╔══██╗       |
  |       ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗███████╗██║  ██║       |
  |        ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    |
   \                      made by hazard                                /
    '.                  github.com/Pytholearn                        .'
      '~~.                                                      .~~'
          '~~~.                                             .~~~'
               '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
""".strip("\n")

CLOUD_SMALL = [
    "    ☁                                                 ☁          ☁",
    "           .--------.              .--------.",
    "      .---'          '---. .------'          '---.",
    "    /                                               \\",
    "   |  ╔═╗ ╦  ╔═╗ ╦ ╦ ╔╦╗   ╔═╗ ╦ ╦ ╔═╗ ╔═╗ ╦╔═ ╔═╗ ╦═╗  |",
    "   |  ║   ║  ║ ║ ║ ║  ║║   ║   ╠═╣ ║╣  ║   ╠╩╗ ║╣  ╠╦╝  |",
    "   |  ╚═╝ ╩═╝╚═╝ ╚═╝ ═╩╝   ╚═╝ ╩ ╩ ╚═╝ ╚═╝ ╩ ╩ ╚═╝ ╩╚═  |",
    "    \\               made by hazard                    /",
    "      '---._____________________________________,---'",
    "                    " + GITHUB,
]

def banner_str(small=False):
    out = []
    if small:
        for ln in CLOUD_SMALL:
            out.append(f"{ORA}{BOLD}{ln}{RST}")
    else:
        for ln in CLOUD.split("\n"):
            out.append(f"{ORA}{BOLD}{ln}{RST}")
    out.append(f"\n  {DIM}{ITAL}  Cloudflare IP Scanner — tuned for restricted networks{RST}")
    out.append(f"  {DIM}  v{VERSION}{RST}\n")
    return "\n".join(out)

BANNER_HEIGHT = len(CLOUD.split("\n")) + 4

# ─── Cloudflare ───────────────────────────────────────────────────
CF_V4_DEFAULT = [
    "173.245.48.0/20","103.21.244.0/22","103.22.200.0/22","103.31.4.0/22",
    "141.101.64.0/18","108.162.192.0/18","190.93.240.0/20","188.114.96.0/20",
    "197.234.240.0/22","198.41.128.0/17","162.158.0.0/15","104.16.0.0/13",
    "104.24.0.0/14","172.64.0.0/13","131.0.72.0/22"]
CDN_PORTS = [443, 8443, 2053, 2083, 2087, 2096]

def _fetch_cf_ranges():
    try:
        req = urllib.request.Request("https://www.cloudflare.com/ips-v4/",
                                    headers={"User-Agent":"CloudChecker/1.0"})
        resp = urllib.request.urlopen(req, timeout=8)
        lines = resp.read().decode().strip().split("\n")
        ranges = [l.strip() for l in lines if l.strip() and "/" in l]
        if len(ranges) >= 5:
            return ranges
    except: pass
    return None

def get_cf_ranges(cfg_dir):
    cache = os.path.join(cfg_dir, "cf_ranges.json")
    try:
        with open(cache) as f:
            data = json.load(f)
            if time.time() - data.get("ts", 0) < 86400:
                return data["ranges"]
    except: pass
    fresh = _fetch_cf_ranges()
    if fresh:
        try:
            os.makedirs(cfg_dir, exist_ok=True)
            with open(cache, "w") as f:
                json.dump({"ts": time.time(), "ranges": fresh}, f)
        except: pass
        return fresh
    return CF_V4_DEFAULT

# ─── Config URL parser ───────────────────────────────────────────
class ProxyConfig:
    def __init__(self, url):
        self.raw = url.strip(); self.sni=""; self.host=""; self.port=443
        self.remark=""; self.protocol=""; self.transport=""
        u = self.raw
        if u.startswith("vless://"): self.protocol="vless"; u=u[8:]
        elif u.startswith("trojan://"): self.protocol="trojan"; u=u[9:]
        else: return
        if "#" in u: u,f=u.rsplit("#",1); self.remark=unquote(f)
        if "?" in u:
            u,qs=u.split("?",1); p=parse_qs(qs)
            self.sni=p.get("sni",[""])[0]; self.host=p.get("host",[""])[0]
            self.transport=p.get("type",["tcp"])[0]
        if "@" in u:
            _,ap=u.split("@",1)
            if ":" in ap:
                a,pp=ap.rsplit(":",1)
                try: self.port=int(pp)
                except: pass
        if not self.host: self.host=self.sni
        if not self.sni: self.sni=self.host
    @property
    def is_valid(self): return self.protocol in ("vless","trojan") and bool(self.sni)

def modify_config_url(base_url, new_ip):
    for proto in ("vless://", "trojan://"):
        if base_url.startswith(proto):
            rest = base_url[len(proto):]
            frag = ""
            if "#" in rest: rest, frag = rest.rsplit("#", 1)
            query = ""
            if "?" in rest: rest, query = rest.split("?", 1)
            if "@" in rest:
                creds, ap = rest.split("@", 1)
                port = "443"
                if ":" in ap: _, port = ap.rsplit(":", 1)
                out = f"{proto}{creds}@{new_ip}:{port}"
                if query: out += "?" + query
                if frag: out += "#" + frag
                return out
    return base_url

# ─── Result ───────────────────────────────────────────────────────
class Result:
    __slots__ = ("ip","port","latencies","failed","total","colo","speed")
    def __init__(self, ip, port):
        self.ip=ip; self.port=port; self.latencies=[]; self.failed=0
        self.total=0; self.colo=""; self.speed=0.0
    @property
    def loss(self): return (self.failed/self.total*100) if self.total else 100
    @property
    def avg(self): return statistics.mean(self.latencies) if self.latencies else 0
    @property
    def ok(self): return len(self.latencies) > 0 and self.loss < 100
    @property
    def ep(self): return f"{self.ip}:{self.port}"

# ─── IP Source ────────────────────────────────────────────────────
class IPSource:
    def __init__(self, ranges=None):
        self.nets = [ipaddress.IPv4Network(c, strict=False) for c in (ranges or CF_V4_DEFAULT)]
    def rand(self, n):
        seen=set(); out=[]
        for _ in range(n*3):
            if len(out) >= n: break
            net = random.choice(self.nets)
            ip = str(ipaddress.IPv4Address(
                int(net.network_address) + random.randint(0, int(net.num_addresses)-1)))
            if ip not in seen: seen.add(ip); out.append(ip)
        return out
    def neighbors(self, ip, r=12):
        b = int(ipaddress.IPv4Address(ip)); out = []
        for o in range(-r, r+1):
            if o == 0: continue
            n = ipaddress.IPv4Address(b+o)
            if any(n in net for net in self.nets): out.append(str(n))
        return out
    @staticmethod
    def from_file(path):
        ips = []
        try:
            for ln in open(path, encoding="utf-8"):
                ln = ln.strip()
                if not ln or ln.startswith("#"): continue
                if "," in ln: ln = ln.split(",")[0].strip()
                if ":" in ln: ln = ln.split(":")[0].strip()
                if "/" in ln:
                    try:
                        net = ipaddress.IPv4Network(ln, strict=False)
                        if net.num_addresses <= 256:
                            ips.extend(str(h) for h in net.hosts())
                        else:
                            b = int(net.network_address); t = int(net.num_addresses)
                            for _ in range(256):
                                ips.append(str(ipaddress.IPv4Address(b+random.randint(0, t-1))))
                    except: pass
                else:
                    try: ipaddress.IPv4Address(ln); ips.append(ln)
                    except: pass
        except FileNotFoundError: pass
        return ips

# ─── Prober ───────────────────────────────────────────────────────
class Prober:
    def __init__(self, timeout=5, tries=1, sni=None):
        self.timeout = timeout; self.tries = tries; self.sni = sni
        self._ctx = ssl.create_default_context()

    def probe(self, ip, port):
        r = Result(ip, port)
        sni = self.sni or "speed.cloudflare.com"
        req = f"GET /cdn-cgi/trace HTTP/1.1\r\nHost: {sni}\r\nConnection: close\r\n\r\n".encode()
        for _ in range(self.tries):
            r.total += 1
            s = None
            try:
                t0 = time.perf_counter()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                s.connect((ip, port))
                ss = self._ctx.wrap_socket(s, server_hostname=sni)
                ss.sendall(req)
                ss.settimeout(2)
                buf = b""
                for _ in range(4):
                    try:
                        c = ss.recv(4096)
                        if not c: break
                        buf += c
                        if b"colo=" in buf: break
                    except (socket.timeout, ssl.SSLError): break
                ms = (time.perf_counter()-t0)*1000
                r.latencies.append(ms)
                txt = buf.decode("utf-8", errors="ignore")
                m = re.search(r"colo=([A-Z]{3})", txt)
                if m: r.colo = m.group(1)
                ss.close()
            except: r.failed += 1
            finally:
                if s:
                    try: s.close()
                    except: pass
        return r

    def speed_test(self, ip, port):
        sni = self.sni or "speed.cloudflare.com"
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((ip, port))
            ss = self._ctx.wrap_socket(s, server_hostname=sni)
            req = f"GET /__down?bytes=102400 HTTP/1.1\r\nHost: speed.cloudflare.com\r\nConnection: close\r\n\r\n"
            ss.sendall(req.encode())
            t0 = time.perf_counter()
            total_bytes = 0
            while True:
                try:
                    c = ss.recv(8192)
                    if not c: break
                    total_bytes += len(c)
                except: break
            elapsed = time.perf_counter() - t0
            ss.close()
            return (total_bytes / elapsed / 1024) if elapsed > 0 else 0
        except: return 0
        finally:
            if s:
                try: s.close()
                except: pass

# ─── Engine ───────────────────────────────────────────────────────
class Engine:
    def __init__(self, workers=50, prober=None):
        self.w = workers; self.prober = prober or Prober()
        self.tested = 0; self.healthy = 0; self.failed = 0
        self._lock = threading.Lock(); self._stop = threading.Event()
    def stop(self): self._stop.set()
    @property
    def stopped(self): return self._stop.is_set()
    def scan(self, ips, ports, on_result=None):
        tasks = [(ip, p) for ip in ips for p in ports]
        total = len(tasks)
        with ThreadPoolExecutor(max_workers=self.w) as pool:
            futs = {}
            for ip, p in tasks:
                if self._stop.is_set(): break
                futs[pool.submit(self.prober.probe, ip, p)] = (ip, p)
            for f in as_completed(futs):
                if self._stop.is_set(): break
                try:
                    r = f.result()
                    with self._lock:
                        self.tested += 1
                        if r.ok: self.healthy += 1
                        else: self.failed += 1
                    if on_result: on_result(r, self.tested, total)
                except:
                    with self._lock: self.tested += 1; self.failed += 1

# ─── Clipboard ────────────────────────────────────────────────────
def copy_clip(text):
    try:
        if sys.platform == "win32":
            subprocess.run(["clip"], input=text.encode("utf-8"), check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        elif sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        else:
            subprocess.run(["xclip", "-selection", "clipboard"],
                           input=text.encode("utf-8"), check=True)
        return True
    except: return False

# ─── Export ───────────────────────────────────────────────────────
def export_csv(results, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("ip,port,latency_ms,loss_pct,colo,speed_kbps\n")
        for r in results:
            f.write(f"{r.ip},{r.port},{r.avg:.2f},{r.loss:.1f},{r.colo},{r.speed:.1f}\n")

def export_json(results, path):
    data = [{"ip": r.ip, "port": r.port, "latency_ms": round(r.avg, 2),
             "loss_pct": round(r.loss, 1), "colo": r.colo,
             "speed_kbps": round(r.speed, 1)} for r in results]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ─── Persistence ──────────────────────────────────────────────────
class Cfg:
    DEF = {"count":5000, "workers":50, "timeout":5, "ports":[443],
           "neighbor":True, "config_url":"", "max_latency":0}
    def __init__(self):
        self.d = dict(self.DEF)
        if sys.platform == "win32":
            b = os.environ.get("APPDATA", os.path.expanduser("~"))
        elif sys.platform == "darwin":
            b = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
        else:
            b = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
        self._dir = os.path.join(b, "cloudchecker")
        self._f = os.path.join(self._dir, "config.json")
        try:
            with open(self._f) as f: self.d.update(json.load(f))
        except: pass
    @property
    def dir(self): return self._dir
    def save(self):
        os.makedirs(self._dir, exist_ok=True)
        with open(self._f, "w") as f: json.dump(self.d, f, indent=2)
    def __getitem__(self, k): return self.d[k]
    def __setitem__(self, k, v): self.d[k] = v

# ─── Live results file ───────────────────────────────────────────
class LiveWriter:
    def __init__(self):
        self.path = f"CloudChecker-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    def write(self, results):
        with open(self.path, "w", encoding="utf-8") as f:
            for r in results:
                if r.ok: f.write(r.ip + "\n")
    def save_ips(self, results):
        with open("ips.txt", "w", encoding="utf-8") as f:
            for r in results:
                if r.ok: f.write(r.ip + "\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONFIG FORM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConfigForm:
    def __init__(self, proxy_cfg=None):
        self.pcfg = proxy_cfg
        self.row = 0
        self.sel = [0, 1, 0, 2, 0]

        self.port_labels = []
        self.port_values = []
        if proxy_cfg and proxy_cfg.is_valid:
            self.port_labels.append("Config")
            self.port_values.append(proxy_cfg.port)
        for p in CDN_PORTS:
            self.port_labels.append(str(p))
            self.port_values.append(p)
        self.port_cur = 0
        self.port_on = {0}

        self.cust = {1: "", 2: "", 3: "", 4: ""}
        self.editing = False

    NROWS = 6
    LABELS = ["Source", "Count", "Workers", "Timeout", "Max Lat", "Ports"]
    DESCS = [
        ["random Cloudflare IPv4 IPs", "load IPs from file",
         "enter custom CIDR / IP range"],
        "IPs to probe",
        "concurrent probes",
        "per-probe deadline",
        "skip IPs above this latency (0 = no limit)",
        "space toggles; multiple ports multiply work",
    ]
    OPTS = [
        ["Random", "From File", "Custom Range"],
        ["1,000", "5,000", "20,000", "Custom"],
        ["50 – default", "100 – balanced", "200 – fast", "Custom"],
        ["2s – aggressive", "3s – balanced", "5s – default", "Custom"],
        ["No limit", "200ms", "500ms", "1000ms", "Custom"],
    ]
    VALS = [
        ["random", "file", "custom"],
        [1000, 5000, 20000, None],
        [50, 100, 200, None],
        [2, 3, 5, None],
        [0, 200, 500, 1000, None],
    ]

    _KEEP = object()
    def run(self):
        while True:
            self._render()
            k = _read_key()
            r = self._handle(k)
            if r is not self._KEEP:
                return r

    def _render(self):
        cls()
        w = sys.stdout.write
        w(f"  {YEL}{BOLD}⚡ Find Working IPs{RST}\n")
        w(f"  {DIM}{'─'*70}{RST}\n\n")

        for ri in range(self.NROWS):
            active = ri == self.row
            lbl = self.LABELS[ri]
            lc = YEL if active else WHT

            if ri < 5:
                opts = self.OPTS[ri]
                parts = []
                for oi, opt in enumerate(opts):
                    if opt == "Custom" and self.cust.get(ri, ""):
                        display = f"Custom: {self.cust[ri]}"
                    elif opt == "Custom" and self.editing and active and self.sel[ri] == oi:
                        display = "Custom: _"
                    else:
                        display = opt
                    if oi == self.sel[ri]:
                        if active:
                            parts.append(f" {CYN}{BOLD}[{display}]{RST} ")
                        else:
                            parts.append(f" {BOLD}[{display}]{RST} ")
                    else:
                        parts.append(f" {DIM}{display}{RST} ")
                    if oi < len(opts) - 1:
                        parts.append(f"{DIM}│{RST}")
                ostr = "".join(parts)
            else:
                parts = []
                for pi, pl in enumerate(self.port_labels):
                    ck = "✓ " if pi in self.port_on else "  "
                    txt = ck + pl
                    if active and pi == self.port_cur:
                        parts.append(f" {CYN}{BOLD}{txt}{RST} ")
                    elif pi in self.port_on:
                        parts.append(f" {GRN}{txt}{RST} ")
                    else:
                        parts.append(f" {DIM}{txt}{RST} ")
                    if pi < len(self.port_labels) - 1:
                        parts.append(f"{DIM}│{RST}")
                ostr = "".join(parts)

            w(f"  {lc}{lbl:<10s}{RST}{ostr}\n")
            desc = self.DESCS[ri]
            if isinstance(desc, list):
                desc = desc[min(self.sel[ri], len(desc)-1)]
            w(f"  {' '*10}{DIM}{desc}{RST}\n\n")

        w(f"  {DIM}↑/↓ row   ←/→ option   enter continue   esc back{RST}\n")
        sys.stdout.flush()

    def _handle(self, k):
        K = self._KEEP
        if self.editing:
            if k == "ENTER":    self.editing = False
            elif k == "ESC":    self.editing = False; self.cust[self.row] = ""
            elif k == "BS":     self.cust[self.row] = self.cust[self.row][:-1]
            elif k.isdigit():   self.cust[self.row] += k
            return K

        if k == "UP":      self.row = (self.row - 1) % self.NROWS
        elif k == "DOWN":  self.row = (self.row + 1) % self.NROWS
        elif k == "LEFT":
            if self.row < 5:
                self.sel[self.row] = max(0, self.sel[self.row] - 1)
            else:
                self.port_cur = max(0, self.port_cur - 1)
        elif k == "RIGHT":
            if self.row < 5:
                self.sel[self.row] = min(len(self.OPTS[self.row]) - 1, self.sel[self.row] + 1)
            else:
                self.port_cur = min(len(self.port_labels) - 1, self.port_cur + 1)
        elif k == " ":
            if self.row == 5:
                pi = self.port_cur
                if pi in self.port_on:
                    if len(self.port_on) > 1: self.port_on.discard(pi)
                else: self.port_on.add(pi)
        elif k == "ENTER":
            if self.row < 5 and self.OPTS[self.row][self.sel[self.row]] == "Custom":
                if not self.cust.get(self.row, ""):
                    self.editing = True
                    return K
            return self._build()
        elif k in ("ESC", "q", "Q"):
            return None
        elif k.isdigit() and self.row < 5:
            if self.OPTS[self.row][self.sel[self.row]] == "Custom":
                self.editing = True
                self.cust[self.row] = k
        return K

    def _build(self):
        source = self.VALS[0][self.sel[0]]
        def _val(row, default):
            vi = self.sel[row]
            v = self.VALS[row][vi]
            if v is None:
                try: return int(self.cust.get(row, str(default)))
                except: return default
            return v
        count = _val(1, 5000)
        workers = _val(2, 50)
        timeout = _val(3, 5)
        max_latency = _val(4, 0)
        ports = sorted({self.port_values[i] for i in self.port_on})
        if not ports: ports = [443]
        return {"source": source, "count": count, "workers": workers,
                "timeout": timeout, "max_latency": max_latency, "ports": ports}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Rich display helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

def _scan_panel(engine, top, total, ports, sni, t0, wpath, si):
    elapsed = time.time() - t0
    sp = SPIN[si % len(SPIN)]
    port_str = ",".join(str(p) for p in ports)

    hdr = RText()
    hdr.append(f" {sp} ", style="bold cyan")
    hdr.append("Phase 1 — Finding reachable IPs", style="bold yellow")
    if sni: hdr.append(f"  SNI: {sni}", style="dim")

    st = RText()
    st.append(f"\n  tested: ", style="white")
    st.append(f"{engine.tested}", style="bold")
    st.append(f"  candidates: ", style="white")
    st.append(f"{engine.healthy}", style="bold green")
    st.append(f"  failed: ", style="white")
    st.append(f"{engine.failed}", style="dim red")
    st.append(f"  target: {total}  {elapsed:.0f}s", style="dim")

    bar = ProgressBar(total=total, completed=engine.tested, width=50,
                      complete_style="cyan", finished_style="bold green")
    info = RText(f"  ports: {port_str}    results → {wpath}", style="dim")

    tbl = RTable(show_header=True, header_style="bold white", border_style="dim",
                 show_edge=False, padding=(0, 1), min_width=60)
    tbl.add_column("ENDPOINT", style="cyan", min_width=22)
    tbl.add_column("LOSS", justify="right", min_width=7)
    tbl.add_column("AVG(ms)", justify="right", min_width=9)
    tbl.add_column("COLO", justify="right", min_width=6, style="magenta")
    tbl.add_column("", min_width=2)
    for r in top:
        lc = "green" if r.loss == 0 else "yellow" if r.loss < 50 else "red"
        ac = "green" if r.avg < 200 else "yellow" if r.avg < 500 else "red"
        tbl.add_row(r.ep, f"[{lc}]{r.loss:.1f}%[/{lc}]",
                    f"[{ac}]{r.avg:.2f}[/{ac}]", r.colo or "—", "[green]✓[/green]")
    if not top:
        tbl.add_row("[dim]scanning...[/dim]", "", "", "", "")

    return Group(hdr, st, RText(""), bar, info, RText(""), tbl,
                 RText("\n  [q] stop scan", style="dim"))


def _speed_panel(idx, total, ip):
    hdr = RText()
    hdr.append(f" {SPIN[idx % len(SPIN)]} ", style="bold cyan")
    hdr.append(f"Phase 2 — Speed test ({idx+1}/{total})", style="bold yellow")
    bar = ProgressBar(total=total, completed=idx, width=40,
                      complete_style="cyan", finished_style="bold green")
    info = RText(f"  Testing {ip} ...", style="dim")
    return Group(hdr, RText(""), bar, info)


def _results_table(results):
    tbl = RTable(show_header=True, header_style="bold white", border_style="dim",
                 show_edge=True, padding=(0, 1), min_width=70)
    tbl.add_column("#", style="dim", width=4, justify="right")
    tbl.add_column("ENDPOINT", style="cyan", min_width=22)
    tbl.add_column("LOSS", justify="right", min_width=7)
    tbl.add_column("AVG(ms)", justify="right", min_width=9)
    tbl.add_column("COLO", justify="right", min_width=6, style="bold magenta")
    tbl.add_column("SPEED", justify="right", min_width=10)
    tbl.add_column("", min_width=2)
    for i, r in enumerate(results[:20], 1):
        lc = "green" if r.loss == 0 else "yellow" if r.loss < 50 else "red"
        ac = "green" if r.avg < 200 else "yellow" if r.avg < 500 else "red"
        spd = f"{r.speed:.0f} KB/s" if r.speed > 0 else "—"
        sc = "green" if r.speed > 500 else "yellow" if r.speed > 100 else "dim"
        tbl.add_row(str(i), r.ep, f"[{lc}]{r.loss:.1f}%[/{lc}]",
                    f"[{ac}]{r.avg:.2f}[/{ac}]", r.colo or "—",
                    f"[{sc}]{spd}[/{sc}]", "[green]✓[/green]")
    return tbl


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class App:
    def __init__(self):
        self.cfg = Cfg()
        cf = get_cf_ranges(self.cfg.dir)
        self.ips = IPSource(cf)
        self.writer = LiveWriter()
        self.pcfg = None
        self.last_results = []

    def run(self):
        cur_hide()
        try:
            if au:
                try:
                    if not au.is_up_to_date():
                        cls()
                        print(f"  {YEL}{BOLD}New version available!{RST}")
                        print(f"  {DIM}Updating...{RST}")
                        au.update()
                        print(f"  {GRN}Updated! Restart to use new version.{RST}")
                        time.sleep(2)
                except: pass
            self._main()
        except KeyboardInterrupt: pass
        finally: cur_show(); cls()

    def _main(self):
        while True:
            cls(); print(banner_str())
            idx = self._menu(
                ["Find Working IPs", "Config Modifier", "About", "Quit"],
                ["scan & speed-test Cloudflare IPs",
                 "replace IPs in V2Ray configs", "", ""])
            if   idx == 0: self._scan_flow()
            elif idx == 1: self._config_modifier()
            elif idx == 2: self._about()
            else: return

    def _menu(self, items, descs):
        idx = 0
        while True:
            goto(BANNER_HEIGHT, 1)
            for i, item in enumerate(items):
                if i == idx:
                    d = f"  {DIM}{descs[i]}{RST}" if descs[i] else ""
                    print(f"  {CYN}{BOLD}▶ {item}{RST}{d}    ")
                else:
                    print(f"    {item}                                              ")
            print(f"\n  {DIM}↑/↓ navigate   enter select   q quit{RST}")
            sys.stdout.flush()
            k = _read_key()
            if k == "UP":     idx = (idx - 1) % len(items)
            elif k == "DOWN": idx = (idx + 1) % len(items)
            elif k == "ENTER": return idx
            elif k in ("q", "Q", "ESC"): return len(items) - 1

    # ── Scan flow ─────────────────────────────────────────────────

    def _scan_flow(self):
        cls(); print(banner_str(small=True))
        print(f"  {BOLD}Config URL (optional){RST}")
        print(f"  {DIM}Paste VLESS/Trojan URL for SNI-based probing, or Enter to skip{RST}\n")
        cur_show()
        try: url = input(f"  {CYN}▶{RST} ").strip()
        except: url = ""
        cur_hide()

        self.pcfg = None
        if url:
            pc = ProxyConfig(url)
            if pc.is_valid:
                self.pcfg = pc; self.cfg["config_url"] = url

        form = ConfigForm(self.pcfg)
        result = form.run()
        if result is None: return

        src      = result["source"]
        count    = result["count"]
        workers  = result["workers"]
        timeout  = result["timeout"]
        max_lat  = result["max_latency"]
        ports    = result["ports"]
        self.cfg["count"] = count; self.cfg["workers"] = workers
        self.cfg["timeout"] = timeout; self.cfg["ports"] = ports
        self.cfg["max_latency"] = max_lat; self.cfg.save()

        if src == "file":
            cls(); print(banner_str(small=True)); cur_show()
            try:
                path = input(f"  {CYN}▶{RST} Path to IP file [{DIM}ips.txt{RST}]: ").strip() or "ips.txt"
            except: path = "ips.txt"
            cur_hide()
            ips = IPSource.from_file(path)
            if not ips:
                self._msg(f"{RED}No valid IPs in {path}{RST}"); return
        elif src == "custom":
            cls(); print(banner_str(small=True))
            print(f"  {BOLD}Custom IP Range{RST}")
            print(f"  {DIM}Enter CIDR ranges, single IPs, or IP:port — one per line{RST}")
            print(f"  {DIM}Examples: 27.50.48.0/24  or  1.0.0.1  or  27.50.48.49{RST}")
            print(f"  {DIM}Empty line to finish{RST}\n")
            cur_show()
            lines = []
            while True:
                try: ln = input(f"  {CYN}▶{RST} ").strip()
                except: break
                if not ln: break
                lines.append(ln)
            cur_hide()
            if not lines:
                self._msg(f"{RED}No IPs entered{RST}"); return
            ips = []
            for ln in lines:
                ln = ln.split(":")[0].strip() if ":" in ln else ln.strip()
                if "/" in ln:
                    try:
                        net = ipaddress.IPv4Network(ln, strict=False)
                        if net.num_addresses <= 65536:
                            ips.extend(str(h) for h in net.hosts())
                        else:
                            b = int(net.network_address); t = int(net.num_addresses)
                            for _ in range(count):
                                ips.append(str(ipaddress.IPv4Address(b+random.randint(0, t-1))))
                    except: self._flash(f"{YEL}Skipped invalid: {ln}{RST}")
                else:
                    try: ipaddress.IPv4Address(ln); ips.append(ln)
                    except: self._flash(f"{YEL}Skipped invalid: {ln}{RST}")
            if not ips:
                self._msg(f"{RED}No valid IPs parsed{RST}"); return
            if len(ips) > count: ips = random.sample(ips, count)
        else:
            ips = self.ips.rand(count)

        self._do_scan(ips, ports, workers, timeout, max_lat)

    def _retry(self):
        url = self.cfg["config_url"]
        if url:
            pc = ProxyConfig(url)
            if pc.is_valid: self.pcfg = pc
        ips = self.ips.rand(self.cfg["count"])
        self._do_scan(ips, self.cfg["ports"], self.cfg["workers"],
                      self.cfg["timeout"], self.cfg["max_latency"])

    # ── Live scan ─────────────────────────────────────────────────

    def _do_scan(self, ips, ports, workers, timeout, max_lat):
        sni = self.pcfg.sni if self.pcfg else None
        prober = Prober(timeout, 1, sni)
        engine = Engine(workers, prober)
        total = len(ips) * len(ports)
        healthy = []; h_lock = threading.Lock()
        self.writer = LiveWriter()

        def on_result(r, tested, tot):
            if r.ok:
                if max_lat > 0 and r.avg > max_lat:
                    return
                with h_lock: healthy.append(r)

        scan_done = threading.Event()
        def worker():
            engine.scan(ips, ports, on_result)
            scan_done.set()

        t = threading.Thread(target=worker, daemon=True)
        t0 = time.time(); t.start(); si = 0; cur_show()

        try:
            with Live(console=console, refresh_per_second=6, transient=True) as live:
                while not scan_done.is_set():
                    if _kbhit():
                        k = _read_key()
                        if k in ("q", "Q", "ESC"):
                            engine.stop(); break
                    si += 1
                    with h_lock:
                        top = sorted(healthy, key=lambda x: x.avg)[:20]
                    live.update(_scan_panel(engine, top, total, ports,
                                           sni, t0, self.writer.path, si))
                    time.sleep(0.15)
        except: pass
        finally: cur_hide()

        scan_done.wait(timeout=2)

        # Neighbor scan
        with h_lock: top_all = sorted(healthy, key=lambda x: x.avg)
        if self.cfg["neighbor"] and top_all:
            nb = set(); existing = {r.ip for r in top_all}
            for r in top_all[:5]:
                for n in self.ips.neighbors(r.ip):
                    if n not in existing: nb.add(n)
            if nb and not engine.stopped:
                nb_eng = Engine(workers, prober)
                def on_nb(r, tested, tot):
                    if r.ok and (max_lat <= 0 or r.avg <= max_lat):
                        with h_lock: healthy.append(r)
                nb_eng.scan(list(nb), ports, on_nb)

        with h_lock:
            final = sorted(healthy, key=lambda x: x.avg)

        # Phase 2: speed test on top 10
        if final and not engine.stopped:
            speed_targets = final[:10]
            cur_show()
            try:
                with Live(console=console, refresh_per_second=4, transient=True) as live:
                    for idx, r in enumerate(speed_targets):
                        live.update(_speed_panel(idx, len(speed_targets), r.ep))
                        r.speed = prober.speed_test(r.ip, r.port)
            except: pass
            finally: cur_hide()
            final.sort(key=lambda x: (-x.speed, x.avg))

        self.last_results = final
        self.writer.write(final)
        elapsed = time.time() - t0
        self._show_results(final, elapsed, engine)

    # ── Results ───────────────────────────────────────────────────

    def _show_results(self, results, elapsed, engine):
        idx = 0
        items = ["Copy best IP", "Save ips.txt", "Export CSV", "Export JSON",
                 "Sort by Avg", "Sort by Speed", "Sort by Colo", "Back"]
        while True:
            console.clear()
            console.print(f"  [bold green]⚡ Scan complete[/]  [dim]{elapsed:.1f}s  "
                          f"Tested:{engine.tested}  Healthy:{engine.healthy}  "
                          f"Failed:{engine.failed}[/]")
            console.print(f"  [dim]Results: {self.writer.path}[/]\n")

            if results:
                console.print(_results_table(results))
            else:
                console.print("  [dim](no healthy results)[/]")

            console.print()
            for i, item in enumerate(items):
                if i == idx: console.print(f"  [cyan bold]▶ {item}[/]")
                else: console.print(f"    {item}")
            console.print(f"\n  [dim]↑/↓ navigate   enter select   q back[/]")

            k = _read_key()
            if k == "UP":     idx = (idx - 1) % len(items)
            elif k == "DOWN": idx = (idx + 1) % len(items)
            elif k == "ENTER":
                if idx == 0 and results:
                    if copy_clip(results[0].ip):
                        self._flash(f"{GRN}✓ Copied {results[0].ip}{RST}")
                    else:
                        self._flash(f"{RED}Clipboard not available{RST}")
                elif idx == 1:
                    self.writer.save_ips(results)
                    self._flash(f"{GRN}✓ Saved to ips.txt{RST}")
                elif idx == 2:
                    p = f"CloudChecker-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
                    export_csv(results, p)
                    self._flash(f"{GRN}✓ Exported {p}{RST}")
                elif idx == 3:
                    p = f"CloudChecker-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
                    export_json(results, p)
                    self._flash(f"{GRN}✓ Exported {p}{RST}")
                elif idx == 4: results.sort(key=lambda r: r.avg if r.avg > 0 else 9e9)
                elif idx == 5: results.sort(key=lambda r: -r.speed)
                elif idx == 6: results.sort(key=lambda r: r.colo)
                elif idx == 7: return
            elif k in ("q", "Q", "ESC"): return

    # ── Config Modifier ──────────────────────────────────────────

    def _config_modifier(self):
        cls(); print(banner_str(small=True))
        print(f"  {BOLD}Config Modifier{RST}")
        print(f"  {DIM}Replace IPs in your V2Ray config with clean scanned IPs{RST}\n")

        cur_show()
        print(f"  {BOLD}Step 1:{RST} Paste your base config URL (VLESS/Trojan):")
        try: base = input(f"  {CYN}▶{RST} ").strip()
        except: base = ""
        if not base: cur_hide(); return

        pc = ProxyConfig(base)
        if not pc.is_valid:
            cur_hide()
            self._msg(f"{RED}Invalid config URL. Must be vless:// or trojan://{RST}")
            return

        print(f"\n  {BOLD}Step 2:{RST} Path to IP list file (or Enter for last scan / ips.txt):")
        try: ip_path = input(f"  {CYN}▶{RST} ").strip()
        except: ip_path = ""
        cur_hide()

        ips = []
        if ip_path:
            ips = IPSource.from_file(ip_path)
            if not ips:
                self._msg(f"{RED}No valid IPs in {ip_path}{RST}"); return
        else:
            if self.last_results:
                ips = [r.ip for r in self.last_results if r.ok]
            if not ips and os.path.exists("ips.txt"):
                ips = [l.strip() for l in open("ips.txt", encoding="utf-8") if l.strip()]
            if not ips:
                self._msg(f"{RED}No IPs found. Run a scan first or provide a file.{RST}")
                return

        configs = [modify_config_url(base, ip) for ip in ips]
        self._show_configs(configs, pc)

    def _show_configs(self, configs, pc):
        scroll = 0
        while True:
            console.clear()
            console.print(f"  [bold yellow]☁ Generated Configs ({len(configs)})[/]")
            console.print(f"  [dim]Protocol: {pc.protocol}  SNI: {pc.sni}[/]\n")

            tbl = RTable(show_header=True, header_style="bold white", border_style="dim",
                         show_edge=True, padding=(0, 1), min_width=70)
            tbl.add_column("#", style="dim", width=4, justify="right")
            tbl.add_column("Config", style="cyan", overflow="fold")

            visible = configs[scroll:scroll+12]
            for i, c in enumerate(visible, scroll+1):
                tbl.add_row(str(i), c if len(c) < 90 else c[:87] + "...")
            console.print(tbl)

            console.print(f"\n  [dim]{scroll+1}-{min(scroll+12, len(configs))} of {len(configs)}[/]")
            console.print(f"\n  [dim]\\[s] save to file  \\[c] copy all  \\[↑/↓] scroll  \\[q] back[/]")

            k = _read_key()
            if k == "UP": scroll = max(0, scroll - 1)
            elif k == "DOWN": scroll = min(max(0, len(configs) - 12), scroll + 1)
            elif k in ("s", "S"):
                path = f"configs-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
                with open(path, "w", encoding="utf-8") as f:
                    for c in configs: f.write(c + "\n")
                self._flash(f"{GRN}✓ Saved {len(configs)} configs to {path}{RST}")
            elif k in ("c", "C"):
                if copy_clip("\n".join(configs)):
                    self._flash(f"{GRN}✓ Copied {len(configs)} configs{RST}")
                else:
                    self._flash(f"{RED}Clipboard not available{RST}")
            elif k in ("q", "Q", "ESC"): return

    # ── About ─────────────────────────────────────────────────────

    def _about(self):
        cls(); print(banner_str())
        print(f"  {BOLD}About Cloud Checker{RST}\n")
        print(f"  Cloudflare IP scanner for restricted networks.")
        print(f"  Finds working edge IPs and tests download speed.\n")
        print(f"  {BOLD}Features:{RST}")
        print(f"  • Phase 1: fast connectivity scan (TLS + HTTP)")
        print(f"  • Phase 2: download speed test on best IPs")
        print(f"  • Config modifier: generate V2Ray configs with clean IPs")
        print(f"  • Max latency threshold filter")
        print(f"  • Export: CSV, JSON, plain IP list")
        print(f"  • Auto-update Cloudflare IP ranges from cloudflare.com")
        print(f"  • Copy best IP to clipboard")
        print(f"  • Automatic neighbor scanning")
        print(f"  • Persistent settings\n")
        print(f"  {ORA}{BOLD}made by hazard{RST}")
        print(f"  {DIM}{GITHUB}{RST}")
        print(f"  {DIM}v{VERSION}{RST}")
        if au:
            try:
                latest = au.get_latest_version()
                print(f"  {DIM}Latest: {latest}{RST}")
            except: pass
        print(f"\n  {DIM}Press any key...{RST}")
        sys.stdout.flush(); _read_key()

    def _msg(self, txt):
        cls(); print(banner_str(small=True)); print(f"  {txt}")
        print(f"\n  {DIM}Press any key...{RST}"); sys.stdout.flush(); _read_key()

    def _flash(self, txt):
        goto(40, 1); sys.stdout.write(f"  {txt}"); sys.stdout.flush(); time.sleep(1)


if __name__ == "__main__":
    App().run()
