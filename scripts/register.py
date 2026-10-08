"""把文件的 SHA-256 追加登记到 02_实验/preregistration_hashes.json（首次调用时建立）。
用法：python3 scripts/register.py "登记理由" 文件1 文件2 …（路径相对于复现包根目录）"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "02_实验" / "preregistration_hashes.json"
reason, files = sys.argv[1], sys.argv[2:]
h = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}
now = datetime.datetime.now().astimezone().isoformat()
if R.exists():
    d = json.loads(R.read_text())
    d["amendments"].append({"at": now, "reason": reason, "files": h})
else:
    d = {"frozen_at": now, "note": "第三篇登记：方案、预测与分析代码在看到数据之前登记；之后的改动以追加方式登记并写明理由。", "files": h, "amendments": []}
R.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
print("已登记", len(h), "个文件")
