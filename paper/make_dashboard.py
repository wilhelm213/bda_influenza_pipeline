# -*- coding: utf-8 -*-
import io
import json
import os
import re

PAPER = os.path.dirname(os.path.abspath(__file__))
BDA = os.path.dirname(PAPER)
SRC = os.path.join(BDA, "web", "sumber")

tpl = io.open(os.path.join(SRC, "situs_tpl.html"), encoding="utf-8").read()
isi = io.open(os.path.join(PAPER, "dashboard_content.js"),
              encoding="utf-8").read()

A = tpl.index("const R=D.ringkas")
B = tpl.index("const SEGLEN")
head, tail = tpl[:A], tpl[B:]

HEAD_SUB = [
    ('new Intl.NumberFormat("id-ID")', 'new Intl.NumberFormat("en-US")'),
    ("<title>Atlas Genom Influenza A</title>",
     "<title>Influenza A Genome Atlas</title>"),
    ('(o.judul||"nilai")', '(o.judul||"value")'),
    ('(o.judul||"seri")', '(o.judul||"series")'),
    ('(o.judul||"tepi")', '(o.judul||"edge")'),
    ('"</b> sekuens pada seluruh rentang"',
     '"</b> sequences across the whole range"'),
    ('" dari total"', '" of total"'),
    ('<span class="tl">tepi co-occurs</span>',
     '<span class="tl">co-occurrence edge</span>'),
    ('"</b> galur berbagi kedua klaster"',
     '"</b> strains share both clusters"'),
    ('<span class="tl">klaster segmen ',
     '<span class="tl">cluster, segment '),
    ('"</b> tepi &middot; <b>"', '"</b> edges &middot; <b>"'),
    ('"</b> galur terkumpul"', '"</b> strains in total"'),
    (')\"></i>Segmen \'+g+" "', ')\"></i>Segment \'+g+" "'),
    ('" klaster</b></div>"', '" clusters</b></div>"'),
    ('<span class="tl">simpul</span>', '<span class="tl">node</span>'),
    ('"</b> tepi");});', '"</b> edges");});'),
]

HEADER_ID = head[head.index('<header class="top">'):
                 head.index('<main id="main"></main>')]

HEADER_EN = """<header class="top">
  <div class="tw">
    <a class="beranda" href="../index.html"><svg viewBox="0 0 24 24" \
fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" \
stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5"/><path \
d="M12 19l-7-7 7-7"/></svg>Project home</a>
    <div class="peta" id="peta" aria-hidden="true"></div>
    <p class="petacap">The eight segments of the Influenza A genome, drawn to
      their true relative length. HA and NA are highlighted: those two alone
      determine the subtype name &mdash; which is why reassortment in the
      internal segments can pass unnoticed without changing that name.</p>
    <div class="idrow">
      <h1>Influenza A Genome Atlas</h1>
      <span class="meta">1,586,912 sequences &middot; 172 countries &middot;
        1902&ndash;2026</span>
      <button class="tema" id="tema" type="button"
        aria-label="Change colour theme">theme: system</button>
    </div>
    <div class="seqbox">
      <div class="seqlab" id="seqlab"></div>
      <div class="seqwrap">
        <div class="kmer" id="kmer"></div>
        <div class="seq" id="seq"></div>
      </div>
    </div>
    <nav class="tracks" role="tablist" id="nav"></nav>
  </div>
</header>

"""

for a, b in HEAD_SUB:
    if a not in head:
        raise SystemExit("head pattern not found: " + repr(a[:70]))
    head = head.replace(a, b)
head = head.replace(HEADER_ID, HEADER_EN, 1)

TAIL_SUB = [
    ('d.title="Segmen "+n+', 'd.title="Segment "+n+'),
    ('" &middot; segmen 4 HA &middot; "',
     '" &middot; segment 4 HA &middot; "'),
    ('" &middot; jendela "+K+"-mer"', '" &middot; "+K+"-mer window"'),
]
for a, b in TAIL_SUB:
    if a not in tail:
        raise SystemExit("tail pattern not found: " + repr(a[:70]))
    tail = tail.replace(a, b)

p0 = tail.index("const PAGES=[")
PAGES_ID = tail[p0:tail.index("];", p0) + 3]
PAGES_EN = """const PAGES=[
  ["archive","Archive",pgArsip],
  ["quality","Quality & timeliness",pgMutu],
  ["diversity","Diversity",pgRagam],
  ["graph","Graph",pgGraf],
  ["reassortment","Reassortment",pgReasort],
];
"""
tail = tail.replace(PAGES_ID, PAGES_EN, 1)

f0 = tail.index("const FOOT=")
FOOT_ID = tail[f0:tail.index("</p>';", f0) + 6]
FOOT_EN = (
    "const FOOT='<p><b>Data source.</b> NCBI Influenza Virus Database, '+\n"
    "  f(R.sekuens)+' records retrieved and processed through HDFS, YARN, '+\n"
    "  'MapReduce, Spark and Neo4j. Every figure on this site was computed '+\n"
    "  'from the data lake zones rather than copied from the literature.'+\n"
    "  '</p>'+\n"
    "  '<p><b>Limits.</b> The similarity graph and the reassortment '+\n"
    "  'candidates were built on a sample, and performance was measured '+\n"
    "  'on a single physical host. Both constraints are stated on the '+\n"
    "  'pages they affect.</p>';")
tail = tail.replace(FOOT_ID, FOOT_EN, 1)

RESET = """<style>

*,*::before,*::after{box-sizing:border-box}
html{color-scheme:light}
:root{padding-top:env(safe-area-inset-top,0px);
      padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0}
img{max-width:100%}
[hidden]{display:none!important}
</style>
"""

TOMBOL = """
<style>
.tema{appearance:none;background:var(--surface2);color:var(--ink2);
  border:1px solid var(--rule);cursor:pointer;font-family:var(--mono);
  font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;
  padding:5px 10px;margin-left:auto;white-space:nowrap}
.tema:hover{color:var(--ink);border-color:var(--ink3)}
.tema:focus-visible{outline:2px solid var(--akos);outline-offset:1px}
</style>
"""

JS_TEMA = """

(function(){
  var b=document.getElementById("tema"), urut=["system","light","dark"];
  function baca(){ try{ return localStorage.getItem("atlas-theme-en")
    ||"system"; }catch(e){ return "system"; } }
  function terap(v){
    var r=document.documentElement;
    if(v==="light") r.setAttribute("data-theme","light");
    else if(v==="dark") r.setAttribute("data-theme","dark");
    else r.removeAttribute("data-theme");
    b.textContent="theme: "+v;
  }
  var kini=baca(); terap(kini);
  b.addEventListener("click",function(){
    kini=urut[(urut.indexOf(kini)+1)%urut.length];
    try{ localStorage.setItem("atlas-theme-en",kini); }catch(e){}
    terap(kini);
  });
})();
"""
tail = tail.replace("show(tok());</script>",
                    "show(tok());" + JS_TEMA + "</script>", 1)

i = head.index("</style>") + len("</style>")
gaya, badan = head[:i], head[i:]

html = ('<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,'
        'viewport-fit=cover">\n'
        '<meta name="description" content="Influenza A genome atlas: '
        '1,586,912 NCBI sequences processed with Hadoop, Spark and Neo4j.">\n'
        + RESET + gaya + TOMBOL + "\n</head>\n<body>\n"
        + (badan + isi + "\n" + tail).strip() + "\n</body>\n</html>\n")

PAKET = json.load(io.open(os.path.join(SRC, "paket_data.json"),
                          encoding="utf-8"))
STRAT = json.load(io.open(os.path.join(BDA, "web", "stratifikasi.json"),
                          encoding="utf-8"))
PAKET["strat"]["kasar"] = STRAT["kasar"]
kerangka = html
html = html.replace("__DATA__", json.dumps(
    PAKET, ensure_ascii=False, separators=(",", ":")))

WEB = os.path.join(PAPER, "web")
os.makedirs(WEB, exist_ok=True)
out = os.path.join(WEB, "index.html")
io.open(out, "w", encoding="utf-8").write(html)

print("written     :", out)
print("size        : %.1f KB" % (len(html) / 1024))
print("doctype     :", html.startswith("<!doctype html>"))
print("placeholder :", html.count("__DATA__"))
for tag in ("html", "head", "body", "style", "script", "header", "main"):
    o = len(re.findall("<" + tag + r"[\s>]", html))
    c = len(re.findall("</" + tag + ">", html))
    print("  %-7s %d / %d %s" % (tag, o, c, "" if o == c else "<<< MISMATCH"))
js = "".join(re.findall(r"<script>(.*?)</script>", html, re.S))
for a, b in (("{", "}"), ("(", ")"), ("[", "]")):
    print("  js %s%s %d / %d %s" % (a, b, js.count(a), js.count(b),
                                    "" if js.count(a) == js.count(b)
                                    else "<<< MISMATCH"))

ID = (r"\b(dari|untuk|dengan|yang|tidak|segmen|galur|sekuens|jumlah|nilai|"
      r"tema|sistem|terang|gelap|halaman|menurut|bersama|negara|inang|"
      r"subtipe|kemiripan|klaster|tepi|simpul|derajat|pangsa|wilayah|"
      r"dekade|seri|rekaman|sampel|batas|babi|unggas|manusia|kandidat|"
      r"keyakinan|ember|bersih|tunggal|lain)\b")
hit = {}
for mm in re.finditer(ID, kerangka, re.I):
    s = kerangka[max(0, mm.start() - 55):mm.end() + 35].replace("\n", " ")
    hit.setdefault(mm.group(0).lower(), s)
if hit:
    print("\nindonesian tokens in markup/code (%d):" % len(hit))
    for k in sorted(hit):
        print("  %-12s ... %s" % (k, hit[k]))
else:
    print("\nindonesian tokens in markup/code: none")
