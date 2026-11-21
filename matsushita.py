#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Công cụ tìm, tải video tư liệu về 松下幸之助 (Matsushita Konosuke)
và cắt clip dọc 9:16 để dựng video TikTok.

Cách dùng nhanh (chi tiết xem HUONG_DAN.md):
    python matsushita.py                        # hiện menu, chọn bằng số
    python matsushita.py check                  # kiểm tra đã cài đủ công cụ chưa
    python matsushita.py download               # tải từ urls.txt + tìm theo từ khóa
    python matsushita.py download --list-only   # chỉ tìm và ghi list.csv, KHÔNG tải
    python matsushita.py cut                    # cắt clip theo cuts.csv (giữ màu)
    python matsushita.py cut --bw               # cắt clip và chuyển đen trắng
"""

import argparse
import csv
import importlib.util
import io
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

# ----------------------------------------------------------------------------
# CẤU HÌNH — có thể sửa trực tiếp ở đây
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent          # thư mục chứa script này
DOWNLOAD_DIR = BASE_DIR / "downloads" / "matsushita"
CLIPS_DIR = BASE_DIR / "clips"
URLS_FILE = BASE_DIR / "urls.txt"
KEYWORDS_FILE = BASE_DIR / "keywords.txt"
CUTS_FILE = BASE_DIR / "cuts.csv"
LIST_FILE = BASE_DIR / "list.csv"
ERRORS_FILE = BASE_DIR / "errors.txt"

# Dùng khi không có keywords.txt
DEFAULT_KEYWORDS = [
    "松下幸之助 肉声",
    "松下幸之助 講演 映像",
    "松下幸之助 記録映像",
    "松下電器 昭和 工場",
]
SEARCH_LIMIT = 10          # số kết quả tối đa cho mỗi từ khóa
MAX_MINUTES = 60           # bỏ qua video dài hơn số phút này
MAX_HEIGHT = 1080          # chất lượng tối đa (1080p)

LIST_COLUMNS = ["tiêu đề", "kênh", "link", "thời lượng", "tên file"]
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}

# ----------------------------------------------------------------------------
# HƯỚNG DẪN CÀI ĐẶT (in ra khi thiếu công cụ)
# ----------------------------------------------------------------------------
PIP_CMD = f'"{sys.executable}" -m pip install -U "yt-dlp[default]"'

HELP_YTDLP = f"""
  [THIẾU] Chưa cài yt-dlp. Mở cửa sổ lệnh và gõ:
      {PIP_CMD}
"""

HELP_FFMPEG = """
  [THIẾU] Chưa cài ffmpeg. Cách cài:
      Windows : winget install Gyan.FFmpeg
                (cài xong phải ĐÓNG và MỞ LẠI cửa sổ lệnh)
      macOS   : brew install ffmpeg      (cần Homebrew, xem https://brew.sh)
      Ubuntu  : sudo apt install ffmpeg
"""

HELP_JS = """
  [KHUYẾN NGHỊ] Chưa có Deno. YouTube hiện cần một trình chạy JavaScript
  thì yt-dlp mới tải ổn định (thiếu có thể bị lỗi hoặc thiếu chất lượng cao):
      Windows : winget install DenoLand.Deno
      macOS   : brew install deno
      Linux   : curl -fsSL https://deno.land/install.sh | sh
  (Nếu máy đã có Node.js hoặc Bun thì script sẽ tự dùng.)
"""


# ----------------------------------------------------------------------------
# TIỆN ÍCH CHUNG
# ----------------------------------------------------------------------------
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def clean_message(msg):
    """Làm gọn thông báo lỗi để ghi vào errors.txt."""
    text = ANSI_RE.sub("", str(msg))
    text = re.sub(r"^\s*ERROR:\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:600]


def log_error(stage, target, msg):
    """Ghi 1 dòng vào errors.txt và in ra màn hình. Không bao giờ dừng chương trình."""
    msg = clean_message(msg)
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{stage}] {target} | {msg}\n"
    try:
        with open(ERRORS_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        print(f"  (Không ghi được errors.txt: {e})")
    print(f"  ✗ LỖI: {msg}")


def read_text(path):
    """Đọc file chữ, tự nhận UTF-8 / UTF-16 / Shift-JIS (Excel tiếng Nhật)."""
    raw = Path(path).read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    for enc in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(
        f"Không đọc được {Path(path).name}. Hãy lưu lại file dạng 'CSV UTF-8' / 'UTF-8'.")


def resolve_user_path(p):
    """Đường dẫn người dùng gõ: thử theo thư mục hiện tại, rồi theo thư mục script."""
    p = Path(p)
    if p.is_absolute() or p.exists():
        return p
    return BASE_DIR / p


def nfc(s):
    return unicodedata.normalize("NFC", s)


def format_duration(seconds):
    """3725 -> '1:02:05'  (luôn có giờ để Excel không hiểu nhầm)."""
    if seconds is None:
        return ""
    s = int(round(float(seconds)))
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def safe_name(text, max_len=60):
    """Bỏ ký tự không hợp lệ trong tên file (Windows/macOS)."""
    text = nfc(str(text))
    text = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", text)
    text = re.sub(r"\s+", "_", text).strip("._ ")
    return text[:max_len]


def find_js_runtimes():
    found = {name: {} for name in ("deno", "node", "bun") if shutil.which(name)}
    return found


# ----------------------------------------------------------------------------
# KIỂM TRA CÔNG CỤ
# ----------------------------------------------------------------------------
def check_tools(need_ytdlp=True, need_ffmpeg=True, verbose=False):
    """Trả về True nếu đủ công cụ bắt buộc. In hướng dẫn cài nếu thiếu."""
    ok = True

    if sys.version_info < (3, 10):
        print(f"  [THIẾU] Cần Python 3.10 trở lên (đang dùng {sys.version.split()[0]}).")
        print("          Tải bản mới tại https://www.python.org/downloads/")
        ok = False
    elif verbose:
        print(f"  [OK] Python {sys.version.split()[0]}")

    if need_ytdlp:
        try:
            import yt_dlp  # noqa: F401
            from yt_dlp.version import __version__ as ytv
            if verbose:
                print(f"  [OK] yt-dlp {ytv}")
            try:
                age = (date.today() - datetime.strptime(ytv[:10], "%Y.%m.%d").date()).days
                if age > 60:
                    print(f"  [CẢNH BÁO] yt-dlp đã cũ ({age} ngày). YouTube hay thay đổi, nên cập nhật:")
                    print(f"      {PIP_CMD}")
            except ValueError:
                pass
            if verbose and importlib.util.find_spec("yt_dlp_ejs") is None:
                print("  [GỢI Ý] Thiếu gói yt-dlp-ejs (script sẽ tự tải khi cần). Cài cho chắc:")
                print(f"      {PIP_CMD}")
        except ImportError:
            print(HELP_YTDLP)
            ok = False

        runtimes = find_js_runtimes()
        if runtimes:
            if verbose:
                print(f"  [OK] Trình chạy JavaScript: {', '.join(runtimes)}")
        else:
            print(HELP_JS)

    if need_ffmpeg:
        missing = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
        if missing:
            print(HELP_FFMPEG)
            ok = False
        elif verbose:
            print("  [OK] ffmpeg + ffprobe")

    return ok


# ----------------------------------------------------------------------------
# list.csv
# ----------------------------------------------------------------------------
class VideoList:
    """Danh sách video trong list.csv. Chạy nhiều lần sẽ cộng dồn, không bị trùng."""

    def __init__(self, path):
        self.path = path
        self.rows = {}           # link -> dict
        self._warned = False
        if path.exists():
            try:
                text = read_text(path)
                for row in csv.DictReader(io.StringIO(text)):
                    link = (row.get("link") or "").strip()
                    if link:
                        self.rows[link] = {c: (row.get(c) or "") for c in LIST_COLUMNS}
            except Exception as e:  # file hỏng -> bắt đầu danh sách mới
                print(f"  (Không đọc được list.csv cũ: {e}. Sẽ tạo danh sách mới.)")

    def add(self, title, channel, link, duration, filename):
        old = self.rows.get(link, {})
        self.rows[link] = {
            "tiêu đề": title or old.get("tiêu đề", ""),
            "kênh": channel or old.get("kênh", ""),
            "link": link,
            "thời lượng": format_duration(duration) or old.get("thời lượng", ""),
            # chế độ --list-only không xóa tên file của video đã tải trước đó
            "tên file": filename or old.get("tên file", ""),
        }
        self.save()

    def save(self, path=None):
        path = path or self.path
        try:
            # utf-8-sig để Excel hiển thị đúng chữ Nhật/Việt
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=LIST_COLUMNS)
                w.writeheader()
                w.writerows(self.rows.values())
            return True
        except PermissionError:
            if not self._warned:
                print(f"  (!) Không ghi được {path.name} — có thể file đang mở trong Excel. "
                      "Hãy đóng Excel, script sẽ thử ghi lại.")
                self._warned = True
            return False

    def final_save(self):
        if self.save():
            return self.path
        backup = self.path.with_name(f"list_{datetime.now():%Y%m%d_%H%M%S}.csv")
        return backup if self.save(backup) else None


# ----------------------------------------------------------------------------
# TẢI VIDEO
# ----------------------------------------------------------------------------
YT_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/|live/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})")
YT_LIST_RE = re.compile(r"youtube\.com/(?:playlist\?|@|channel/|c/|user/)")


def youtube_id(url):
    m = YT_ID_RE.search(url)
    return m.group(1) if m else None


def read_urls(path):
    """Đọc urls.txt: mỗi dòng 1 link. Dòng trống hoặc bắt đầu bằng # bị bỏ qua."""
    urls = []
    for line in read_text(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        token = next((t for t in line.split() if t.startswith("http")), None)
        if token:
            urls.append(token)
        elif re.fullmatch(r"[A-Za-z0-9_-]{11}", line):     # chỉ gõ ID video
            urls.append(f"https://www.youtube.com/watch?v={line}")
        else:
            log_error("ĐỌC", f"urls.txt: {line}", "Dòng này không phải link hợp lệ")
    return urls


def read_keywords(args):
    if args.keyword:
        return args.keyword
    path = resolve_user_path(args.keywords)
    if path.exists():
        kws = [k.strip() for k in read_text(path).splitlines()
               if k.strip() and not k.strip().startswith("#")]
        if kws:
            return kws
    return DEFAULT_KEYWORDS


def skip_reason(info, max_seconds):
    """Lý do bỏ qua video (None = được tải)."""
    if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming"):
        return "đang phát trực tiếp hoặc chưa công chiếu"
    duration = info.get("duration")
    if duration and duration > max_seconds:
        return f"dài {format_duration(duration)} (> {max_seconds / 60:g} phút)"
    return None


def canonical_link(info, fallback):
    vid = info.get("id")
    if vid and (info.get("extractor_key") or info.get("ie_key")) == "Youtube":
        return f"https://www.youtube.com/watch?v={vid}"
    return info.get("webpage_url") or info.get("original_url") or fallback


class Downloader:
    def __init__(self, args, video_list):
        import yt_dlp
        self.list = video_list
        self.list_only = args.list_only
        self.max_seconds = args.max_minutes * 60
        self.limit = args.limit
        self._skip = None

        common = {
            "noplaylist": True,
            "extract_flat": "in_playlist",   # không bao giờ tải cả playlist/kênh
            "socket_timeout": 30,
            "retries": 5,
            "extractor_retries": 3,
            "js_runtimes": find_js_runtimes() or {"deno": {}},
        }
        if importlib.util.find_spec("yt_dlp_ejs") is None:
            common["remote_components"] = ["ejs:github"]
        if args.cookies_from_browser:
            common["cookiesfrombrowser"] = (args.cookies_from_browser, None, None, None)
        if args.cookies:
            common["cookiefile"] = str(resolve_user_path(args.cookies))

        self.search_ydl = yt_dlp.YoutubeDL({**common, "quiet": True, "skip_download": True})
        self.ydl = yt_dlp.YoutubeDL({
            **common,
            # Ưu tiên: độ phân giải cao nhất nhưng ≤1080p, rồi codec H.264, rồi mp4/m4a
            # (H.264 dễ dựng nhất trên CapCut / Premiere)
            "format": "bv*+ba/b",
            "format_sort": [f"res:{MAX_HEIGHT}", "vcodec:h264", "ext:mp4:m4a"],
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}],
            "paths": {"home": str(DOWNLOAD_DIR)},
            # [id]_[tiêu đề].mp4 — tiêu đề cắt ở 150 byte để tên file không quá dài
            "outtmpl": {"default": "%(id)s_%(title).150B.%(ext)s"},
            "windowsfilenames": True,
            "playlist_items": "1",
            "match_filter": self._match_filter,
            "fragment_retries": 5,
            "sleep_interval": 2,          # nghỉ vài giây giữa các video để tránh bị YouTube chặn
            "max_sleep_interval": 5,
            "quiet": False,
            "noprogress": False,
        })

    def _match_filter(self, info, *, incomplete=False):
        if info.get("playlist_index") is not None:      # video nằm trong playlist -> không tải
            self._skip = "là playlist/kênh"
            return self._skip
        reason = skip_reason(info, self.max_seconds)
        if reason and not incomplete:
            self._skip = reason
        return reason

    def search(self, keyword):
        res = self.search_ydl.extract_info(f"ytsearch{self.limit}:{keyword}", download=False)
        return [e for e in (res or {}).get("entries") or [] if e]

    def process(self, url, flat=None):
        """Tải 1 video. Trả về ('ok'|'listed'|'skip', mô tả)."""
        if YT_LIST_RE.search(url) and not youtube_id(url):
            return "skip", "là playlist/kênh"

        # --list-only với kết quả tìm kiếm: dùng luôn thông tin có sẵn, không cần hỏi lại YouTube
        if self.list_only and flat:
            info = flat
        else:
            self._skip = None
            before = set(DOWNLOAD_DIR.iterdir())
            info = self.ydl.extract_info(url, download=not self.list_only)
            if info is None:
                raise RuntimeError("Không lấy được thông tin video")

        if info.get("_type") in ("playlist", "multi_video"):
            return "skip", "là playlist/kênh"
        reason = self._skip or skip_reason(info, self.max_seconds)
        if reason:
            return "skip", reason

        title = info.get("title") or ""
        channel = info.get("channel") or info.get("uploader") or ""
        link = canonical_link(info, url)

        if self.list_only:
            self.list.add(title, channel, link, info.get("duration"), "")
            return "listed", title

        filepath = None
        for d in info.get("requested_downloads") or []:
            if d.get("filepath"):
                filepath = Path(d["filepath"])
        if not filepath or not filepath.exists():
            raise RuntimeError("Đã tải nhưng không tìm thấy file mp4 (có thể ffmpeg ghép file bị lỗi)")
        self.list.add(title, channel, link, info.get("duration"), filepath.name)
        if filepath in before:
            return "ok", f"{filepath.name}  (đã có sẵn, không tải lại)"
        return "ok", filepath.name


def cmd_download(args):
    print("\n=== KIỂM TRA CÔNG CỤ ===")
    if not check_tools(need_ytdlp=True, need_ffmpeg=not args.list_only):
        print("Hãy cài các công cụ còn thiếu ở trên rồi chạy lại.")
        return 1

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    video_list = VideoList(LIST_FILE)
    dl = Downloader(args, video_list)
    stats = {"ok": 0, "listed": 0, "skip": 0, "error": 0}
    seen = set()
    counter = [0]

    def run_one(url, flat=None, label=None):
        key = (flat or {}).get("id") or youtube_id(url) or url
        if key in seen:
            return
        seen.add(key)
        counter[0] += 1
        print(f"\n[{counter[0]}] {label or url}")
        if flat and not args.list_only:
            reason = skip_reason(flat, dl.max_seconds)   # bỏ qua sớm, đỡ tốn thời gian
            if reason:
                print(f"  ↷ Bỏ qua: {reason}")
                stats["skip"] += 1
                return
        try:
            status, detail = dl.process(url, flat)
        except Exception as e:     # lỗi 1 video -> ghi lại rồi làm tiếp
            log_error("TẢI", url, e)
            stats["error"] += 1
            return
        stats[status] += 1
        icon = {"ok": "✓ Đã lưu", "listed": "✓ Đã ghi vào list.csv", "skip": "↷ Bỏ qua"}[status]
        print(f"  {icon}: {detail}")

    # 1) Danh sách link trong urls.txt
    if not args.no_urls:
        urls_path = resolve_user_path(args.urls)
        if urls_path.exists():
            urls = read_urls(urls_path)
            print(f"\n=== {urls_path.name}: {len(urls)} link ===")
            for url in urls:
                run_one(url)
        else:
            print(f"\n(Không thấy {urls_path.name} — bỏ qua phần tải theo link.)")

    # 2) Tìm theo từ khóa
    if not args.no_search:
        for kw in read_keywords(args):
            print(f"\n=== Tìm trên YouTube: {kw}  (tối đa {args.limit} kết quả) ===")
            try:
                entries = dl.search(kw)
            except Exception as e:
                log_error("TÌM", kw, e)
                stats["error"] += 1
                continue
            print(f"  Tìm thấy {len(entries)} video")
            for e in entries:
                url = e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}"
                run_one(url, flat=e, label=f"{e.get('title') or url}  ({format_duration(e.get('duration'))})")

    saved = video_list.final_save()
    print("\n" + "=" * 60)
    if args.list_only:
        print(f"XONG. Đã liệt kê: {stats['listed']} | Bỏ qua: {stats['skip']} | Lỗi: {stats['error']}")
    else:
        print(f"XONG. Đã tải: {stats['ok']} | Bỏ qua: {stats['skip']} | Lỗi: {stats['error']}")
        print(f"Video nằm trong: {DOWNLOAD_DIR}")
    if saved:
        print(f"Danh sách: {saved}")
    if stats["error"]:
        print(f"Chi tiết lỗi: {ERRORS_FILE}")
    return 0


# ----------------------------------------------------------------------------
# CẮT CLIP
# ----------------------------------------------------------------------------
def norm_header(h):
    h = nfc((h or "").strip().lower()).replace("đ", "d")
    h = "".join(c for c in unicodedata.normalize("NFD", h) if not unicodedata.combining(c))
    return re.sub(r"[\s_\-]+", " ", h).strip()


CUT_COLUMNS = {
    "file": {"ten file", "file", "filename", "file name", "video", "id"},
    "start": {"bat dau", "start", "tu", "from"},
    "end": {"ket thuc", "end", "den", "to"},
    "label": {"nhan", "label", "ten clip", "ghi chu"},
}


def parse_time(text):
    """'1:23' -> 83 ; '00:01:23.5' -> 83.5 ; '83' -> 83 ; '1:02:03' -> 3723."""
    t = (text or "").strip().replace(",", ".")
    if not t:
        raise ValueError("ô thời gian bị trống")
    parts = t.split(":")
    if len(parts) > 3 or not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        raise ValueError(f"thời gian '{text}' không đúng dạng (ví dụ đúng: 00:01:23)")
    total = 0.0
    for p in parts:
        total = total * 60 + float(p)
    return total


def read_cuts(path):
    """Trả về list (số_dòng, {file,start,end,label})."""
    text = read_text(path)
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    # Excel tiếng Việt thường lưu CSV bằng dấu ; thay vì dấu ,
    delim = max([",", ";", "\t"], key=first.count)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))

    header_idx = next((i for i, r in enumerate(rows) if any(c.strip() for c in r)), None)
    if header_idx is None:
        return []
    header = [norm_header(c) for c in rows[header_idx]]
    colmap = {}
    for key, names in CUT_COLUMNS.items():
        for i, h in enumerate(header):
            if h in names:
                colmap[key] = i
                break

    data_start = header_idx + 1
    if not {"file", "start", "end"} <= colmap.keys():
        # Không có dòng tiêu đề -> hiểu theo thứ tự cột: tên file, bắt đầu, kết thúc, nhãn
        try:
            parse_time(rows[header_idx][1])
            colmap, data_start = {"file": 0, "start": 1, "end": 2, "label": 3}, header_idx
        except (ValueError, IndexError):
            raise ValueError("cuts.csv cần các cột: tên file, bắt đầu, kết thúc, nhãn")

    result = []
    for i in range(data_start, len(rows)):
        r = rows[i]
        if not any(c.strip() for c in r) or r[0].strip().startswith("#"):
            continue

        def cell(k):
            j = colmap.get(k)
            return r[j].strip() if j is not None and j < len(r) else ""

        result.append((i + 1, {k: cell(k) for k in CUT_COLUMNS}))
    return result


def find_source(name):
    """Tìm file video theo tên trong cuts.csv. Chấp nhận: tên file đầy đủ, thiếu .mp4, hoặc chỉ ID."""
    name = name.strip().strip('"')
    if not name:
        return None
    for c in (resolve_user_path(name), DOWNLOAD_DIR / name, DOWNLOAD_DIR / f"{name}.mp4"):
        if c.is_file():
            return c
    if not DOWNLOAD_DIR.is_dir():
        return None
    target = nfc(Path(name).name).lower()
    files = [f for f in DOWNLOAD_DIR.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTS]
    for f in files:   # so khớp không phân biệt hoa/thường & kiểu mã hóa Unicode (macOS)
        if target in (nfc(f.name).lower(), nfc(f.stem).lower()):
            return f
    by_id = [f for f in files if nfc(f.name).startswith(nfc(name) + "_")]
    return by_id[0] if len(by_id) == 1 else None


def probe_duration(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=60)
        return float(out.stdout.strip().splitlines()[0])
    except Exception:
        return None


def build_video_filter(bw=False, upscale=False):
    vf = [
        # đưa pixel về hình vuông (một số tư liệu cũ có pixel méo)
        "scale=trunc(iw*sar/2)*2:ih", "setsar=1",
        # cắt khung 9:16 ở chính giữa (mặc định crop lấy giữa khung hình)
        "crop='trunc(min(iw,ih*9/16)/2)*2':'trunc(min(ih,iw*16/9)/2)*2'",
    ]
    if upscale:
        vf += ["scale=1080:1920:flags=lanczos", "setsar=1"]
    if bw:
        vf.append("hue=s=0")      # bỏ màu -> đen trắng
    return ",".join(vf)


def cmd_cut(args):
    print("\n=== KIỂM TRA CÔNG CỤ ===")
    if not check_tools(need_ytdlp=False, need_ffmpeg=True):
        print("Hãy cài ffmpeg rồi chạy lại.")
        return 1

    cuts_path = resolve_user_path(args.cuts)
    if not cuts_path.exists():
        print(f"Không thấy file {cuts_path}. Hãy tạo cuts.csv (xem HUONG_DAN.md).")
        return 1
    try:
        cuts = read_cuts(cuts_path)
    except Exception as e:
        log_error("CẮT", cuts_path.name, e)
        return 1
    if not cuts:
        print("cuts.csv chưa có dòng nào để cắt (dòng bắt đầu bằng # bị bỏ qua).")
        return 0

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    vf = build_video_filter(bw=args.bw, upscale=args.upscale)
    mode = "ĐEN TRẮNG" if args.bw else "màu"
    print(f"\n=== Cắt {len(cuts)} clip 9:16 ({mode}) -> {CLIPS_DIR} ===")
    ok = err = 0
    durations = {}

    for n, (line_no, c) in enumerate(cuts, 1):
        target = f"cuts.csv dòng {line_no} ({c['file'] or 'trống'})"
        print(f"\n[{n}/{len(cuts)}] dòng {line_no}: {c['file']}  {c['start']} → {c['end']}")
        try:
            src = find_source(c["file"])
            if not src:
                raise FileNotFoundError(f"không tìm thấy video '{c['file']}' trong {DOWNLOAD_DIR}")
            start, end = parse_time(c["start"]), parse_time(c["end"])
            if end <= start:
                raise ValueError(f"thời gian kết thúc ({c['end']}) phải lớn hơn bắt đầu ({c['start']})")
            if src not in durations:
                durations[src] = probe_duration(src)
            total = durations[src]
            if total is not None:
                if start >= total:
                    raise ValueError(f"bắt đầu {c['start']} vượt quá độ dài video ({format_duration(total)})")
                if end > total:
                    print(f"  (kết thúc vượt độ dài video {format_duration(total)}, sẽ cắt tới hết video)")
                    end = total

            label = safe_name(c["label"]) or safe_name(src.stem, 40)
            out = CLIPS_DIR / f"{n:03d}_{label}{'_bw' if args.bw else ''}.mp4"

            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{end - start:.3f}",
                "-map", "0:v:0", "-map", "0:a:0?",
                "-vf", vf,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                str(out),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", stdin=subprocess.DEVNULL)
            if proc.returncode != 0 or not out.exists() or out.stat().st_size == 0:
                out.unlink(missing_ok=True)
                tail = " ".join(proc.stderr.strip().splitlines()[-3:]) or f"mã lỗi {proc.returncode}"
                raise RuntimeError(f"ffmpeg báo lỗi: {tail}")
            print(f"  ✓ {out.name}")
            ok += 1
        except Exception as e:
            log_error("CẮT", target, e)
            err += 1

    print("\n" + "=" * 60)
    print(f"XONG. Cắt thành công: {ok} | Lỗi: {err}")
    print(f"Clip nằm trong: {CLIPS_DIR}")
    if err:
        print(f"Chi tiết lỗi: {ERRORS_FILE}")
    return 0


# ----------------------------------------------------------------------------
# KIỂM TRA CÀI ĐẶT
# ----------------------------------------------------------------------------
def cmd_check(_args):
    print("\n=== KIỂM TRA CÀI ĐẶT ===")
    if check_tools(need_ytdlp=True, need_ffmpeg=True, verbose=True):
        print("\nĐã đủ công cụ. Có thể chạy: python matsushita.py download")
        return 0
    print("\nCòn thiếu công cụ — làm theo hướng dẫn ở trên rồi chạy lại lệnh check.")
    return 1


# ----------------------------------------------------------------------------
# MENU & DÒNG LỆNH
# ----------------------------------------------------------------------------
MENU = """
==============================================================
   CÔNG CỤ TƯ LIỆU 松下幸之助 — tải video & cắt clip TikTok
==============================================================
   1. Tải video (urls.txt + tìm theo từ khóa)
   2. Chỉ tải các link trong urls.txt
   3. Chỉ tìm theo từ khóa và tải
   4. Chỉ tìm và ghi danh sách vào list.csv (KHÔNG tải)
   5. Cắt clip 9:16 theo cuts.csv (giữ màu)
   6. Cắt clip 9:16 theo cuts.csv (đen trắng)
   7. Kiểm tra cài đặt
   0. Thoát
"""

MENU_ACTIONS = {
    "1": ["download"],
    "2": ["download", "--no-search"],
    "3": ["download", "--no-urls"],
    "4": ["download", "--list-only"],
    "5": ["cut"],
    "6": ["cut", "--bw"],
    "7": ["check"],
}


def build_parser():
    p = argparse.ArgumentParser(
        description="Tìm, tải video tư liệu 松下幸之助 và cắt clip dọc 9:16 cho TikTok.")
    sub = p.add_subparsers(dest="cmd")

    d = sub.add_parser("download", help="tìm và tải video")
    d.add_argument("--urls", default=str(URLS_FILE.name), help="file danh sách link (mặc định urls.txt)")
    d.add_argument("--keywords", default=str(KEYWORDS_FILE.name),
                   help="file từ khóa, mỗi dòng 1 từ (mặc định keywords.txt)")
    d.add_argument("-k", "--keyword", action="append",
                   help="từ khóa tìm kiếm (dùng nhiều lần được, thay cho keywords.txt)")
    d.add_argument("--no-urls", action="store_true", help="không dùng urls.txt")
    d.add_argument("--no-search", action="store_true", help="không tìm theo từ khóa")
    d.add_argument("--list-only", action="store_true", help="chỉ tìm và ghi list.csv, không tải")
    d.add_argument("--limit", type=int, default=SEARCH_LIMIT, help="số kết quả mỗi từ khóa (mặc định 10)")
    d.add_argument("--max-minutes", type=float, default=MAX_MINUTES,
                   help="bỏ qua video dài hơn số phút này (mặc định 60)")
    d.add_argument("--cookies-from-browser", metavar="TRINH_DUYET",
                   help="dùng đăng nhập YouTube từ trình duyệt: firefox, chrome, edge, safari...")
    d.add_argument("--cookies", metavar="FILE", help="file cookies.txt (nếu YouTube đòi đăng nhập)")
    d.set_defaults(func=cmd_download)

    c = sub.add_parser("cut", help="cắt clip theo cuts.csv")
    c.add_argument("--cuts", default=str(CUTS_FILE.name), help="file danh sách đoạn cắt (mặc định cuts.csv)")
    c.add_argument("--bw", action="store_true", help="chuyển clip sang đen trắng")
    c.add_argument("--upscale", action="store_true", help="phóng clip lên đúng 1080x1920")
    c.set_defaults(func=cmd_cut)

    k = sub.add_parser("check", help="kiểm tra đã cài đủ công cụ chưa")
    k.set_defaults(func=cmd_check)
    return p


def interactive_menu():
    print(MENU)
    choice = input("Chọn số rồi nhấn Enter: ").strip()
    if choice not in MENU_ACTIONS:
        return 0
    return main(MENU_ACTIONS[choice])


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):      # tránh lỗi in chữ Nhật trên Windows cũ
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
    try:
        if len(sys.argv) == 1:
            code = interactive_menu()
            input("\nNhấn Enter để đóng...")
        else:
            code = main()
    except KeyboardInterrupt:
        print("\nĐã dừng (Ctrl+C). Những video tải xong vẫn được giữ lại.")
        code = 130
    sys.exit(code)
