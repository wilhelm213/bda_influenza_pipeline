import glob
import io
import json
import os
import re

SP = os.path.dirname(os.path.abspath(__file__))
ins = json.load(io.open(os.path.join(SP, "insight.json"), encoding="utf-8"))
babi = json.load(io.open(os.path.join(SP, "babi.json"), encoding="utf-8"))

tahap = {}
for f in glob.glob(r"D:\BDA\audit\*.jsonl"):
    for ln in io.open(f, encoding="utf-8").read().strip().splitlines():
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("status", "").startswith("OK") and d.get("detik"):
            k = (d.get("lapisan", "?"), d.get("tahap", "?"))
            tahap[k] = max(tahap.get(k, 0), float(d["detik"]))
kinerja = sorted(({"lapisan": k[0], "tahap": k[1], "detik": round(v, 1)}
                  for k, v in tahap.items()),
                 key=lambda r: -r["detik"])[:14]

def bersih(rows, kunci):
    return [r for r in rows if r.get(kunci) is not None]

D = {
    "ringkas": ins["ringkas"],
    "rilis": [[r["tahun_rilis"], r["count"]]
              for r in bersih(ins["per_tahun_rilis"], "tahun_rilis")],
    "koleksi": [[r["tahun_koleksi"], r["count"]]
                for r in bersih(ins["per_tahun_koleksi"], "tahun_koleksi")],
    "dup": ins["duplikat_ember"],
    "jeda": ins["jeda_ringkas"],
    "jeda_seb": [[r["jeda"], r["count"]] for r in ins["jeda_sebaran"]],
    "jeda_tren": [[r["tahun_koleksi"], round(float(r["rata"]), 3), r["n"]]
                  for r in ins["jeda_per_tahun"]],
    "presisi": ins["presisi_tanggal"],
    "kelengkapan": ins["kelengkapan"],
    "sumber_sub": ins["sumber_subtipe"],
    "sumber_seg": ins["sumber_segmen"],
    "ambigu": ins["ambigu_ember"],
    "rongga": ins["rongga"],
    "segmen": bersih(ins["per_segmen"], "segmen"),
    "seg_nol": [r for r in ins["per_segmen"] if r.get("segmen") is None],
    "subtipe": ins["per_subtipe"],
    "negara": bersih(ins["per_negara"], "negara"),
    "wilayah": ins["per_wilayah"],
    "inang": bersih(ins["per_inang"], "inang"),
    "sub_tahun": ins["subtipe_tahun"],
    "wil_tahun": ins["wilayah_tahun"],
    "inang_sub": ins["inang_subtipe"],
    "graf_seg": ins["graf_per_segmen"],
    "graf_tepi": ins["graf_total_tepi"],
    "klaster_seg": ins["klaster_per_segmen"],
    "klaster_uk": ins["klaster_ukuran"],
    "klaster_top": ins["klaster_terbesar"],
    "co_total": ins["co_total"],
    "co_pasang": ins["co_pasangan_segmen"],
    "co_top": ins["co_teratas"],
    "kd": ins["kandidat_ringkas"],
    "kd_seg": ins["kandidat_per_segmen"],
    "kd_wil": ins["kandidat_per_wilayah"],
    "kd_tahun": ins["kandidat_per_tahun"],
    "kd_inang": bersih(ins["kandidat_per_inang"], "inang"),
    "kd_silang": ins["kandidat_silang"],
    "kd_yakin": ins["kandidat_keyakinan"],
    "kd_top": ins["kandidat_teratas"],
    "babi": babi,
    "kinerja": kinerja,
}

pg = os.path.join(SP, "graf.json")
if os.path.exists(pg):
    g = json.load(io.open(pg, encoding="utf-8"))
    D["co_semua"] = g.get("co_semua")
    D["sub_klaster"] = g.get("sub_klaster")
    print("graf penuh disertakan: %d tepi co-occurs" % len(D["co_semua"] or []))
else:
    print("graf.json belum ada -- dashboard memakai 20 tepi terkuat")

json.dump(D, io.open(os.path.join(SP, "paket_data.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

TPL = io.open(os.path.join(SP, "situs_tpl.html"), encoding="utf-8").read()
html = TPL.replace("__DATA__",
                   json.dumps(D, ensure_ascii=False, separators=(",", ":")))
out = os.path.join(SP, "atlas-influenza.html")
io.open(out, "w", encoding="utf-8").write(html)
print("ditulis:", out, "|", round(len(html) / 1024, 1), "KB")
print("tahap kinerja teratas:",
      ", ".join("%s %.0fs" % (r["tahap"][:26], r["detik"]) for r in kinerja[:4]))
