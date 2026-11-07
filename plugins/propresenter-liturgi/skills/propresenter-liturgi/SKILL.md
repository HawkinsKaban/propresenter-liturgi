---
name: propresenter-liturgi
description: Ubah PDF/DOCX liturgi ibadah Minggu (GBKP, bahasa Karo/Indonesia) menjadi playlist ProPresenter mingguan yang memakai ulang item Library (1 lagu = 1 presentation dengan arrangement, 1 bacaan = 1 presentation) dan hanya membuat item yang belum ada, dengan tata penulisan & penamaan baku. Pakai saat pengguna memberi file liturgi/tata ibadah dan menyebut ProPresenter, playlist, slide, operator multimedia, atau "/propresenter-liturgi".
argument-hint: "<file liturgi .pdf/.docx>"
---

# Liturgi → ProPresenter (Library + Playlist)

**Wajib baca dulu: [TATA_PENULISAN.md](TATA_PENULISAN.md)** (`${CLAUDE_SKILL_DIR}/TATA_PENULISAN.md`). Ini aturan baku
nama item, playlist, header, folder, dan isi slide. Generator menandai nama yang menyimpang dengan ✎.

Konsep (jangan dilanggar): Library = gudang permanen · 1 lagu = 1 presentation (ayat dipilih lewat arrangement) ·
1 bacaan = 1 presentation · teks liturgi mingguan = item bertanggal · Playlist = susunan satu minggu.
**Jangan pernah** membuat satu presentation untuk satu ibadah.

## Syarat (cek sekali di komputer baru)

- macOS dan `python3` (`python3 --version`; bila belum ada, macOS menawarkan pemasangan Command Line Tools).
- ProPresenter (7.9+ / 21 / 22) **terbuka**, dengan **Settings → Network → Enable Network** menyala. Bila generator tidak
  bisa menghubungi ProPresenter, minta pengguna menyalakannya. Itu pengaturan mereka, jangan diubah sendiri.
- Font **Plus Jakarta Sans** untuk gaya slide. Bila belum terpasang (`ls ~/Library/Fonts | grep -i jakarta`), **tanya dulu**,
  lalu salin `${CLAUDE_SKILL_DIR}/assets/fonts/*.ttf` ke `~/Library/Fonts/` (lisensi SIL OFL).
- Gambar background (`assets/media/`) disalin otomatis ke folder Media ProPresenter bila belum ada, tanpa menimpa.

Aturan keamanan: **jangan** menulis database ProPresenter (`…/Workspaces/*/DocumentStore/*.sqlite3`). API ProPresenter tidak
bisa menghapus atau mengganti nama presentation/playlist, jadi penghapusan selalu dilakukan pengguna. Item yang namanya
mengandung "(hapus)" diabaikan generator.

## Langkah

1. **Ekstrak teks PDF**: `python3 -I "${CLAUDE_SKILL_DIR}/liturgi2pro.py" pdf "<file.pdf>" > <scratchpad>/liturgi.txt`
   (DOCX: `textutil -convert txt -stdout "<file.docx>"`). Baca seluruhnya. Perhatikan lirik yang tercetak dua kolom.
2. **Lihat Library** (read-only): `curl -s localhost:<port>/v1/libraries` lalu `/v1/library/<uuid>`. Port tampil di
   ProPresenter → Settings → Network. Lagu baku (`KEE n – Judul`) yang sudah ada tidak perlu `.txt`. Kartu/teks tetap punya
   `.txt` bawaan di `${CLAUDE_SKILL_DIR}/tetap/` dan dibuat otomatis bila belum ada di Library.
3. **Buat folder** `Liturgi/<YYYY-MM-DD> Minggu <Tema>/` di folder kerja pengguna. Isinya `Playlist.txt` dan `.txt` untuk item
   yang belum ada (nama file = nama item; `:` ditulis `∶`). Contoh lengkap: `${CLAUDE_SKILL_DIR}/contoh/2026-10-18 Minggu Moria/`.
   Lagu: tulis semua ayat yang tercetak dalam urutan dinyanyikan; baris playlist `KEE 308 : 1,2`.
   `Countdown` / `Announcement` hanya dimasukkan bila memang ada di Library pengguna.
4. **Uji**: `python3 -I "${CLAUDE_SKILL_DIR}/liturgi2pro.py" playlist "<folder>/Playlist.txt" --coba`
   → ♻ dipakai ulang · ✚ akan dibuat · ⚠ tidak ada · ✎ nama menyimpang. Perbaiki ✎ sebelum lanjut.
5. **Jalankan** tanpa `--coba`. Item ⚠ menjadi header merah "⚠ BELUM ADA: …".
   Lagu baku yang sudah ada tetapi tidak punya ayat/arrangement yang diminta: ⚠ di laporan. Operator menambah ayat lewat
   Reflow dan membuat arrangement di ProPresenter (API tidak bisa mengubah item).
6. **Verifikasi** via `GET /v1/playlist/<uuid>` (urutan, arrangement lagu).
7. **Laporkan**: tabel susunan liturgi, item ♻/✚/⚠, lirik yang disusun ulang atau diragukan, teks yang tidak ada di PDF.
   Panduan operator untuk pengguna: [PANDUAN_OPERATOR.md](PANDUAN_OPERATOR.md).

## Teknis

- `template.pro` = gaya slide (kartu judul Thumbnail, isi + Background 1, Plus Jakarta Sans, label kiri atas). Path media di
  dalamnya otomatis disesuaikan ke folder ProPresenter pengguna.
- Arrangement ditulis tanpa `selected_arrangement`. Kalau di-set, ProPresenter menambah "- [ 1,2 ]" ke nama saat impor.
- Nama item di Library mengikuti nama file `.pro`: `:` muncul sebagai `∶`. Pencocokan mengabaikan tanda baca.
- API: header butuh `id.uuid` string; item presentation `id.uuid` = UUID presentation; `presentation_info` hanya bila
  ada arrangement, dan wajib `arrangement_name` + `arrangement_uuid`.
- Uji generator: `python3 -I "${CLAUDE_SKILL_DIR}/liturgi2pro.py" --selftest`.
