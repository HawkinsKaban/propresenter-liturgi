# propresenter-liturgi

Plugin **Claude Code** untuk operator multimedia gereja (GBKP). Berikan PDF liturgi Minggu, lalu Claude:

1. membaca liturgi dan menyusun teksnya sesuai tata penulisan baku,
2. memakai ulang item yang sudah ada di Library ProPresenter, seperti lagu KEE, bacaan, dan kartu tetap,
3. membuat hanya item yang belum ada: 1 lagu = 1 presentation dengan arrangement ayat, 1 bacaan = 1 presentation,
4. membuat **playlist minggu itu** di ProPresenter, lengkap dengan header per bagian liturgi.

Tidak perlu impor `.txt` manual.

## Syarat

- **macOS** dengan `python3` (tanpa pip/install lain).
- **ProPresenter** 7.9 ke atas / 21 / 22, terbuka, dengan **Settings → Network → Enable Network** menyala.
- **Claude Code** (aplikasi desktop tab *Code*, atau CLI `claude`) di komputer yang sama dengan ProPresenter.
- Font **Plus Jakarta Sans**. File-nya ikut di plugin, dan Claude akan menawarkan pemasangannya.

## Pasang

Di Terminal:

```bash
claude plugin marketplace add HawkinsKaban/propresenter-liturgi
```

```bash
claude plugin install propresenter-liturgi@propresenter-liturgi
```

Atau di dalam sesi Claude Code: `/plugin marketplace add HawkinsKaban/propresenter-liturgi`, lalu
`/plugin install propresenter-liturgi@propresenter-liturgi`.

Jika repo ini **private**, pemasang harus punya akses baca ke repo dan login GitHub di komputernya
(`gh auth login` lalu `gh auth setup-git`).

## Pakai

Buka Claude Code di folder tempat arsip liturgi akan disimpan. Ketik `/propresenter-liturgi:propresenter-liturgi`
atau cukup tulis *"buatkan playlist ProPresenter dari liturgi ini"*, lalu lampirkan PDF-nya. Claude menampilkan
rencana (♻ dipakai ulang / ✚ dibuat / ⚠ tidak ada di PDF) sebelum membuat playlist.

Panduan operator: [`PANDUAN_OPERATOR.md`](plugins/propresenter-liturgi/skills/propresenter-liturgi/PANDUAN_OPERATOR.md) ·
Tata penulisan: [`TATA_PENULISAN.md`](plugins/propresenter-liturgi/skills/propresenter-liturgi/TATA_PENULISAN.md) ·
Contoh: [`contoh/2026-10-18 Minggu Moria`](plugins/propresenter-liturgi/skills/propresenter-liturgi/contoh/).

## Perbarui

```bash
claude plugin marketplace update propresenter-liturgi
```

```bash
claude plugin update propresenter-liturgi@propresenter-liturgi
```

Lalu jalankan `/reload-plugins` atau buka ulang Claude Code.

## Catatan

- Plugin tidak pernah menulis database ProPresenter. Item baru diimpor lewat cara resmi (membuka file `.pro`), dan playlist
  dibuat lewat Network API ProPresenter.
- API ProPresenter tidak bisa menghapus atau mengganti nama item, jadi penghapusan dilakukan manual di ProPresenter.
- Gambar background bawaan (`assets/media`) disalin ke folder Media ProPresenter bila belum ada. File yang sudah ada tidak ditimpa.
