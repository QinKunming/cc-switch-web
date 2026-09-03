#!/usr/bin/env python3
"""构建 cc-switch-web 的干净部署 zip。

用法:  python tests/make_package.py [版本号]     # 默认 2.0.0
产物:  项目根目录下 cc-switch-web-<版本号>.zip

打包规则:
  - 只包含运行必需文件 + 文档 + 测试; 剔除 cc-switch 参考源码、
    cc-switch-main.zip、__pycache__、.venv 等
  - 文件名 UTF-8 + EFS 标志(Linux unzip 正确识别中文文件名)
  - *.sh 写入 Unix 可执行位 0o755, 解压即用无需 chmod
"""
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOP_FILES = [
    "server.py", "storage.py", "db.py", "config_ops.py", "models.py",
    "requirements.txt", "README.md", "run.sh", "run.bat", "watchdog.sh",
]
# 开发总结*.md 全部带上（按文件名通配）
TOP_FILES += [p.name for p in ROOT.glob("开发总结*.md")]
DIRS = {"agents": "*.py", "presets": "*.py", "static": "*", "tests": "*"}


def collect() -> list[Path]:
    files = [ROOT / n for n in TOP_FILES]
    for d, pat in DIRS.items():
        files += [p for p in (ROOT / d).glob(pat) if p.is_file()]
    missing = [f for f in files if not f.is_file()]
    if missing:
        sys.exit(f"缺失文件: {missing}")
    return sorted(files)


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else "2.0.0"
    out = ROOT / f"cc-switch-web-v{version}.zip"
    files = collect()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            arcname = f"cc-switch-web-v{version}/{rel}"
            mt = time.localtime(f.stat().st_mtime)
            info = zipfile.ZipInfo(arcname, date_time=mt[:6])
            mode = 0o755 if f.suffix == ".sh" else 0o644
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())
    size_kb = out.stat().st_size / 1024
    print(f"OK {out.name}  {len(files)} 个文件  {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
