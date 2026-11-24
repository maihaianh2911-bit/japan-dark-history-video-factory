# sports-news — video dọc kiểu bản tin chuyển nhượng

Mẫu motion graphics (nền sao, thẻ cầu thủ, ô đội, nhãn TIN ĐỒN / CHÍNH THỨC, phụ đề tô chữ, thanh tiến độ)
dựng bằng [Remotion](https://www.remotion.dev/). Bản hiện tại là **demo 27 giây** về Sato Teruaki & Taira Kaima (NPB → MLB, mùa đông 2026).

```
npm install
npm run studio     # xem trước & chỉnh trong trình duyệt
npm run render     # xuất out/demo.mp4 (1080x1920, 30fps)
```

- `src/components.tsx` — các khối dùng lại: thẻ cầu thủ, ô đội, nhãn, con dấu, phụ đề…
- `src/TransferNews.tsx` — kịch bản demo: danh sách cảnh, phụ đề, dữ liệu cầu thủ.
- Ảnh cầu thủ đang là hình bóng người; thêm ảnh thật bằng trường `photo` của cầu thủ.
- Ô đội dùng chữ viết tắt, không dùng logo thật.
