# Panduan Operator ProPresenter — Kebaktin Minggu GBKP

Tata penulisan & penamaan lengkap: `TATA_PENULISAN.md` (di folder skill yang sama).

## 1. Cara kerja mingguan

1. Di Claude Code, ketik `/propresenter-liturgi:propresenter-liturgi` (atau cukup minta "buatkan playlist ProPresenter dari liturgi ini") dan lampirkan PDF liturgi. ProPresenter harus terbuka dengan
   **Settings → Network → Enable Network** menyala.
2. Claude akan membuat folder `Liturgi/<YYYY-MM-DD> Minggu <Tema>/` (berisi `Playlist.txt` dan `.txt` per item),
   memakai ulang item Library, membuat hanya item yang belum ada, lalu membuat playlist `<YYYY-MM-DD> · Minggu <Tema>`.
3. Buka playlist itu dan klik setiap item sekali dari atas ke bawah untuk mengecek teks muat di layar.
4. Header merah **⚠ BELUM ADA: …** artinya teksnya tidak ada di PDF (lirik lagu pra-ibadah, dll.). Buat item
   `Lagu – <Judul>` di Library, seret ke bawah header itu, lalu hapus header merahnya.

## 2. Isi Library (setelah dirapikan)

| Jenis | Contoh | Keterangan |
|---|---|---|
| Lagu | `KEE 424 – Ipuji Kami Kam Dibata Si Mbelin` | Semua ayat yang pernah dipakai. Ayat minggu itu dipilih lewat **arrangement** (`1,3`). |
| Bacaan | `Titus 2∶3-5`, `Kejadin 24∶50-67` | Dipakai lagi bila perikop sama muncul. |
| Mingguan | `2026-10-18 · 05 Pujin Man Dibata …` | Berurutan per tanggal & nomor liturgi di Library. |
| Tetap | `Perpulungen Tedis/Kundul`, `Erkata Lonceng`, `Kata Dibata Sipemena`, `Kata Dibata – Haleluya`, `Pengakun Kiniteken`, `Pertoton Tuhan`, … | Selalu dipakai ulang. |

**Warna grup:** abu = Judul · biru = Liturgos · hijau = Perpulungen · merah tua = Moria · tosca = Mamre & Permata ·
kuning = Bersama · ungu = Ayat lagu · merah muda = Reff · oranye = bacaan Alkitab.

## 3. Arrangement

- Lagu menyimpan setiap ayat dan Reff **sekali saja**. Arrangement mengatur urutannya, misalnya `1,3` = Judul → Ayat 1 →
  Reff → Ayat 3 → Reff. "Master" = semua slide berurutan.
- Di playlist, arrangement sudah dipilih otomatis per item. Ganti lewat menu arrangement di kepala item.
- Ayat yang belum ada di item lagu: buka item → **Reflow** → tambahkan `[Ayat 2]` + liriknya → buat arrangement baru.

## 4. Reflow Editor

Buka item → tombol **Reflow**. Baris kosong = slide baru, `[Nama Grup]` di baris sendiri = grup baru. Dipakai untuk
memecah slide yang padat, memperbaiki salah ketik, dan menempel lirik. Perubahan tersimpan permanen di Library.

## 5. Saat ibadah

- **Clear Slide (F2)** menghapus teks, background tetap. Pakai di antara bagian dan saat doa/khotbah.
- **Clear All (F1)** mengosongkan layar total. Pakai di akhir ibadah atau saat ada gangguan.
- **Clear Media (F3)** menghapus background saja. Cek tombol Clear di bawah Preview bila shortcut ProPresenter 22 berbeda.
- Pakai transisi Dissolve ±0,5 detik agar pergantian background halus.
- **Urutan dilompati:** klik header/item tujuan di playlist (nomor header = nomor liturgi). Jangan Clear All.
  Bila lagu diulang, klik slide Reff lagi. Saat Teduh/Announcement bisa dipakai untuk menutup jeda.
