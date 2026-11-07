#!/usr/bin/env python3
"""Liturgi -> ProPresenter dengan konsep Library + Playlist.

* 1 lagu = 1 presentation (grup "Ayat 1", "Reff", ... + arrangement sesuai ayat yang dinyanyikan)
* 1 bacaan/bagian liturgi = 1 presentation
* Item yang SUDAH ADA di Library dipakai ulang; hanya yang belum ada dibuat dari .txt lalu diimpor.
* Playlist mingguan dibuat lewat ProPresenter Network API (Settings -> Network -> Enable Network).

Rencana playlist (Playlist.txt), satu baris per entri:
    # Minggu 08 November 2026 – Kesehaten     <- nama playlist (baris pertama)
    ## 3. Votum – Salam                        <- header playlist
    Votum – Salam                               <- item: nama presentation di Library
    KEE 308 : 1,2                               <- lagu: nomor KEE + ayat yang dinyanyikan
Item yang tidak ada di Library dibuat dari "<nama>.txt" (lagu: "KEE 308.txt") di folder yang sama.

Format .txt item: blok dipisah 1 baris kosong = 1 slide; penanda [..] berlaku sampai penanda berikutnya.
    [Judul] kartu judul | [Liturgos] | [Perpulungen] | [Bersama] | [2 Raja-raja 4 : 38-41]
    Lagu: [Judul], [Ayat 1], [Reff], [Ayat 2], [Reff] ... (Reff boleh diulang; jadi 1 grup + arrangement)

Pakai:
    python3 liturgi2pro.py pdf LITURGI.pdf              (teks PDF, lewat PDFKit bawaan macOS)
    python3 liturgi2pro.py playlist FOLDER/Playlist.txt [--coba]
    python3 liturgi2pro.py item FILE.txt [--nama "Nama"] [--ayat 1,2] [--buka]
    python3 liturgi2pro.py --selftest
"""
import shutil, urllib.parse, urllib.error, argparse, json, math, re, struct, subprocess, sys, textwrap, time, urllib.request, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP_BUNDLE = "com.renewedvision.propresenter"   # dibuka lewat bundle id: lokasi aplikasi tidak penting
# Folder data pengguna ProPresenter (PP 21/22; fallback PP 7 lama). Template merujuk media relatif ke folder ini.
PP_USER_DIRS = [Path.home() / "Library/Application Support/RenewedVision/ProPresenter/UserWorkspaces/ProPresenter",
                Path.home() / "Documents/ProPresenter"]
TEMPLATE_MEDIA_PREFIX = b"file:///Users/hawkins/Library/Application%20Support/RenewedVision/ProPresenter/UserWorkspaces/ProPresenter/"
WIDTH = 36

# ---------- protobuf wire format ----------
def _varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7F) << s; s += 7
        if c < 0x80: return r, i

def parse(b):
    i, out = 0, []
    while i < len(b):
        k, i = _varint(b, i); f, w = k >> 3, k & 7
        if w == 0: v, i = _varint(b, i)
        elif w == 1: v = b[i:i + 8]; i += 8
        elif w == 5: v = b[i:i + 4]; i += 4
        elif w == 2:
            n, i = _varint(b, i); v = b[i:i + n]; i += n
        else: raise ValueError(f"wire type {w} tidak didukung")
        out.append([f, w, v])
    return out

def _enc_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n: return bytes(out)

def ser(msg):
    out = bytearray()
    for f, w, v in msg:
        out += _enc_varint(f << 3 | w)
        if w == 0: out += _enc_varint(v)
        elif w == 2: out += _enc_varint(len(v)) + v
        else: out += v
    return bytes(out)

def get(msg, f): return [v for ff, _, v in msg if ff == f]
def field(f, v): return [f, 2, v]
def new_uuid(): return str(uuid.uuid4()).upper()
def uuid_msg(u): return ser([field(1, u.encode())])

# ---------- template (gaya slide pengguna) ----------
UUID_RE = re.compile(rb"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}")
TEXT_PATH = [10, 23, 2, 1, 1, 1, 13]  # cue>action>slide>?>base slide>slide element>graphics element>text

def n_text_elements(cue):
    n = 0
    for a in get(parse(cue), 10):
        for s in get(parse(a), 23):
            for bs in get(parse(s), 2):
                for base in get(parse(bs), 1):
                    for el in get(parse(base), 1):
                        n += bool(get(parse(get(parse(el), 1)[0]), 13))
    return n

def pp_user_dir():
    return next((d for d in PP_USER_DIRS if d.exists()), PP_USER_DIRS[0])

def ensure_media():
    """Salin gambar background bawaan ke Media/Assets ProPresenter bila belum ada (tidak menimpa)."""
    dst = pp_user_dir() / "Media/Assets"
    for f in (HERE / "assets/media").glob("*.png"):
        if not (dst / f.name).exists():
            dst.mkdir(parents=True, exist_ok=True); shutil.copy2(f, dst / f.name)

def rewrite_urls(b, old, new):
    """Ganti awalan URL file:// di seluruh pohon protobuf (panjang field ikut disesuaikan)."""
    try: msg = parse(b)
    except (ValueError, IndexError): return b
    if ser(msg) != b: return b
    for item in msg:
        if item[1] != 2: continue
        if item[2].startswith(old): item[2] = new + item[2][len(old):]
        elif item[2]: item[2] = rewrite_urls(item[2], old, new)
    return ser(msg)

_TEMPLATE = None
def load_template(path=HERE / "template.pro"):
    global _TEMPLATE
    if _TEMPLATE: return _TEMPLATE
    ensure_media()
    here = ("file://" + urllib.parse.quote(str(pp_user_dir())) + "/").encode()
    top = parse(rewrite_urls(path.read_bytes(), TEMPLATE_MEDIA_PREFIX, here))
    title = body_bg = body = None
    for c in get(top, 13):
        n_txt, n_act = n_text_elements(c), len(get(parse(c), 10))
        if n_txt == 1 and title is None: title = c
        elif n_txt == 2 and n_act >= 2 and body_bg is None: body_bg = c
        elif n_txt == 2 and n_act == 1 and body is None: body = c
    assert title and body_bg and body, "template.pro harus punya: kartu judul, slide isi + background, slide isi tanpa background"
    _TEMPLATE = (top, title, body_bg, body)
    return _TEMPLATE

def rtf_escape(s):
    out = []
    for ch in s:
        if ch in "\\{}": out.append("\\" + ch)
        elif ch == "\n": out.append("\\\n")
        elif ord(ch) < 128: out.append(ch)
        else:
            try: out.append("\\'%02x" % ch.encode("cp1252")[0])
            except UnicodeEncodeError: out.append("\\u%d?" % (ord(ch) if ord(ch) < 32768 else ord(ch) - 65536))
    return "".join(out)

def set_rtf(rtf, text):
    rtf = rtf.decode()
    i = rtf.rindex("\\CocoaLigature0 ") + len("\\CocoaLigature0 ")
    return (rtf[:i] + rtf_escape(text) + "}").encode()

def rewrite(msg_bytes, path, fn):
    msg = parse(msg_bytes)
    for item in msg:
        if item[0] == path[0]:
            item[2] = fn(item[2]) if len(path) == 1 else rewrite(item[2], path[1:], fn)
    return ser(msg)

def make_cue(tpl, texts):
    """Kloning cue template, ganti semua UUID, isi teks elemen berurutan."""
    cue = UUID_RE.sub(lambda m: new_uuid().encode(), tpl)
    it = iter(texts)
    cue = rewrite(cue, TEXT_PATH, lambda t: rewrite(t, [5], lambda r: set_rtf(r, next(it))))
    return cue, get(parse(get(parse(cue), 1)[0]), 1)[0].decode()

# ---------- teks ----------
def layout(block, width=WIDTH, max_lines=4):
    lines = []
    for ln in block.splitlines():
        ln = " ".join(ln.split())
        if ln: lines += textwrap.wrap(ln, width, break_on_hyphens=False) or [ln]
    if not lines: return []
    per = math.ceil(len(lines) / math.ceil(len(lines) / max_lines))
    return ["\n".join(lines[k:k + per]) for k in range(0, len(lines), per)]

def read_txt(path, width=WIDTH):
    """-> list of (penanda, teks_slide). [Judul] tidak dibungkus."""
    role, out = "Liturgos", []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8").replace("\r\n", "\n")):
        m = re.match(r"\s*\[([^\]]+)\]\s*\n?", block)
        if m: role, block = m.group(1).strip(), block[m.end():]
        if role.lower() == "judul":
            if block.strip(): out.append((role, "\n".join(l.strip() for l in block.strip().splitlines())))
        else:
            out += [(role, s) for s in layout(block, width)]
    return out

COLORS = {"judul": (0.55, 0.55, 0.55), "liturgos": (0.20, 0.50, 1.00), "perpulungen": (0.20, 0.80, 0.35),
          "bersama": (1.00, 0.80, 0.10), "moria": (0.90, 0.30, 0.45), "mamre": (0.20, 0.75, 0.80),
          "ayat": (0.65, 0.35, 0.95), "reff": (0.95, 0.45, 0.75), "alkitab": (1.00, 0.55, 0.10)}
def rgb_for(role):
    r = role.lower()
    key = next((k for k in COLORS if r.startswith(k)), None)
    if key is None and re.search(r"\d+\s*:\s*\d", r): key = "alkitab"
    return COLORS[key or "judul"]
def color_msg(rgb): return ser([[i + 1, 5, struct.pack("<f", x)] for i, x in enumerate(tuple(rgb) + (1.0,))])

SONG_RE = re.compile(r"^KEE\s*(?:No\.?\s*)?(\d+)\b", re.I)
SONG_LINE_RE = re.compile(r"^KEE (\d+)(?: : ([\d,\- ]+))?$")   # baris lagu di Playlist.txt: "KEE 308 : 1,2"
CANON_SONG_RE = re.compile(r"^KEE (\d+) – \S")
DATED_RE = re.compile(r"^\d{4}-\d{2}-\d{2} · \S")
BIBLE_RE = re.compile(r"^(?:[1-3] )?[A-Z][\w-]*(?: [\w-]+)* \d+:\d+(?:-\d+)?$")
FIXED = {"Perpulungen Tedis", "Perpulungen Kundul", "Erkata Lonceng", "Kata Pengalo-ngalo ras Momo",
         "Kata Dibata Sipemena", "Kata Dibata – Haleluya", "Pengakun Kiniteken", "Pertoton Persembahen ras Syafaat",
         "Pertoton Tuhan", "Paksa Teneng", "Saat Teduh", "Countdown", "Announcement"}

def name_ok(line):
    """Tata penamaan item (lihat TATA_PENULISAN.md)."""
    return bool(SONG_LINE_RE.match(line) or line.startswith("Lagu – ") or DATED_RE.match(line) or BIBLE_RE.match(line) or line in FIXED)

VERSE_RE = re.compile(r"^(?:Ayat|Verse|Bait)\s*(\d+)$", re.I)

def song_label(name, role):
    """Label kiri atas slide lagu, meniru gaya pengguna: 'KEE 308 : 1' / 'REFREIN'."""
    m, v = SONG_RE.match(name), VERSE_RE.match(role)
    if m and v: return f"KEE {m.group(1)} : {v.group(1)}"
    if role.lower().startswith(("reff", "chorus")): return "REFREIN"
    return role.upper()

def build(name, slides, order=None, arr_name=None):
    """slides: [(penanda, teks)] -> bytes .pro.
    Lagu (order diberikan): 1 grup per penanda + arrangement `arr_name` mengikuti `order` (Reff bisa berulang).
    Bukan lagu: grup baru setiap penanda berganti, tanpa arrangement."""
    top, t_title, t_bg, t_body = load_template()
    groups, cues, need_bg, prev = [], [], True, None     # groups: [uuid, nama, rgb, [cue ids]]
    by_role = {}
    for role, text in slides:
        judul = role.lower() == "judul"
        if judul: cue, cid = make_cue(t_title, [text]); need_bg = True
        else: cue, cid = make_cue(t_bg if need_bg else t_body, [text, song_label(name, role)]); need_bg = False
        if order is not None and role in by_role: g = by_role[role]
        elif order is None and role == prev: g = groups[-1]
        else:
            g = [new_uuid(), role, rgb_for(role), []]; groups.append(g); by_role[role] = g
        g[3].append(cid); cues.append(cue); prev = role
    new = []
    for f_, w, v in top:
        if f_ == 2: v = uuid_msg(new_uuid())
        elif f_ == 3: v = name.encode()
        elif f_ == 14: v = ser([field(3, name.encode())])
        elif f_ in (10, 11, 12, 13): continue
        new.append([f_, w, v])
        if f_ == 9:  # arrangements(11), cue_groups(12), cues(13)
            if order is not None:
                arr = new_uuid()  # sengaja tanpa selected_arrangement (field 10): PP22 menambah "- [ arr ]" ke nama saat impor
                new.append(field(11, ser([field(1, uuid_msg(arr)), field(2, (arr_name or "Semua").encode())]
                                         + [field(3, uuid_msg(by_role[r][0])) for r in order])))
            for gid, gname, rgb, ids in groups:
                g = ser([field(1, uuid_msg(gid)), field(2, gname.encode()), field(3, color_msg(rgb))])
                new.append(field(12, ser([field(1, g)] + [field(2, uuid_msg(i)) for i in ids])))
            new += [field(13, c) for c in cues]
    return ser(new)

def build_item(path, name, verses=None):
    slides = read_txt(path)
    if not SONG_RE.match(name): return build(name, slides)
    order, uniq, seen, cur = [], [], set(), None
    for role, text in slides:          # blok lagu yang diulang (Reff ke-2 dst.) hanya masuk arrangement
        if role != cur:
            cur = role; order.append(role); repeat = role in seen and role.lower() != "judul"; seen.add(role)
        if not repeat: uniq.append((role, text))
    return build(name, uniq, order, spec_name(verses))

# ---------- ProPresenter Network API ----------
class PP:
    def __init__(self, port): self.base = f"http://localhost:{port}"
    def req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(self.base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=15) as resp:
                t = resp.read()
                return json.loads(t) if t.strip() else None
        except urllib.error.HTTPError as e:
            sys.exit(f"ProPresenter API {method} {path} -> HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")
    def library(self):
        out = {}
        for lib in self.req("GET", "/v1/libraries"):
            for it in self.req("GET", f"/v1/library/{lib['uuid']}")["items"]:
                if "(hapus)" not in it["name"]: out[it["name"]] = it["uuid"]   # item bertanda "(hapus)" diabaikan
        return out
    def presentation(self, u):
        d = self.req("GET", f"/v1/presentation/{u}"); return d.get("presentation", d)

def norm(s): return re.sub(r"[^0-9a-z]", "", s.lower())

def spec_name(spec):
    """Nama arrangement baku dari pilihan ayat: '1-2'->'1,2', '1,2,3,4'->'1-4', ''->'Semua'."""
    v = sorted(set(verses_of(spec)))
    if not v: return "Semua"
    if len(v) >= 3 and v == list(range(v[0], v[-1] + 1)): return f"{v[0]}-{v[-1]}"
    return ",".join(map(str, v))

def verses_of(spec):
    out = []
    for part in re.split(r"[,\s]+", spec or ""):
        a, _, b = part.partition("-")
        if a.isdigit(): out += list(range(int(a), int(b) + 1)) if b.isdigit() else [int(a)]
    return out

def find_song(pp, lib, num, spec):
    """-> (uuid, nama, arrangement {'uuid','name'}|None, catatan) atau None."""
    need = set(verses_of(spec))
    for name, u in sorted(lib.items()):
        m = CANON_SONG_RE.match(name)   # hanya nama baku "KEE 308 – Judul"
        if not m or m.group(1) != num: continue
        p = pp.presentation(u)
        have = {int(v.group(1)) for g in p.get("groups", []) if (v := VERSE_RE.match(g["name"].strip()))}
        if need and not need <= have: continue
        arr = next((a for a in p.get("arrangements", []) if a["id"]["name"] == spec_name(spec)), None)
        if arr: return u, name, arr["id"], f"arrangement '{arr['id']['name']}'"
        extra = have - need if need else set()
        return u, name, None, (f"⚠ berisi ayat ekstra {sorted(extra)} — pilih arrangement manual" if extra else "")
    return None

def find_txt(folder, name):
    """Cari <nama>.txt di folder minggu itu, lalu di teks baku bawaan (tetap/)."""
    for d in (folder, HERE / "tetap"):
        hit = next((p for p in sorted(d.glob("*.txt")) if norm(p.stem) == norm(name)), None)
        if hit: return hit
    return None

def pdf_text(path):
    """Teks PDF lewat PDFKit (JXA bawaan macOS) — tanpa Xcode/pip."""
    js = ('ObjC.import("PDFKit"); function run(a){var d=$.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(a[0]));'
          'if(!d.isNil()){var o=[];for(var i=0;i<d.pageCount;i++){o.push("=====HALAMAN "+(i+1)+"=====");'
          'o.push(ObjC.unwrap(d.pageAtIndex(i).string)||"")}return o.join("\\n")}return "GAGAL membuka PDF"}')
    return subprocess.run(["osascript", "-l", "JavaScript", "-e", js, str(path)], capture_output=True, text=True, check=True).stdout

def import_pro(pp, folder, name, data, timeout=40):
    """Tulis .pro (nama file aman: ':' -> '∶') lalu buka di ProPresenter; tunggu sampai muncul di Library."""
    path = folder / (name.replace(":", "∶").replace("/", "∕") + ".pro"); path.write_bytes(data)
    subprocess.run(["open", "-b", PP_BUNDLE, str(path)], check=True)
    end = time.time() + timeout
    while time.time() < end:
        time.sleep(2)
        hit = next(((n, u) for n, u in pp.library().items() if norm(n) == norm(name)), None)
        if hit: return hit
    sys.exit(f"'{name}' belum muncul di Library setelah {timeout} dtk — cek apakah ProPresenter menampilkan dialog.")

def detect_port():
    """Port Network API ProPresenter yang sedang LISTEN (port bisa berganti otomatis)."""
    out = subprocess.run("for p in $(pgrep -f ProPresenter.app); do lsof -a -nP -iTCP -sTCP:LISTEN -p $p; done",
                         shell=True, capture_output=True, text=True).stdout
    ports = re.findall(r":(\d+) \(LISTEN\)", out)
    return int(ports[0]) if ports else 50001

def run_playlist(plan, port, overwrite=False, dry=False):
    folder, pp = plan.parent, PP(port or detect_port())
    try: lib = pp.library()
    except OSError as e: sys.exit(f"Tidak bisa menghubungi ProPresenter di port {port} ({e}). Aktifkan: ProPresenter → Settings → Network → Enable Network.")
    lines = [l.rstrip() for l in plan.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert lines[0].startswith("# "), "baris pertama harus '# Nama Playlist'"
    pl_name, items, report = lines[0][2:].strip(), [], []
    out_dir = folder / "_pro"; out_dir.mkdir(exist_ok=True)
    for ln in lines[1:]:
        if ln.startswith("## "):
            items.append({"id": {"uuid": new_uuid(), "name": ln[3:].strip(), "index": len(items)}, "type": "header",
                          "header_color": {"red": 0.0, "green": 0.54, "blue": 0.87, "alpha": 1.0}, "is_hidden": False, "is_pco": False})
            continue
        if ln.startswith("#"): continue
        if not name_ok(ln): report.append(f"✎  {ln:40} → nama tidak sesuai TATA_PENULISAN.md")
        song = SONG_LINE_RE.match(ln)
        arr = None
        if song:
            num, spec = song.group(1), (song.group(2) or "").strip()
            hit = find_song(pp, lib, num, spec)
            if hit:
                u, name, arr, note = hit; report.append(f"♻  {ln:40} → Library: {name} {note}")
            else:
                src = next((f for f in sorted(folder.glob(f"KEE {num} – *.txt"))), None)
                if not src: report.append(f"⚠  {ln:40} → TIDAK ADA di Library & tidak ada 'KEE {num} – <Judul>.txt'"); u = None
                else:
                    name = src.stem
                    data = build_item(src, name, spec or None)
                    if dry: report.append(f"✚  {ln:40} → AKAN DIBUAT: {name}"); continue
                    name, u = import_pro(pp, out_dir, name, data); lib[name] = u
                    p = pp.presentation(u)
                    arr = next((a["id"] for a in p.get("arrangements", []) if a["id"]["name"] != "Master"), None)
                    report.append(f"✚  {ln:40} → BARU: {name} (arrangement {spec_name(spec)})")
        else:
            name = next((n for n in lib if norm(n) == norm(ln)), None)
            if name: u = lib[name]; report.append(f"♻  {ln:40} → Library: {name}")
            else:
                src = find_txt(folder, ln)
                if not src: report.append(f"⚠  {ln:40} → TIDAK ADA di Library & tidak ada '{ln}.txt'"); u = None
                else:
                    data = build_item(src, ln)
                    if dry: report.append(f"✚  {ln:40} → AKAN DIBUAT: {ln}"); continue
                    name, u = import_pro(pp, out_dir, ln, data); lib[name] = u
                    report.append(f"✚  {ln:40} → BARU: {name}")
        if u is None:
            items.append({"id": {"uuid": new_uuid(), "name": f"⚠ BELUM ADA: {ln}", "index": len(items)}, "type": "header",
                          "header_color": {"red": 1.0, "green": 0.2, "blue": 0.2, "alpha": 1.0}, "is_hidden": False, "is_pco": False})
            continue
        # API PP22: id.uuid = UUID presentasi; presentation_info hanya bila ada arrangement (wajib nama + uuid)
        it = {"id": {"uuid": u, "name": name, "index": len(items)}, "type": "presentation", "is_hidden": False, "is_pco": False}
        if arr: it["presentation_info"] = {"presentation_uuid": u, "arrangement_name": arr["name"], "arrangement_uuid": arr["uuid"]}
        items.append(it)
    if dry: print("\n".join(report)); return
    existing = [p for p in pp.req("GET", "/v1/playlists") if p["id"]["name"] == pl_name]
    if existing and not overwrite: sys.exit(f"Playlist '{pl_name}' sudah ada — ganti nama di Playlist.txt atau pakai --timpa.")
    pid = existing[0]["id"]["uuid"] if existing else pp.req("POST", "/v1/playlists", {"name": pl_name, "type": "playlist"})["id"]["uuid"]
    pp.req("PUT", f"/v1/playlist/{pid}", items)
    got = pp.req("GET", f"/v1/playlist/{pid}")
    print("\n".join(report))
    print(f"\nPlaylist '{pl_name}': {len(got.get('items', got)) if isinstance(got, dict) else len(got)} entri (dikirim {len(items)}).")

def selftest():
    assert parse(ser([[1, 0, 300], [2, 2, b"ab"], [3, 5, b"\0\0\x80?"]])) == [[1, 0, 300], [2, 2, b"ab"], [3, 5, b"\0\0\x80?"]]
    assert rtf_escape("k’rina {x}\nb") == "k\\'92rina \\{x\\}\\\nb"
    assert layout("satu dua tiga empat lima", 9) == ["satu dua\ntiga\nempat\nlima"]
    assert len(layout("\n".join("abc" for _ in range(5)), 40)) == 2
    assert spec_name("1-2") == "1,2" and spec_name("1,2,3,4") == "1-4" and spec_name("") == "Semua"
    assert name_ok("KEE 308 : 1,2") and name_ok("2026-11-08 · 03 Votum – Salam") and name_ok("Titus 2:3-5")
    assert name_ok("Lagu – Lebih dari Pemenang")
    assert name_ok("2 Raja-raja 4:38-41") and name_ok("Perpulungen Tedis") and not name_ok("KEE 336  1,2") and not name_ok("Votum – Salam")
    assert verses_of("1,3") == [1, 3] and verses_of("1-3") == [1, 2, 3] and verses_of("") == []
    assert song_label("KEE 308 – X", "Ayat 2") == "KEE 308 : 2" and song_label("KEE 308", "Reff") == "REFREIN"
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "KEE 1.txt"
        p.write_text("[Judul]\nKEE 1\n“Uji”\n\n[Ayat 1]\na\n\n[Reff]\nr\n\n[Ayat 2]\nb\n\n[Reff]\nr\n", encoding="utf-8")
        top = parse(build_item(p, "KEE 1 – Uji", "1,2"))
        assert len(get(top, 13)) == 4 and len(get(top, 12)) == 4            # judul, ayat1, reff, ayat2 (Reff sekali)
        arr = parse(get(top, 11)[0]); assert get(arr, 2) == [b"1,2"] and len(get(arr, 3)) == 5   # Judul Ayat1 Reff Ayat2 Reff
        p2 = Path(d) / "Votum.txt"; p2.write_text("[Judul]\nVotum\n\n[Liturgos]\nx\n\n[Perpulungen]\nAmin\n", encoding="utf-8")
        top = parse(build_item(p2, "Votum")); assert len(get(top, 13)) == 3 and not get(top, 11)
    raw = (HERE / "template.pro").read_bytes()
    moved = rewrite_urls(raw, TEMPLATE_MEDIA_PREFIX, b"file:///Users/teman/PP/")
    assert TEMPLATE_MEDIA_PREFIX in raw and TEMPLATE_MEDIA_PREFIX not in moved and b"file:///Users/teman/PP/Media/Assets/Background%201.png" in moved
    assert len(get(parse(moved), 13)) == len(get(parse(raw), 13))
    print("selftest OK")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("perintah", nargs="?", choices=["playlist", "item", "pdf"])
    ap.add_argument("file", nargs="?", type=Path)
    ap.add_argument("--port", type=int, help="default: dideteksi otomatis")
    ap.add_argument("--coba", action="store_true", help="playlist: hanya tampilkan rencana, tanpa impor/menulis")
    ap.add_argument("--nama"); ap.add_argument("--ayat")
    ap.add_argument("--buka", action="store_true", help="item: impor ke ProPresenter")
    ap.add_argument("--timpa", action="store_true", help="playlist: timpa isi playlist bernama sama")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    if not (a.perintah and a.file): ap.error("butuh perintah dan file")
    if a.perintah == "pdf": print(pdf_text(a.file))
    elif a.perintah == "playlist": run_playlist(a.file, a.port, a.timpa, a.coba)
    else:
        name = a.nama or a.file.stem
        out = a.file.with_suffix(".pro"); out.write_bytes(build_item(a.file, name, a.ayat))
        print(f"OK: {out}")
        if a.buka: subprocess.run(["open", "-b", PP_BUNDLE, str(out)], check=True)
