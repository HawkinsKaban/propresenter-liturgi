# Tata Penulisan & Penamaan — Liturgi ProPresenter (GBKP)

Berlaku untuk setiap liturgi baru. `liturgi2pro.py` memberi tanda ✎ pada nama yang tidak sesuai.

## 1. Nama item di Library

| Jenis | Pola | Contoh | Dipakai ulang? |
|---|---|---|---|
| Lagu | `KEE <no> – <Judul Lagu>` | `KEE 308 – Puji Tuhan Haleluya` | Ya. 1 lagu = 1 item, ayat dipilih lewat arrangement |
| Lagu non-KEE (pra-ibadah, pujian) | `Lagu – <Judul>` | `Lagu – Lebih dari Pemenang` | Ya |
| Bacaan Alkitab | `<Kitab> <pasal>:<ayat>` (nama kitab seperti tertulis di liturgi, tanpa spasi di sekitar `:`) | `Titus 2:3-5`, `2 Raja-raja 4:38-41`, `Perbahanen Rasul-rasul 27:33-38` | Ya, setiap kali perikop itu muncul |
| Bagian liturgi mingguan | `<YYYY-MM-DD> · <NN> <Nama Bagian>` (NN = nomor urut liturgi, 2 digit) | `2026-10-18 · 03 Votum – Salam`, `2026-10-18 · 05 Pujin Man Dibata si Mperdiateken Kegeluhen Manusia` | Tidak, khusus minggu itu |
| Kartu mingguan (persembahan pujian, khotbah) | `<YYYY-MM-DD> · <Nama>` | `2026-10-18 · Persembahan Pujian PJJ Sektor Nazareth`, `2026-10-18 · Khotbah` | Tidak |
| Kartu/teks tetap | nama baku | `Perpulungen Tedis`, `Perpulungen Kundul`, `Erkata Lonceng`, `Kata Pengalo-ngalo ras Momo`, `Kata Dibata Sipemena`, `Kata Dibata – Haleluya`, `Pengakun Kiniteken`, `Pertoton Persembahen ras Syafaat`, `Pertoton Tuhan`, `Paksa Teneng`, `Saat Teduh`, `Countdown`, `Announcement` | Ya, selalu |

- Pemisah judul memakai en dash ` – ` (Votum – Salam). Penanggalan memakai ` · `.
- Huruf kapital di awal setiap kata, **kecuali** kata sambung Karo/Indonesia: `ras, si, i, bas, man, ku, kerna, dingen, dan, di, ke`.
  Kata pertama selalu kapital. Judul lagu ditulis seperti di buku KEE.
- Tanpa HURUF BESAR SEMUA, tanpa spasi ganda.

## 2. Playlist

- Nama: `<YYYY-MM-DD> · Minggu <Tema>` → `2026-10-18 · Minggu Moria`.
- Header: `A. Persikapen`, lalu `1. Kata Pengalo-ngalo ras Momo` … `13. Pengutusen ras Pasu-pasu Dibata`, dan `Penutup`.
  Judul header = judul bagian di liturgi (dirapikan dengan aturan kapital di atas).
- Urutan item di bawah header: kartu sikap (`Perpulungen Tedis/Kundul`) → teks bagian itu → lagu.

## 3. Folder & file

```
Liturgi/
  2026-10-18 Minggu Moria/
    Playlist.txt
    2026-10-18 · 03 Votum – Salam.txt
    KEE 57 – Nggo Kita Pulung I Lebe.txt
    Titus 2∶3-5.txt                 (":" di nama file ditulis "∶")
    Panduan Operator.md
```
Nama file `.txt` = nama item. File hanya dipakai bila item belum ada di Library.

## 4. Isi slide (`.txt`)

- 1 baris kosong = slide baru. Penanda `[..]` berlaku sampai penanda berikutnya. Baris dibungkus otomatis (≤36 huruf, ≤4 baris/slide).
- Penanda peran (label kiri atas = penanda dalam huruf besar):
  `[Judul]` kartu judul · `[Liturgos]` (L) · `[Perpulungen]` (P) · `[Moria]` · `[Mamre & Permata]` · `[Bersama]` ·
  bacaan: `[Titus 2:3-5]` dengan nomor ayat di awal teks (`3. Bage pe …`).
- Lagu: `[Judul]` berisi `KEE No. 308` + baris `“Judul Lagu”` (tanpa nomor ayat, karena ayat dipilih lewat arrangement),
  lalu `[Ayat 1]`, `[Reff]`, `[Ayat 3]`, `[Reff]` … dalam urutan yang dinyanyikan; tulis semua ayat yang tercetak.
  Reff yang diulang ditulis ulang lengkap. Generator menyimpannya sekali dan mengulang lewat arrangement.
- Kartu judul bagian: `[Judul]` + nama bagian (1–3 baris); `(Perpulungen Kundul)` tidak ditulis di sini, karena itu item tersendiri.
- Kutipan ayat: “…” lalu referensi pada baris sendiri, mis. `(Msm. 131:2)`, `(Bdk. Kua. 31:31)`. Singkatan kitab seperti di liturgi,
  spasi baku `Kitab. pasal:ayat`.
- Respons jemaat baku: `Amin... Amin... Amin` dan `Haleluya... Haleluya... Haleluya`.
- `(Paksa Teneng)` ditulis sebagai kartu `[Judul]` `Paksa Teneng` di dalam item.
- Buang: nomor halaman, `(iendeken)`, `(Ngogeken Momo)`, `(Tunggal)`, `(Serayan … bengket ku mimbar)`, `(ibenai ras idungi alu pertoton)`.
- Rapikan hanya kerusakan PDF: spasi di tengah kata bersambung (`itengah- tengah` → `itengah-tengah`), spasi ganda,
  tanda kutip/titik ganda. **Jangan** mengubah kata Karo yang tidak pasti salah — catat sebagai keraguan.
- **Jangan mengarang** teks yang tidak tercetak (Pengakuan Iman, Doa Bapa Kami, lirik lagu pra-ibadah, isi Momo).
- Lirik yang tercetak dua kolom (baris terakhir ayat terpisah dari ayatnya) disusun kembali menurut rima/arti, lalu dilaporkan.
