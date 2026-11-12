"""
Đề 18: Tìm K file lớn nhất bằng Min-Heap — Python 3.12 trở lên.
Chạy trên Windows: python.exe main.py | Kiểm thử: python.exe main.py --test
Thực nghiệm: python.exe main.py --benchmark (tự dọn dữ liệu tạm).
Sau kết quả: nhấn Enter để tìm tiếp, nhập 0 để thoát.
Chỉ dùng thư viện chuẩn; chương trình không nén, sửa hoặc xóa file của bạn.
"""

import argparse
import gc
import os
import platform
import random
import stat
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path


# Mỗi phần tử là (kích thước byte, đường dẫn); tuple giúp xử lý hòa ổn định.
def heap_push(heap, item):
    heap.append(item)
    child = len(heap) - 1
    while child > 0:
        parent = (child - 1) // 2
        if heap[parent] <= heap[child]:
            break
        heap[parent], heap[child] = heap[child], heap[parent]
        child = parent


def sift_down(heap):
    parent = 0
    while 2 * parent + 1 < len(heap):
        child = 2 * parent + 1
        right = child + 1
        if right < len(heap) and heap[right] < heap[child]:
            child = right
        if heap[parent] <= heap[child]:
            break
        heap[parent], heap[child] = heap[child], heap[parent]
        parent = child


def top_k_files(records, k):
    if type(k) is not int or k <= 0:
        raise ValueError("K phải là số nguyên dương.")
    heap = []
    for record in records:
        if len(heap) < k:
            heap_push(heap, record)
        elif record > heap[0]:
            heap[0] = record
            sift_down(heap)
    return sorted(heap, reverse=True)


def sort_all_files(records, k):
    if type(k) is not int or k <= 0:
        raise ValueError("K phải là số nguyên dương.")
    return sorted(records, reverse=True)[:k]


def iter_files(root, stats):
    """DFS bằng các iterator đang mở; không lưu danh sách mọi file/thư mục."""
    if os.path.islink(root) or os.path.isjunction(root):
        raise ValueError("Hãy chọn thư mục thật, không chọn symlink/junction.")
    try:
        pending = [os.scandir(root)]
    except OSError as error:
        raise ValueError("Không thể mở thư mục. Hãy kiểm tra đường dẫn và quyền truy cập.") from error
    try:
        while pending:
            try:
                entry = next(pending[-1])
            except StopIteration:
                pending.pop().close()
                continue
            except OSError:
                stats["errors"] += 1
                pending.pop().close()
                continue
            try:
                if entry.is_symlink():
                    stats["links"] += 1
                    continue
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    if os.path.isjunction(entry.path):
                        stats["links"] += 1
                    else:
                        pending.append(os.scandir(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    stats["files"] += 1
                    yield info.st_size, entry.path
            except OSError:
                stats["errors"] += 1
    finally:
        for iterator in pending:
            iterator.close()


def human_size(size):
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:,.2f} {unit}"
        value /= 1024


def interactive():
    print("TÌM K FILE LỚN NHẤT — MIN-HEAP")
    print("Quét thư mục bạn chọn và thư mục con. Nhập . để chọn thư mục hiện tại.")
    while True:
        raw = input("Nhập đường dẫn thư mục: ").strip().strip('"')
        try:
            if not raw:
                raise ValueError("Đường dẫn không được để trống.")
            root = Path(raw).expanduser().resolve(strict=True)
            if not root.is_dir():
                raise ValueError("Đường dẫn phải trỏ đến một thư mục.")
            # Kiểm tra trước resolve vì resolve sẽ đi theo liên kết.
            if os.path.islink(raw) or os.path.isjunction(raw):
                raise ValueError("Hãy chọn thư mục thật, không chọn symlink/junction.")
            break
        except FileNotFoundError:
            print("Không tìm thấy thư mục. Hãy kiểm tra lại đường dẫn.")
        except PermissionError:
            print("Không có quyền truy cập thư mục này. Hãy chọn thư mục khác.")
        except (OSError, ValueError, RuntimeError):
            print("Đường dẫn không hợp lệ. Hãy nhập đường dẫn tới một thư mục có thật.")
    while True:
        try:
            k = int(input("Nhập số lượng file cần tìm K: "))
            if k <= 0:
                raise ValueError
            break
        except ValueError:
            print("K phải là số nguyên dương, ví dụ 10.")
    stats = {"files": 0, "errors": 0, "links": 0}
    records = iter_files(str(root), stats)
    try:
        result = top_k_files(records, k)
    finally:
        records.close()
    print(f"\nThư mục đã quét: {root}")
    print(f"Đã xét {stats['files']:,} file; lỗi truy cập: {stats['errors']:,}; "
          f"liên kết bỏ qua: {stats['links']:,}.")
    if result:
        print(f"\n{len(result)} FILE LỚN NHẤT (giảm dần theo byte, rồi đường dẫn):")
        for index, (size, path) in enumerate(result, 1):
            print(f"{index:>3}. {human_size(size)} ({size:,} byte)\n     {path}")
        print(f"Tổng dung lượng các file được chọn: {human_size(sum(r[0] for r in result))}")
    else:
        print("Không tìm thấy file thường có thể đọc thông tin.")


def run_tests():
    import contextlib
    import io
    import unittest
    from unittest.mock import patch

    class Tests(unittest.TestCase):
        def test_heap_invariant(self):
            heap = []
            for size in (8, 3, 7, 0, 3, 20, 1):
                heap_push(heap, (size, str(size)))
                self.assertTrue(all(heap[(i - 1) // 2] <= heap[i]
                                    for i in range(1, len(heap))))
            heap[0] = (99, "replacement")
            sift_down(heap)
            self.assertTrue(all(heap[(i - 1) // 2] <= heap[i]
                                for i in range(1, len(heap))))

        def test_boundaries_and_ties(self):
            for rows in ([], [(0, "a")], [(5, "a"), (5, "c"), (5, "b")]):
                for k in (1, 2, 10):
                    self.assertEqual(top_k_files(iter(rows), k), sort_all_files(rows, k))

        def test_invalid_k(self):
            for k in (0, -1, 1.5, "2", True):
                with self.assertRaises(ValueError):
                    top_k_files([], k)

        def test_random_and_adversarial(self):
            rng = random.Random(18)
            rows = [(rng.randrange(100), f"f{i:04}") for i in range(500)]
            for data in (rows, sorted(rows), sorted(rows, reverse=True)):
                for k in (1, 10, 100, 500, 600):
                    self.assertEqual(top_k_files(iter(data), k), sort_all_files(data, k))

        def test_heap_never_exceeds_k(self):
            original = heap_push
            lengths = []
            def observed(heap, item):
                original(heap, item)
                lengths.append(len(heap))
            with patch.object(sys.modules[__name__], "heap_push", observed):
                result = top_k_files(((i, str(i)) for i in range(1000)), 7)
            self.assertEqual(max(lengths), 7)
            self.assertEqual(len(result), 7)

        def test_empty_and_nested_unicode(self):
            with tempfile.TemporaryDirectory(prefix="ctdl-test-") as folder:
                root = Path(folder)
                stats = {"files": 0, "errors": 0, "links": 0}
                self.assertEqual(list(iter_files(folder, stats)), [])
                (root / "thư mục con").mkdir()
                (root / "rỗng.txt").write_bytes(b"")
                target = root / "thư mục con" / "tài liệu.txt"
                target.write_bytes(b"abc")
                rows = list(iter_files(folder, stats))
                self.assertEqual(top_k_files(rows, 1), [(3, str(target))])
                self.assertEqual(stats["files"], 2)

        def test_bad_root(self):
            with tempfile.TemporaryDirectory(prefix="ctdl-test-") as folder:
                with self.assertRaises(ValueError):
                    list(iter_files(str(Path(folder) / "missing"), {}))

        def test_inaccessible_child(self):
            with tempfile.TemporaryDirectory(prefix="ctdl-test-") as folder:
                blocked = Path(folder) / "blocked"
                blocked.mkdir()
                (Path(folder) / "ok.txt").write_bytes(b"ok")
                original = os.scandir
                def guarded(path):
                    if os.fspath(path) == str(blocked):
                        raise PermissionError("simulated")
                    return original(path)
                stats = {"files": 0, "errors": 0, "links": 0}
                with patch.object(os, "scandir", guarded):
                    rows = list(iter_files(folder, stats))
                self.assertEqual(len(rows), 1)
                self.assertEqual(stats["errors"], 1)

        def test_links_are_not_followed(self):
            from unittest.mock import MagicMock
            with tempfile.TemporaryDirectory(prefix="ctdl-test-") as folder:
                entry = MagicMock()
                entry.is_symlink.return_value = True
                iterator = MagicMock()
                iterator.__next__.side_effect = [entry, StopIteration]
                stats = {"files": 0, "errors": 0, "links": 0}
                with patch.object(os, "scandir", return_value=iterator):
                    self.assertEqual(list(iter_files(folder, stats)), [])
                entry.stat.assert_not_called()
                self.assertEqual(stats["links"], 1)
                iterator.close.assert_called_once()

        def test_junction_is_not_followed(self):
            with tempfile.TemporaryDirectory(prefix="ctdl-test-") as folder:
                child = Path(folder) / "junction"
                child.mkdir()
                stats = {"files": 0, "errors": 0, "links": 0}
                with patch.object(os.path, "isjunction", side_effect=lambda p: str(p) == str(child)):
                    self.assertEqual(list(iter_files(folder, stats)), [])
                self.assertEqual(stats["links"], 1)

        def test_interactive_validation(self):
            with tempfile.TemporaryDirectory(prefix="ctdl-test-") as folder:
                (Path(folder) / "demo.txt").write_bytes(b"abc")
                output = io.StringIO()
                answers = ["", str(Path(folder) / "missing"), folder, "0", "abc", "10"]
                with patch("builtins.input", side_effect=answers), contextlib.redirect_stdout(output):
                    interactive()
                self.assertIn("1 FILE LỚN NHẤT", output.getvalue())
                self.assertIn("K phải là số nguyên dương", output.getvalue())
                self.assertIn("Đường dẫn không hợp lệ", output.getvalue())
                for unwanted in ("Đề xuất:", "File ZIP, ảnh JPEG", "Thời gian quét và chọn:"):
                    self.assertNotIn(unwanted, output.getvalue())

                output = io.StringIO()
                answers = [folder, "1", "sai", "", folder, "1", "0"]
                with patch.object(sys, "argv", ["main.py"]), \
                        patch("builtins.input", side_effect=answers) as ask, \
                        contextlib.redirect_stdout(output):
                    self.assertEqual(main(), 0)
                self.assertEqual(output.getvalue().count("1 FILE LỚN NHẤT"), 2)
                self.assertEqual(sum("Nhấn Enter" in call.args[0] for call in ask.call_args_list), 3)

                output = io.StringIO()
                with patch.object(sys, "argv", ["main.py"]), \
                        patch.object(sys.modules[__name__], "interactive",
                                     side_effect=[PermissionError("Không đọc được thư mục"), None]) as scan, \
                        patch("builtins.input", side_effect=["", "0"]), \
                        contextlib.redirect_stdout(output):
                    self.assertEqual(main(), 0)
                self.assertEqual(scan.call_count, 2)
                self.assertIn("Không thể quét thư mục", output.getvalue())

                for failure, message in (
                    (FileNotFoundError("[WinError 2] F:\\private\\ư"), "Không tìm thấy thư mục"),
                    (PermissionError("[WinError 5] F:\\private"), "Không có quyền truy cập"),
                    (OSError("[WinError 123] F:\\private"), "Đường dẫn không hợp lệ"),
                    (ValueError("embedded null byte"), "Đường dẫn không hợp lệ"),
                ):
                    output = io.StringIO()
                    with self.subTest(error=type(failure).__name__), \
                            patch.object(Path, "resolve", side_effect=[failure, Path(folder)]), \
                            patch("builtins.input", side_effect=["ư", folder, "1"]), \
                            contextlib.redirect_stdout(output):
                        interactive()
                    self.assertIn(message, output.getvalue())
                    for technical in ("WinError", "Errno", "Traceback", "F:\\private", "null byte"):
                        self.assertNotIn(technical, output.getvalue())

                output = io.StringIO()
                with patch.object(sys, "argv", ["main.py", "--benchmark"]), \
                        patch.object(sys.modules[__name__], "run_benchmarks",
                                     side_effect=OSError("[WinError 1117] F:\\private")), \
                        contextlib.redirect_stderr(output):
                    self.assertEqual(main(), 1)
                self.assertIn("Không thể hoàn thành thao tác", output.getvalue())
                self.assertNotIn("WinError", output.getvalue())

    outcome = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return outcome.wasSuccessful()


def run_benchmarks():
    environment = {"python": platform.python_version(), "os": platform.platform(),
                   "processor": platform.processor(), "seed": 18, "repeats": 5}
    print("THỰC NGHIỆM — cùng đầu vào, cùng quy tắc hòa; không tính in kết quả.")
    print(f"Python {environment['python']} | {environment['os']}")
    print("Bộ nhớ: đỉnh cấp phát Python thêm, không gồm bộ dữ liệu dùng chung hoặc RAM toàn tiến trình.")
    print("N       K     Phương pháp      TB ms     Min ms     Max ms    Peak KiB")
    rows = []
    for n in (1000, 10000, 50000):
        rng = random.Random(environment["seed"])
        records = [(rng.randrange(1 << 30), f"file_{i:06}.dat") for i in range(n)]
        for k in (10, 100, 1000):
            methods = (("Min-Heap", top_k_files), ("Sort-all", sort_all_files))
            expected = sort_all_files(iter(records), k)
            samples = {name: [] for name, _ in methods}
            for _, function in methods:
                if function(iter(records), k) != expected:
                    raise AssertionError("Sai kết quả ở lượt khởi động.")
            for repeat in range(5):
                for name, function in methods[::1 if repeat % 2 == 0 else -1]:
                    gc.collect()
                    started = time.perf_counter()
                    actual = function(iter(records), k)
                    samples[name].append((time.perf_counter() - started) * 1000)
                    if actual != expected:
                        raise AssertionError("Kết quả hai phương pháp khác nhau.")
                    del actual
            for name, function in methods:
                gc.collect()
                tracemalloc.start()
                try:
                    actual = function(iter(records), k)
                    _, peak = tracemalloc.get_traced_memory()
                finally:
                    tracemalloc.stop()
                if actual != expected:
                    raise AssertionError("Sai kết quả ở lượt đo bộ nhớ.")
                row = {"n": n, "k": k, "method": name,
                       "mean_ms": sum(samples[name]) / len(samples[name]),
                       "min_ms": min(samples[name]), "max_ms": max(samples[name]),
                       "peak_kib": peak / 1024}
                rows.append(row)
                print(f"{n:<7} {k:<5} {name:<14} {row['mean_ms']:>9.3f} "
                      f"{row['min_ms']:>10.3f} {row['max_ms']:>10.3f} {row['peak_kib']:>11.2f}")
    # shortcut: đo phần chọn trên metadata; đo I/O riêng vì cache ổ đĩa làm nhiễu kết quả.
    with tempfile.TemporaryDirectory(prefix="ctdl-benchmark-") as folder:
        root = Path(folder)
        for group in range(40):
            child = root / f"nhom_{group:02}"
            child.mkdir()
            for index in range(250):
                number = group * 250 + index
                (child / f"tep_{number:05}.dat").write_bytes(b"x" * (number % 1025))
        stats = {"files": 0, "errors": 0, "links": 0}
        started = time.perf_counter()
        selected = top_k_files(iter_files(folder, stats), 10)
        elapsed_ms = (time.perf_counter() - started) * 1000
        expected_stats = {"files": 0, "errors": 0, "links": 0}
        if selected != sort_all_files(iter_files(folder, expected_stats), 10) or stats["files"] != 10000:
            raise AssertionError("Kiểm thử 10.000 file thật thất bại.")
        disk = {"files": stats["files"], "k": 10, "elapsed_ms": elapsed_ms,
                "errors": stats["errors"], "selected_bytes": sum(r[0] for r in selected)}
    print(f"\nQuét {disk['files']:,} file thật, K=10: {elapsed_ms:.3f} ms; "
          f"lỗi={disk['errors']}; khớp Sort-all. Dữ liệu tạm đã được dọn.")
    return {"environment": environment, "rows": rows, "disk": disk}


def main():
    parser = argparse.ArgumentParser(description="Tìm K file lớn nhất bằng Min-Heap tự cài.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--test", action="store_true", help="Chạy kiểm thử tự động")
    modes.add_argument("--benchmark", action="store_true", help="Đo hiệu năng và quét 10.000 file tạm")
    args = parser.parse_args()
    try:
        if args.test:
            return 0 if run_tests() else 1
        if args.benchmark:
            run_benchmarks()
        else:
            while True:
                try:
                    interactive()
                except (OSError, ValueError):
                    print("Không thể quét thư mục. Hãy kiểm tra đường dẫn và quyền truy cập.")
                while True:
                    choice = input("\nNhấn Enter để tìm tiếp, nhập 0 để thoát: ").strip()
                    if choice in ("", "0"):
                        break
                    print("Chỉ nhấn Enter để tìm tiếp hoặc nhập 0 để thoát.")
                if choice == "0":
                    break
    except (EOFError, KeyboardInterrupt):
        print("\nĐã dừng chương trình.")
        return 130
    except (OSError, ValueError):
        print("Không thể hoàn thành thao tác. Hãy kiểm tra quyền truy cập và dung lượng trống.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
