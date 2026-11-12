# Đề 18 – Tìm K File Lớn Nhất Bằng Min-Heap

**Bài tập cuối kỳ môn Cấu trúc dữ liệu và Giải thuật**

## Giới thiệu
Chương trình Python tìm K file có dung lượng lớn nhất trong thư mục và các thư mục con bằng thuật toán Min-Heap tự cài đặt.

## Chức năng
- Quét thư mục và tìm K file lớn nhất.
- Hiển thị kích thước và đường dẫn file.
- Sử dụng Min-Heap với độ phức tạp chọn lọc O(N log K).
- Kiểm thử tự động và so sánh hiệu năng với phương pháp sắp xếp toàn bộ.

## Cách chạy
Yêu cầu **Python 3.12 trở lên**, không cần cài thư viện ngoài.

```bash
python main.py
```

Kiểm thử:
```bash
python main.py --test
```

Đo hiệu năng:
```bash
python main.py --benchmark
```

## Ghi chú
Chương trình chỉ đọc thông tin file, không chỉnh sửa hoặc xóa dữ liệu của người dùng.
