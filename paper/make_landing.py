# -*- coding: utf-8 -*-
import io
import os
import re

PAPER = os.path.dirname(os.path.abspath(__file__))
BDA = os.path.dirname(PAPER)
OUT = os.path.join(PAPER, "index.html")

t = io.open(os.path.join(BDA, "index.html"), encoding="utf-8").read()

SUB = [
    ('<html lang="id">', '<html lang="en">'),
    ('content="Pipeline Big Data surveilans genomik Influenza A: '
     '1.586.912 sekuens NCBI diproses dengan Hadoop, YARN, MapReduce, '
     'Spark, dan Neo4j."',
     'content="Big Data pipeline for Influenza A genomic surveillance: '
     '1,586,912 NCBI sequences processed with Hadoop, YARN, MapReduce, '
     'Spark and Neo4j."'),
    ("<title>Pipeline Genom Influenza A</title>",
     "<title>Influenza A Genome Pipeline</title>"),

    ("<h1>Pipeline Genom Influenza A</h1>",
     "<h1>Influenza A Genome Pipeline</h1>"),
    ("""      <span class="kop">COMP8035041 &middot; Big Data Analytics<br>
        Magister Teknik Informatika &middot; BINUS Graduate Program</span>""",
     """      <span class="kop">COMP8035041 &middot; Big Data Analytics<br>
        Master of Computer Science &middot; BINUS Graduate Program</span>"""),
    ('aria-label="Ganti tema tampilan">tema: sistem</button>',
     'aria-label="Change colour theme">theme: system</button>'),

    ("""  <p class="lede">Pipeline menyeluruh atas <b>1.586.912 sekuens</b> genom
    Influenza A dari NCBI: dari pengambilan data, penyimpanan di HDFS,
    pemrosesan dengan MapReduce dan Spark di atas YARN, klasifikasi dengan
    Spark MLlib, sampai <i>graph analytics</i> di Neo4j.</p>""",
     """  <p class="lede">An end-to-end pipeline over <b>1,586,912 Influenza A
    genome sequences</b> from NCBI: retrieval, storage on HDFS, processing
    with MapReduce and Spark on YARN, classification with Spark MLlib, and
    <i>graph analytics</i> in Neo4j.</p>"""),

    ("  <h2>Jelajahi</h2>", "  <h2>Explore</h2>"),
    ("""      <span class="t">Atlas interaktif &rarr;</span>
      <span class="d">Dashboard lima halaman: arsip, mutu dan ketepatan waktu,
        keragaman, graf kemiripan, dan reassortment. Lima diagram jaringan.</span>""",
     """      <span class="t">Interactive atlas &rarr;</span>
      <span class="d">A five-page dashboard: archive, quality and timeliness,
        diversity, similarity graph, and reassortment. Five network
        diagrams.</span>"""),
    ("""      <span class="t">Kode sumber &rarr;</span>
      <span class="d">Delapan notebook pipeline, Docker Compose, konfigurasi
        Hadoop, dan skrip analisis lanjutan.</span>""",
     """      <span class="t">Source code &rarr;</span>
      <span class="d">Eight pipeline notebooks, Docker Compose, the Hadoop
        configuration, and the downstream analysis scripts.</span>"""),

    ("  <h2>Angka utama</h2>", "  <h2>Headline figures</h2>"),
    ("""    <div><span class="k">Sekuens</span><span class="v">1.586.912</span>
      <span class="n">dari 172 negara</span></div>
    <div><span class="k">Wakil unik</span><span class="v">893.599</span>
      <span class="n">43,69% duplikat</span></div>
    <div><span class="k">Basa</span><span class="v">2,57 Gb</span>
      <span class="n">nukleotida</span></div>
    <div><span class="k">Tepi graf</span><span class="v">358.212</span>
      <span class="n">8 segmen</span></div>
    <div><span class="k">Kandidat</span><span class="v">1.990</span>
      <span class="n">reassortment</span></div>
    <div><span class="k">Spesies inang</span><span class="v">601</span>
      <span class="n">tercatat</span></div>""",
     """    <div><span class="k">Sequences</span><span class="v">1,586,912</span>
      <span class="n">from 172 countries</span></div>
    <div><span class="k">Unique representatives</span><span class="v">893,599</span>
      <span class="n">43.69% duplicated</span></div>
    <div><span class="k">Bases</span><span class="v">2.57 Gb</span>
      <span class="n">nucleotides</span></div>
    <div><span class="k">Graph edges</span><span class="v">358,212</span>
      <span class="n">8 segments</span></div>
    <div><span class="k">Candidates</span><span class="v">1,990</span>
      <span class="n">reassortment</span></div>
    <div><span class="k">Host species</span><span class="v">601</span>
      <span class="n">recorded</span></div>"""),

    ("  <h2>Temuan</h2>", "  <h2>Findings</h2>"),
    ('<thead><tr><th>Hasil</th><th class="n">Nilai</th></tr></thead>',
     '<thead><tr><th>Result</th><th class="n">Value</th></tr></thead>'),
    ("""      <tr><td>Klasifikasi segmen, F1 makro</td><td class="n">0,9998</td></tr>
      <tr><td>Subtipe dari HA dan NA</td><td class="n">0,9654</td></tr>
      <tr><td>Subtipe dari segmen internal saja</td><td class="n">0,8678</td></tr>
      <tr><td>MapReduce vs Spark, komputasi identik</td>
          <td class="n">42,4 s vs 65,7 s</td></tr>
      <tr><td>scikit-learn satu node</td>
          <td class="n">gagal dari 25% data</td></tr>
      <tr><td>Pengayaan kandidat pada babi, OR Mantel-Haenszel</td>
          <td class="n">10,86</td></tr>""",
     """      <tr><td>Segment classification, macro F1</td><td class="n">0.9998</td></tr>
      <tr><td>Subtype from HA and NA</td><td class="n">0.9654</td></tr>
      <tr><td>Subtype from internal segments only</td><td class="n">0.8678</td></tr>
      <tr><td>MapReduce vs Spark, identical computation</td>
          <td class="n">42.4 s vs 65.7 s</td></tr>
      <tr><td>scikit-learn on a single node</td>
          <td class="n">fails from 25% of the data</td></tr>
      <tr><td>Candidate enrichment in swine, Mantel&ndash;Haenszel OR</td>
          <td class="n">10.86</td></tr>"""),

    ("  <h2>Menjalankan sendiri</h2>", "  <h2>Running it yourself</h2>"),
    ("""  <p>Kredensial tidak ikut repositori. Siapkan dua berkas lebih dulu, lalu
    nyalakan klaster:</p>""",
     """  <p>Credentials are not committed to the repository. Prepare two files
    first, then bring the cluster up:</p>"""),
    ("""  <p style="margin-top:14px">Jalankan notebook <code>00_setup.ipynb</code>
    sekali; ia membuat <code>nb/bda_secret.json</code> dari contoh dan
    memberi tahu bidang mana yang perlu diisi. Zona data tidak ikut
    repositori karena berukuran ratusan megabita dan dapat dibangun ulang
    dengan menjalankan notebook 01 sampai 06 berurutan.</p>""",
     """  <p style="margin-top:14px">Run <code>00_setup.ipynb</code> once; it
    creates <code>nb/bda_secret.json</code> from the template and reports
    which fields still need values. The data zones are not committed because
    they run to hundreds of megabytes, and they can be rebuilt by running
    notebooks 01 through 06 in order.</p>"""),

    ("""    <p>Sumber data: NCBI Influenza Virus Database. Seluruh angka dihitung
      dari zona data lake proyek ini, bukan disalin dari literatur.</p>
    <p>Graf kemiripan dan kandidat reassortment dibangun atas sampel maksimum
      2.500 simpul per segmen. Pengukuran kinerja dilakukan pada satu mesin
      fisik, sehingga perbandingan relatif antar mesin pemrosesan sah tetapi
      angkanya tidak dapat digeneralisasi ke klaster produksi.</p>""",
     """    <p>Data source: NCBI Influenza Virus Database. Every figure was
      computed from this project's data lake zones rather than copied from
      the literature.</p>
    <p>The similarity graph and the reassortment candidates were built on a
      sample of at most 2,500 nodes per segment. Performance was measured on
      a single physical host, so relative comparisons between processing
      engines are valid but the absolute figures cannot be generalised to a
      production cluster.</p>"""),

    ('''  var b=document.getElementById("tema"), urut=["sistem","terang","gelap"];
  function baca(){ try{ return localStorage.getItem("tema-bda")||"sistem"; }
    catch(e){ return "sistem"; } }
  function terap(v){
    var r=document.documentElement;
    if(v==="terang") r.setAttribute("data-theme","light");
    else if(v==="gelap") r.setAttribute("data-theme","dark");
    else r.removeAttribute("data-theme");
    b.textContent="tema: "+v;
  }''',
     '''  var b=document.getElementById("tema"), urut=["system","light","dark"];
  function baca(){ try{ return localStorage.getItem("theme-bda-en")||"system"; }
    catch(e){ return "system"; } }
  function terap(v){
    var r=document.documentElement;
    if(v==="light") r.setAttribute("data-theme","light");
    else if(v==="dark") r.setAttribute("data-theme","dark");
    else r.removeAttribute("data-theme");
    b.textContent="theme: "+v;
  }'''),
    ('try{ localStorage.setItem("tema-bda",kini); }catch(e){}',
     'try{ localStorage.setItem("theme-bda-en",kini); }catch(e){}'),
]

for a, b in SUB:
    if a not in t:
        raise SystemExit("pattern not found:\n" + a[:220])
    t = t.replace(a, b, 1)

io.open(OUT, "w", encoding="utf-8").write(t)

print("written :", OUT)
print("size    : %.1f KB" % (len(t) / 1024))
print("doctype :", t.startswith("<!doctype html>"))
for tag in ("html", "head", "body", "style", "script", "header", "footer"):
    o = len(re.findall("<" + tag + r"[\s>]", t))
    c = len(re.findall("</" + tag + ">", t))
    print("  %-7s %d / %d %s" % (tag, o, c, "" if o == c else "<<< MISMATCH"))

ID = (r"\b(dari|untuk|dengan|yang|tidak|sekuens|jumlah|nilai|tema|sistem|"
      r"terang|gelap|halaman|negara|inang|subtipe|kemiripan|klaster|tepi|"
      r"simpul|wilayah|rekaman|sampel|batas|babi|kandidat|arsip|mutu|"
      r"keragaman|jelajahi|temuan|hasil|basa|galur|segmen|duplikat|"
      r"kredensial|repositori|notebook|berkas|angka|utama|sumber|data)\b")
hit = sorted(set(w.lower() for w in re.findall(ID, t, re.I)))
hit = [h for h in hit if h not in ("data", "notebook")]
print("indonesian tokens:", hit if hit else "none")
