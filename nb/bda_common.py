from __future__ import annotations

import gc
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import time
import warnings
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MODE = os.environ.get("BDA_MODE", "lokal").strip().lower()
KLASTER = MODE == "klaster"
HDFS_URI = os.environ.get("BDA_HDFS", "hdfs://namenode:8020").strip()

BASE = Path("/workspace") if KLASTER else Path(r"D:\BDA")

LAKE = BASE / "lake"
STAGE = BASE / "stage"
FEAT = BASE / "features"
MODELS = BASE / "models"
GRAPH = BASE / "graph"
MART = BASE / "mart"
OUT = BASE / "output"

TMP = BASE / "spark_tmp"
CKPT = BASE / "checkpoint"
AUDIT = BASE / "audit"
LOGDIR = BASE / "spark_events"

for _d in (LAKE, STAGE, FEAT, MODELS, GRAPH, MART, OUT, TMP, CKPT, AUDIT, LOGDIR):
    _d.mkdir(parents=True, exist_ok=True)

LAKE_FASTA = LAKE / "fasta"
LAKE_META = LAKE / "meta_csv"
for _d in (LAKE_FASTA, LAKE_META):
    _d.mkdir(parents=True, exist_ok=True)

def jalur(zona: str) -> str:
    zona = zona.strip("/")
    if KLASTER:
        return f"{HDFS_URI}/bda/{zona}"
    return str(BASE / Path(zona))

CFG = {
    "taxid": 11320,

    "spark_master": (os.environ.get("BDA_SPARK_MASTER",
                                    "spark://spark-master:7077").strip()
                     if KLASTER else "local[16]"),
    "driver_memory": "8g" if KLASTER else "32g",

    "executor_memory": "4g",
    "executor_cores": 4,
    "shuffle_part": 256,
    "max_result": "4g",

    "efetch_batch": 500,
    "vv_chunk": 100_000,
    "ncbi_delay": 0.34,
    "ncbi_api_key": None,
    "http_timeout": 600,
    "http_retry": 6,

    "min_len": 500,
    "max_len": 2600,
    "max_ambigu_pct": 5.0,

    "k_utama": 8,
    "k_ablasi": [4, 6, 8, 10],
    "vocab_max": 1 << 18,

    "seed": 42,
    "n_subtipe_teratas": 20,
    "fraksi_uji": 0.2,
    "fraksi_skalabilitas": [0.01, 0.05, 0.25, 0.50, 1.00],

    "lsh_hash": 3,

    "lsh_ambang_jarak": 0.12,

    "lsh_simpul_maks": 2_500,
    "lsh_tepi_maks": 1_500_000,
}

SEGMEN = {
    1: ("PB2", "polymerase basic 2"),
    2: ("PB1", "polymerase basic 1"),
    3: ("PA", "polymerase acidic"),
    4: ("HA", "hemagglutinin"),
    5: ("NP", "nucleoprotein"),
    6: ("NA", "neuraminidase"),
    7: ("M", "matrix"),
    8: ("NS", "nonstructural"),
}
SEG_EKSTERNAL = [4, 6]
SEG_INTERNAL = [1, 2, 3, 5, 7, 8]

PETA_SEGMEN = {
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
    "PB2": 1, "PB1": 2, "PA": 3, "HA": 4, "NP": 5, "NA": 6,
    "M": 7, "MA": 7, "M1": 7, "M2": 7, "MP": 7,
    "NS": 8, "NS1": 8, "NS2": 8,
    "SEGMENT 1": 1, "SEGMENT 2": 2, "SEGMENT 3": 3, "SEGMENT 4": 4,
    "SEGMENT 5": 5, "SEGMENT 6": 6, "SEGMENT 7": 7, "SEGMENT 8": 8,
    "RNA 1": 1, "RNA 2": 2, "RNA 3": 3, "RNA 4": 4,
    "RNA 5": 5, "RNA 6": 6, "RNA 7": 7, "RNA 8": 8,
}

RE_SUBTIPE = re.compile(r"\bH(\d{1,2})N(\d{1,2})\b", re.I)
RE_SEG_DEFLINE = re.compile(r"\bsegment\s+([1-8])\b", re.I)
RE_STRAIN = re.compile(r"\(?(A/[^()]{3,90}?)\s*(?:\((H\d+N\d+)\))?\)?[,\s]", re.I)

def normalisasi_subtipe(nilai) -> str | None:
    if not nilai:
        return None
    m = RE_SUBTIPE.search(str(nilai))
    return f"H{int(m.group(1))}N{int(m.group(2))}" if m else None

def normalisasi_segmen(nilai) -> int | None:
    if nilai is None:
        return None
    s = str(nilai).strip().upper()
    if not s:
        return None
    return PETA_SEGMEN.get(s)

SECRET_PATH = BASE / "nb" / "bda_secret.json"
SECRET_CONTOH = {
    "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "ISI_PASSWORD_MYSQL_ANDA",
        "database": "bda_influenza",
    },
    "neo4j": {
        "user": "neo4j",
        "password": "ISI_PASSWORD_NEO4J_ANDA",
    },
    "ncbi_api_key": "",
}

def muat_secret() -> dict:
    if not SECRET_PATH.exists():
        SECRET_PATH.write_text(
            json.dumps(SECRET_CONTOH, indent=2), encoding="utf-8")
        raise FileNotFoundError(
            f"Berkas kredensial dibuat di {SECRET_PATH}.\n"
            "Isi password MySQL Anda, lalu jalankan ulang sel ini.\n"
            "API key NCBI opsional (gratis di https://www.ncbi.nlm.nih.gov/account/) "
            "dan menaikkan batas dari 3 menjadi 10 permintaan per detik.")
    s = json.loads(SECRET_PATH.read_text(encoding="utf-8"))
    if s.get("ncbi_api_key"):
        CFG["ncbi_api_key"] = s["ncbi_api_key"]
        CFG["ncbi_delay"] = 0.11

    if KLASTER and s.get("mysql", {}).get("host") in ("127.0.0.1", "localhost"):
        s["mysql"] = dict(s["mysql"], host="host.docker.internal")
    return s

def neo4j_auth(secret: dict | None = None) -> tuple[str, str]:
    s = (secret or muat_secret()).get("neo4j") or {}
    return s.get("user", "neo4j"), s.get("password", "")


def mysql_url(secret: dict | None = None) -> str:
    s = (secret or muat_secret())["mysql"]
    return (f"mysql+pymysql://{s['user']}:{s['password']}"
            f"@{s['host']}:{s['port']}/{s['database']}?charset=utf8mb4")

def mysql_jdbc(secret: dict | None = None) -> tuple[str, dict]:
    s = (secret or muat_secret())["mysql"]
    url = (f"jdbc:mysql://{s['host']}:{s['port']}/{s['database']}"
           "?useUnicode=true&characterEncoding=UTF-8&rewriteBatchedStatements=true")
    return url, {"user": s["user"], "password": s["password"],
                 "driver": "com.mysql.cj.jdbc.Driver"}

RUN_ID = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
_JEJAK: list[dict] = []

def _ram():
    try:
        import psutil
        v = psutil.virtual_memory()
        return v.used / 1e9, v.available / 1e9
    except Exception:
        return float("nan"), float("nan")

@contextmanager
def Tahap(nama: str, lapisan: str = "-"):
    t0 = time.time()
    u0, _ = _ram()
    print("\n" + "-" * 68)
    print(f"[>] {lapisan} | {nama}")
    status = "OK"
    try:
        yield
    except Exception as ex:
        status = f"GAGAL {type(ex).__name__}"
        raise
    finally:
        dt = time.time() - t0
        u1, bebas = _ram()
        baris = {"run_id": RUN_ID, "lapisan": lapisan, "tahap": nama,
                 "status": status, "detik": round(dt, 2),
                 "ram_delta_gb": round(u1 - u0, 2),
                 "ram_bebas_gb": round(bebas, 1),
                 "waktu": datetime.now(timezone.utc).isoformat()}
        _JEJAK.append(baris)
        with open(AUDIT / f"{RUN_ID}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(baris) + "\n")
        print(f"[<] {status} | {dt:,.1f} detik | RAM bebas {bebas:,.1f} GB")

def jejak_df():
    import pandas as pd
    return pd.DataFrame(_JEJAK)

_spark = None
_HADOOP_HOME = None

def path_pendek(p) -> str:
    p = str(p)
    if os.name != "nt":
        return p
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        n = ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024)
        return buf.value if n else p
    except Exception:
        return p

def siapkan_java() -> str | None:
    jh = os.environ.get("JAVA_HOME", "").strip()
    if jh and (Path(jh) / "bin" / "java.exe").exists():
        jh = path_pendek(jh)
        os.environ["JAVA_HOME"] = jh
        return jh

    kandidat = []
    for akar in (r"C:\Program Files\Java", r"C:\Program Files\Eclipse Adoptium",
                 r"C:\Program Files\Microsoft", r"C:\Program Files\Amazon Corretto",
                 r"C:\Program Files\Zulu"):
        p = Path(akar)
        if p.is_dir():
            kandidat += [d for d in p.iterdir()
                         if d.is_dir() and (d / "bin" / "java.exe").exists()]

    if not kandidat:
        print("  [!] JDK tidak ditemukan. Pasang JDK 11 atau 17, "
              "lalu setel JAVA_HOME.")
        return None

    def skor(d: Path):

        nama = d.name.lower()
        for v, s in (("17", 3), ("11", 2), ("1.8", 1), ("-8", 1)):
            if v in nama:
                return s
        return 0

    pilih = path_pendek(sorted(kandidat, key=skor, reverse=True)[0])
    os.environ["JAVA_HOME"] = pilih
    os.environ["PATH"] = pilih + r"\bin" + os.pathsep + os.environ.get("PATH", "")
    print(f"  JAVA_HOME  : {pilih}")
    return pilih

def siapkan_spark_home() -> str:
    import pyspark
    sh = path_pendek(Path(pyspark.__file__).parent)
    os.environ["SPARK_HOME"] = sh
    print(f"  SPARK_HOME : {sh}")
    return sh

def siapkan_hadoop() -> str | None:
    hh = os.environ.get("HADOOP_HOME", "").strip()
    calon = [Path(hh)] if hh else []
    calon.append(BASE / "hadoop")
    for c in calon:
        if (c / "bin" / "winutils.exe").exists():
            os.environ["HADOOP_HOME"] = str(c)
            os.environ["hadoop.home.dir"] = str(c)
            os.environ["PATH"] = str(c / "bin") + os.pathsep + os.environ.get("PATH", "")
            return str(c)
    return None

def spark_session(nama: str, memori: str | None = None,
                  master: str | None = None, paket: list[str] | None = None,
                  konfig: dict | None = None):
    global _spark
    if _spark is not None:
        return _spark

    global _HADOOP_HOME
    if not KLASTER:

        siapkan_java()
        siapkan_spark_home()
        _HADOOP_HOME = siapkan_hadoop()

    from pyspark.sql import SparkSession

    nama_aman = re.sub(r"[^A-Za-z0-9._-]+", "-", f"BDA-Influenza-{nama}").strip("-")

    b = (SparkSession.builder
         .appName(nama_aman)
         .master(master or CFG["spark_master"])
         .config("spark.driver.memory", memori or CFG["driver_memory"])
         .config("spark.driver.maxResultSize", CFG["max_result"])
         .config("spark.sql.shuffle.partitions", CFG["shuffle_part"])
         .config("spark.sql.adaptive.enabled", "true")
         .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
         .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
         .config("spark.sql.execution.arrow.pyspark.enabled", "true")
         .config("spark.ui.showConsoleProgress", "true"))

    if KLASTER:
        b = (b.config("spark.executor.memory", CFG["executor_memory"])
              .config("spark.executor.cores", str(CFG["executor_cores"]))

              .config("spark.hadoop.dfs.replication", "2")
              .config("spark.eventLog.enabled", "true")
              .config("spark.eventLog.dir", f"{HDFS_URI}/bda/spark-events")

              .config("spark.driver.host", os.environ.get("HOSTNAME", "jupyter")))
    else:
        b = b.config("spark.local.dir", str(TMP))

        if _HADOOP_HOME:
            b = (b.config("spark.eventLog.enabled", "true")
                  .config("spark.eventLog.dir", LOGDIR.as_uri()))
        else:
            print("  Event log NONAKTIF (winutils.exe tidak ada di mode lokal).")

    if paket:
        b = b.config("spark.jars.packages", ",".join(paket))

    for k, v in (konfig or {}).items():
        b = b.config(k, str(v))

    if KLASTER and not str(master or CFG["spark_master"]).startswith("yarn"):
        periksa_klaster_kosong()

    _spark = b.getOrCreate()
    _spark.sparkContext.setLogLevel("WARN")
    print(f"Spark {_spark.version} | master {_spark.sparkContext.master} | "
          f"driver {memori or CFG['driver_memory']} | "
          f"paralelisme {_spark.sparkContext.defaultParallelism}")
    print(f"Spark UI: {_spark.sparkContext.uiWebUrl}")
    return _spark

def unggah_ke_hdfs(spark, sumber: Path, tujuan: str, pola: str = "*") -> int:
    jvm = spark._jvm
    konf = spark._jsc.hadoopConfiguration()
    JPath = jvm.org.apache.hadoop.fs.Path
    fs = jvm.org.apache.hadoop.fs.FileSystem.get(jvm.java.net.URI(tujuan), konf)
    fs.mkdirs(JPath(tujuan))

    baru = 0
    berkas = sorted(p for p in sumber.glob(pola) if p.is_file())
    for f in berkas:
        dst = JPath(f"{tujuan}/{f.name}")
        if fs.exists(dst):
            continue

        fs.copyFromLocalFile(False, True, JPath(str(f)), dst)
        baru += 1
    print(f"  {sumber.name}: {baru} berkas baru diunggah, "
          f"{len(berkas) - baru} sudah ada -> {tujuan}")
    return baru

def periksa_klaster_kosong(diam: bool = False) -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen("http://spark-master:8080/json/", timeout=8) as r:
            d = json.load(r)
    except Exception:
        return True

    aktif = [a for a in d.get("activeapps", []) if a.get("cores", 0) > 0]
    bebas = d.get("cores", 0) - d.get("coresused", 0)
    if not aktif:
        return True

    if not diam:
        print("  [!] KLASTER SEDANG DIPAKAI aplikasi lain:")
        for a in aktif:
            print(f"        {a['name']}  core={a['cores']}  "
                  f"jalan {a['duration']/1000/60:.0f} menit")
        print(f"      Core bebas: {bebas} dari {d.get('cores', 0)}")
        if bebas == 0:
            print("      Sesi ini akan MENGANTRE tanpa batas waktu.")
            print("      Hentikan sesi notebook lain dulu (jalankan stop_spark()")
            print("      di notebook itu, atau Kernel -> Shutdown Kernel).")
    return bebas > 0

YARN_RM = os.environ.get("BDA_YARN_RM", "resourcemanager:8088")

def yarn_api(jalan: str, timeout: int = 8):
    import urllib.request
    try:
        with urllib.request.urlopen(
                f"http://{YARN_RM}/ws/v1/cluster/{jalan.strip('/')}",
                timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return None

def info_yarn(diam: bool = False) -> dict | None:
    m = yarn_api("metrics")
    if m is None:
        if not diam:
            print(f"  [!] ResourceManager tidak terjangkau di {YARN_RM}.")
            print("      Klaster dinyalakan dengan profil yarn?")
            print("      docker compose --profile yarn up -d")
        return None

    d = m.get("clusterMetrics", {})
    if not diam:
        print(f"  ResourceManager : {YARN_RM}")
        print(f"  NodeManager     : {d.get('activeNodes', 0)} aktif, "
              f"{d.get('lostNodes', 0)} hilang")
        print(f"  Memori          : {d.get('totalMB', 0):,} MB total, "
              f"{d.get('availableMB', 0):,} MB bebas")
        print(f"  vCore           : {d.get('totalVirtualCores', 0)} total, "
              f"{d.get('availableVirtualCores', 0)} bebas")
        print(f"  Aplikasi        : {d.get('appsRunning', 0)} berjalan, "
              f"{d.get('appsCompleted', 0)} selesai, "
              f"{d.get('appsFailed', 0)} gagal")
    return d

def yarn_aplikasi(batas: int = 10):
    import pandas as pd
    d = yarn_api("apps")
    if not d or not d.get("apps"):
        return pd.DataFrame(columns=["id", "name", "applicationType",
                                     "state", "finalStatus"])
    baris = []
    for a in d["apps"].get("app", [])[:batas]:
        baris.append({
            "id": a.get("id"),
            "nama": a.get("name"),
            "jenis": a.get("applicationType"),
            "status": a.get("state"),
            "hasil": a.get("finalStatus"),
            "detik": round(a.get("elapsedTime", 0) / 1000, 1),
            "memori_MB_detik": a.get("memorySeconds"),
            "vcore_detik": a.get("vcoreSeconds"),
        })
    return pd.DataFrame(baris)

def stop_spark():
    global _spark
    if _spark is not None:
        try:
            _spark.stop()
        except Exception:
            pass
        _spark = None
    gc.collect()
    try:
        import psutil
        sisa = [p.pid for p in psutil.process_iter(["name"])
                if "java" in (p.info["name"] or "").lower()]
        print(f"Spark dihentikan. Proses Java tersisa: {len(sisa)}")
    except Exception:
        print("Spark dihentikan.")

def bersihkan_java():
    import subprocess
    import psutil
    pids = [p.pid for p in psutil.process_iter(["name"])
            if "java" in (p.info["name"] or "").lower()]
    if pids:
        subprocess.run(["taskkill", "/F", "/IM", "java.exe"],
                       capture_output=True, text=True)
        time.sleep(3)
    v = _ram()
    print(f"{len(pids)} proses Java dimatikan. RAM bebas {v[1]:,.1f} GB")

def sesi_http():
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": "BDA-Influenza-Pipeline/2.0 (akademik)"})
    return s

def ukuran(p: Path) -> str:
    if not p.exists():
        return "0 B"
    n = (p.stat().st_size if p.is_file()
         else sum(f.stat().st_size for f in p.rglob("*") if f.is_file()))
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {u}"
        n /= 1024
    return f"{n:,.1f} PB"

def ringkas_zona():
    import pandas as pd
    baris = []
    for nama, p in [("lake/fasta", LAKE_FASTA), ("lake/meta_csv", LAKE_META),
                    ("stage", STAGE), ("features", FEAT), ("models", MODELS),
                    ("graph", GRAPH), ("mart", MART), ("output", OUT)]:
        n = len(list(p.rglob("*"))) if p.exists() else 0
        baris.append({"zona": nama, "isi": n, "ukuran": ukuran(p)})
    return pd.DataFrame(baris)

def _sql_lit(v) -> str:

    if hasattr(v, "item") and not isinstance(v, (str, bytes, bool)):
        try:
            v = v.item()
        except Exception:
            pass
    if v is None:
        return "NULL"
    if isinstance(v, float) and v != v:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)

    s = str(v).replace("\\", "\\\\").replace("'", "''")
    return "'" + s + "'"

def df_literal(spark, baris, kolom: list | None = None):
    if not baris:
        raise ValueError("df_literal: tidak ada baris untuk dibangun")
    if isinstance(baris[0], dict):
        if kolom is None:
            kolom = list(baris[0].keys())
        rows = [{k: r.get(k) for k in kolom} for r in baris]
    else:
        if kolom is None:
            raise ValueError("df_literal: `kolom` wajib untuk baris non-dict")
        rows = [dict(zip(kolom, r)) for r in baris]

    tipe = {}
    for k in kolom:
        tipe[k] = "STRING"
        for r in rows:
            v = r.get(k)
            if hasattr(v, "item") and not isinstance(v, (str, bytes, bool)):
                try:
                    v = v.item()
                except Exception:
                    pass
            if v is None or (isinstance(v, float) and v != v):
                continue
            tipe[k] = ("BOOLEAN" if isinstance(v, bool) else
                       "BIGINT" if isinstance(v, int) else
                       "DOUBLE" if isinstance(v, float) else "STRING")
            break

    nilai = ",".join("(" + ",".join(_sql_lit(r.get(k)) for k in kolom) + ")"
                     for r in rows)
    nama = ",".join("`%s`" % k for k in kolom)
    df = spark.sql("SELECT * FROM VALUES %s AS t(%s)" % (nilai, nama))

    from pyspark.sql import functions as _F
    return df.select(*[_F.col("`%s`" % k).cast(tipe[k]).alias(k) for k in kolom])

def simpan_ckpt(nama: str, data: dict):
    (CKPT / f"{nama}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

def muat_ckpt(nama: str, bawaan: dict | None = None) -> dict:
    p = CKPT / f"{nama}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(bawaan or {})

def sha1(teks: str) -> str:
    return hashlib.sha1(teks.encode("utf-8", "ignore")).hexdigest()

def info_mesin():
    import psutil
    v = psutil.virtual_memory()
    d = shutil.disk_usage(str(BASE))
    print(f"CPU logis      : {os.cpu_count()}")
    print(f"RAM total      : {v.total / 1e9:,.1f} GB   bebas {v.available / 1e9:,.1f} GB")
    print(f"Disk D: bebas  : {d.free / 1e9:,.1f} GB dari {d.total / 1e9:,.1f} GB")
    print(f"Python         : {sys.version.split()[0]}")
    print(f"Mode           : {MODE.upper()}" + (f"  ({HDFS_URI})" if KLASTER else "  (Windows lokal)"))
    print(f"run_id         : {RUN_ID}")

__all__ = [
    "MODE", "KLASTER", "HDFS_URI", "jalur",
    "BASE", "LAKE", "LAKE_FASTA", "LAKE_META", "STAGE", "FEAT", "MODELS",
    "GRAPH", "MART", "OUT", "TMP", "CKPT", "AUDIT", "LOGDIR",
    "CFG", "SEGMEN", "SEG_EKSTERNAL", "SEG_INTERNAL", "PETA_SEGMEN",
    "RE_SUBTIPE", "RE_SEG_DEFLINE", "RE_STRAIN",
    "normalisasi_subtipe", "normalisasi_segmen",
    "muat_secret", "mysql_url", "mysql_jdbc", "neo4j_auth", "SECRET_PATH",
    "Tahap", "jejak_df", "RUN_ID",
    "spark_session", "stop_spark", "bersihkan_java", "unggah_ke_hdfs",
    "periksa_klaster_kosong",
    "YARN_RM", "yarn_api", "info_yarn", "yarn_aplikasi",
    "sesi_http", "ukuran", "ringkas_zona", "simpan_ckpt", "muat_ckpt",
    "df_literal",
    "sha1", "info_mesin", "siapkan_java", "siapkan_hadoop",
    "siapkan_spark_home", "path_pendek",
    "Path", "json", "re", "time", "gzip", "gc", "os", "sys", "datetime", "timezone",
]
