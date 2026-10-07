# Atlas Genom Influenza A

Dashboard lima halaman atas 1.586.912 sekuens Influenza A dari NCBI.

## Isi

| Berkas | |
|---|---|
| `index.html` | Seluruh situs, satu berkas, data tertanam |
| `.nojekyll` | Menonaktifkan Jekyll pada GitHub Pages |
| `sumber/` | Skrip pembangun |

Tautan halaman: `#arsip`, `#mutu`, `#ragam`, `#graf`, `#reasort`.

## Menjalankan lokal

Klik dua kali `index.html`.

## GitHub Pages

```bash
git init
git add .
git commit -m "Atlas Genom Influenza A"
git branch -M main
git remote add origin https://github.com/<akun>/<repo>.git
git push -u origin main
```

Settings → Pages → Deploy from a branch → `main` / root → Save.
URL: `https://<akun>.github.io/<repo>/`. Repositori harus publik.

## Alternatif

Cloudflare Pages, Netlify Drop, atau webspace mana pun. Satu berkas statis.

## Memperbarui data

```bash
docker cp sumber/tarik_insight.py bda-jupyter:/tmp/tarik_insight.py
docker exec bda-jupyter python3 /tmp/tarik_insight.py
docker cp bda-jupyter:/tmp/insight.json ./insight.json

docker cp sumber/babi.py bda-jupyter:/tmp/babi.py
docker exec bda-jupyter python3 /tmp/babi.py
docker cp bda-jupyter:/tmp/babi.json ./babi.json

python buat_situs.py
python buat_web.py
```

## Graf penuh

```bash
docker cp sumber/tarik_graf.py bda-jupyter:/tmp/tarik_graf.py
docker exec bda-jupyter python3 /tmp/tarik_graf.py
docker cp bda-jupyter:/tmp/graf.json ./graf.json
python buat_situs.py && python buat_web.py
```

## Berkas di `sumber/`

| Skrip | Fungsi |
|---|---|
| `tarik_insight.py` | Agregat dari zona HDFS |
| `babi.py` | Pengayaan kandidat per inang |
| `tarik_graf.py` | Graf penuh untuk diagram jaringan |
| `situs_tpl.html` | Templat halaman |
| `buat_situs.py` | Paket data |
| `buat_web.py` | Dokumen HTML utuh |
| `validasi_palet.py` | Validator palet grafik |

```bash
python sumber/validasi_palet.py
```

## Batas

| Batas | |
|---|---|
| Graf kemiripan dan kandidat | sampel maksimum 2.500 simpul per segmen |
| Kinerja | satu mesin fisik |
