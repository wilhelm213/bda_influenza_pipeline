# Naskah artikel (bahasa Indonesia)

Aset untuk naskah artikel jurnal "Penapisan Kandidat Reassortment pada 1,59 Juta
Sekuens Influenza A Menggunakan Klasifikasi Alignment-Free dan Analitik Graf
Terdistribusi".

| Berkas | Isi |
| --- | --- |
| `buat_gambar_metodologi.py` | Membangkitkan diagram alur metodologi |
| `gambar1-metodologi.png` | Gambar 1 pada Bagian 3, 300 DPI |

Jalankan dari mana saja:

```
python naskah/buat_gambar_metodologi.py
```

Skrip hanya butuh `matplotlib`. Lebar tiap baris teks diperiksa terhadap lebar
kotaknya sebelum digambar, sehingga perubahan teks yang membuat tulisan
melimpah akan menghentikan skrip dengan pesan yang menyebut baris penyebabnya,
bukan menghasilkan gambar yang rusak diam-diam.

Angka pada diagram diambil dari keluaran pipeline: `models/metrik_model.csv`,
`models/metrik_skalabilitas.csv`, dan laporan kualitas data pada zona silver.
