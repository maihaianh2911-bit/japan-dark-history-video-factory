# japan-dark-history-video-factory

## `matsushita.py` — tư liệu 松下幸之助 cho video dọc TikTok

Tìm và tải video tư liệu từ YouTube (yt-dlp), rồi cắt clip 9:16 bằng ffmpeg.

```
python matsushita.py                 # menu chọn bằng số
python matsushita.py check           # kiểm tra cài đặt
python matsushita.py download        # tải từ urls.txt + từ khóa trong keywords.txt
python matsushita.py cut [--bw]      # cắt clip theo cuts.csv, tùy chọn đen trắng
```

Hướng dẫn từng bước: **[HUONG_DAN.md](HUONG_DAN.md)**

| File | Vai trò |
|---|---|
| `urls.txt` | danh sách link YouTube (mỗi dòng 1 link) |
| `keywords.txt` | từ khóa tìm kiếm (mỗi dòng 1 từ khóa, tối đa 10 kết quả/từ khóa) |
| `cuts.csv` | các đoạn cần cắt: `tên file, bắt đầu, kết thúc, nhãn` |
| `downloads/matsushita/` | video đã tải, tên `[id]_[tiêu đề].mp4` |
| `list.csv` | danh sách video: tiêu đề, kênh, link, thời lượng, tên file |
| `clips/` | clip 9:16 đã cắt |
| `errors.txt` | video/đoạn cắt bị lỗi (đã bỏ qua) |
