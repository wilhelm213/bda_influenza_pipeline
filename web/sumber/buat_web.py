import io
import json
import os
import re
import shutil

SP = os.path.dirname(os.path.abspath(__file__))
WEB = r"D:\BDA\web"
os.makedirs(WEB, exist_ok=True)

tpl = io.open(os.path.join(SP, "situs_tpl.html"), encoding="utf-8").read()
data = json.load(io.open(os.path.join(SP, "insight.json"), encoding="utf-8"))

i = tpl.index("</style>") + len("</style>")
kepala, badan = tpl[:i], tpl[i:]

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

badan = badan.replace(
    '<span class="sub">',
    '<button class="tema" id="tema" type="button" '
    'aria-label="Ganti tema tampilan">tema: sistem</button>\n      '
    '<span class="sub">', 1)

JS_TEMA = """

(function(){
  var b=document.getElementById("tema"), urut=["sistem","terang","gelap"];
  function baca(){ try{ return localStorage.getItem("tema-atlas")||"sistem"; }
    catch(e){ return "sistem"; } }
  function terap(v){
    var r=document.documentElement;
    if(v==="terang") r.setAttribute("data-theme","light");
    else if(v==="gelap") r.setAttribute("data-theme","dark");
    else r.removeAttribute("data-theme");
    b.textContent="tema: "+v;
  }
  var kini=baca(); terap(kini);
  b.addEventListener("click",function(){
    kini=urut[(urut.indexOf(kini)+1)%urut.length];
    try{ localStorage.setItem("tema-atlas",kini); }catch(e){}
    terap(kini);
  });
})();
"""
badan = badan.replace("show(tok());", "show(tok());\n" + JS_TEMA, 1)

html = ('<!doctype html>\n<html lang="id">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,'
        'viewport-fit=cover">\n'
        '<meta name="description" content="Atlas genom Influenza A: '
        '1.586.912 sekuens NCBI diproses dengan Hadoop, Spark, dan Neo4j.">\n'
        + RESET + kepala + TOMBOL + '\n</head>\n<body>\n'
        + badan.strip() + '\n</body>\n</html>\n')

html = html.replace("__DATA__", json.dumps(
    json.load(io.open(os.path.join(SP, "paket_data.json"), encoding="utf-8")),
    ensure_ascii=False, separators=(",", ":")))

out = os.path.join(WEB, "index.html")
io.open(out, "w", encoding="utf-8").write(html)

io.open(os.path.join(WEB, ".nojekyll"), "w", encoding="utf-8").write("")

print("ditulis   :", out)
print("ukuran    : %.1f KB" % (len(html) / 1024))
print("doctype   :", html.startswith("<!doctype html>"))
print("placeholder tersisa:", html.count("__DATA__"))
for tag in ("html", "head", "body", "style", "script", "header", "main"):
    o = len(re.findall(r"<" + tag + r"[\s>]", html))
    c = len(re.findall(r"</" + tag + r">", html))
    print("  %-7s %d / %d %s" % (tag, o, c, "" if o == c else "<<< TIMPANG"))
m = re.findall(r"<script>(.*?)</script>", html, re.S)
js = "".join(m)
for a, b in (("{", "}"), ("(", ")"), ("[", "]")):
    print("  js %s%s %d / %d %s" % (a, b, js.count(a), js.count(b),
                                    "" if js.count(a) == js.count(b) else "<<<"))