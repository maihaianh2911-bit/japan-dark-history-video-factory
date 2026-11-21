# Hướng dẫn dùng `matsushita.py`

Công cụ này tìm và tải video tư liệu về **松下幸之助**, rồi cắt thành các clip dọc **9:16** để dựng TikTok.

---

## Bước 1 — Cài đặt (chỉ làm 1 lần)

### 1.1. Cài Python
- Tải tại https://www.python.org/downloads/ (bản 3.10 trở lên).
- **Windows:** khi cài, nhớ **tích vào ô "Add python.exe to PATH"**.

### 1.2. Mở cửa sổ lệnh ngay tại thư mục chứa `matsushita.py`
- **Windows:** mở thư mục trong File Explorer, bấm vào thanh địa chỉ, gõ `cmd` rồi Enter.
- **macOS:** chuột phải vào thư mục → *Services* → **New Terminal at Folder**.

### 1.3. Cài ffmpeg, Deno và yt-dlp
Gõ từng dòng sau vào cửa sổ lệnh rồi Enter:

| | Windows | macOS (cần [Homebrew](https://brew.sh)) |
|---|---|---|
| ffmpeg | `winget install Gyan.FFmpeg` | `brew install ffmpeg` |
| Deno | `winget install DenoLand.Deno` | `brew install deno` |

> Deno giúp yt-dlp tải YouTube ổn định (YouTube hiện bắt buộc có nó để lấy đủ chất lượng).
> **Windows:** cài xong ffmpeg/Deno phải **đóng cửa sổ lệnh và mở lại**.

Sau đó cài yt-dlp:
```
python -m pip install -U -r requirements.txt
```
*(macOS: gõ `python3` thay cho `python` ở mọi lệnh trong hướng dẫn này.)*

### 1.4. Kiểm tra
```
python matsushita.py check
```
Thấy toàn chữ **[OK]** là xong. Thấy **[THIẾU]** thì làm theo hướng dẫn hiện ra ngay bên dưới.

---

## Bước 2 — Tải video

**Cách dễ nhất:** gõ `python matsushita.py` (không thêm gì) → hiện menu → gõ số rồi Enter.
Trên Windows có thể **bấm đúp** vào file `matsushita.py` để mở menu.

Hoặc gõ lệnh trực tiếp:

| Muốn làm gì | Lệnh |
|---|---|
| Tải cả link trong `urls.txt` + tìm theo từ khóa | `python matsushita.py download` |
| Chỉ tải link trong `urls.txt` | `python matsushita.py download --no-search` |
| Chỉ tìm theo từ khóa và tải | `python matsushita.py download --no-urls` |
| **Chỉ tìm và xem danh sách, chưa tải** | `python matsushita.py download --list-only` |

- **Link của bạn:** mở `urls.txt`, dán mỗi dòng 1 link YouTube, lưu lại.
- **Từ khóa:** sửa trong `keywords.txt` (mỗi dòng 1 từ khóa, mặc định có sẵn 4 từ khóa).
- Script tự **bỏ qua playlist/kênh** và **video dài hơn 60 phút**, chọn chất lượng **tốt nhất nhưng không quá 1080p**, lưu dạng **mp4**.

> 💡 4 từ khóa × 10 kết quả có thể ra ~40 video, rất nặng. Nên chạy `--list-only` trước,
> mở `list.csv` xem video nào hợp, chép link vào `urls.txt`, rồi tải bằng `--no-search`.

**Kết quả:**
- Video: thư mục `downloads/matsushita/`, tên dạng `[id]_[tiêu đề].mp4`
- Danh sách: `list.csv` (tiêu đề, kênh, link, thời lượng, tên file) — mở được bằng Excel.
- Chạy lại nhiều lần không sao: video đã tải sẽ không tải lại, `list.csv` được cộng dồn.

---

## Bước 3 — Cắt clip 9:16

1. Mở `cuts.csv` (bằng Notepad, Google Sheets hoặc Excel) và điền mỗi dòng 1 đoạn:

   ```
   tên file,bắt đầu,kết thúc,nhãn
   dQw4w9WgXcQ,00:01:05,00:01:20,肉声_経営の神様
   dQw4w9WgXcQ,00:03:10,00:03:18,工場
   ```
   - **tên file:** chép từ cột "tên file" trong `list.csv`, **hoặc chỉ cần gõ ID video** (phần trước dấu `_` đầu tiên).
   - **bắt đầu / kết thúc:** luôn viết đủ dạng **`giờ:phút:giây`**, ví dụ `00:01:05` (Excel hay hiểu nhầm `1:05` thành 1 giờ 5 phút).
   - **nhãn:** tên đặt cho clip (có thể để trống).
   - Dòng bắt đầu bằng `#` sẽ bị bỏ qua.
   - Nếu dùng Excel: khi lưu chọn **"CSV UTF-8"** để không mất chữ Nhật.

2. Chạy:

| Muốn làm gì | Lệnh |
|---|---|
| Cắt clip, giữ màu | `python matsushita.py cut` |
| Cắt clip, **đen trắng** | `python matsushita.py cut --bw` |
| Phóng clip lên đúng 1080×1920 | thêm `--upscale`, ví dụ `python matsushita.py cut --bw --upscale` |

**Kết quả:** thư mục `clips/`, tên dạng `001_nhãn.mp4` (bản đen trắng có thêm `_bw`).
Khung hình được cắt lấy **phần giữa** theo tỉ lệ 9:16.

---

## Khi có lỗi

- Video nào lỗi sẽ bị **bỏ qua**, chương trình vẫn chạy tiếp. Chi tiết ghi trong **`errors.txt`**.
- Muốn dừng giữa chừng: bấm **Ctrl + C**. Video đã tải xong vẫn được giữ.

| Thông báo | Cách xử lý |
|---|---|
| `Sign in to confirm you're not a bot` | Đăng nhập YouTube trên Firefox, rồi chạy `python matsushita.py download --cookies-from-browser firefox` |
| `Video unavailable` / `Private video` | Video đã bị xóa hoặc để riêng tư — bỏ qua. |
| Lỗi lạ khi tải YouTube | Cập nhật yt-dlp: `python -m pip install -U -r requirements.txt` |
| `'python' is not recognized` | Cài lại Python và tích ô "Add python.exe to PATH", hoặc gõ `py` thay cho `python`. |
| `Không ghi được list.csv` | Đóng file `list.csv` đang mở trong Excel. |
| `không tìm thấy video ... trong downloads/matsushita` | Kiểm tra cột "tên file" trong `cuts.csv` — gõ ID video là dễ nhất. |

---

> ⚠️ Video trên YouTube (kể cả tư liệu cũ) thường có bản quyền của đài truyền hình hoặc
> doanh nghiệp. Hãy kiểm tra quyền sử dụng trước khi đăng lại lên TikTok.
