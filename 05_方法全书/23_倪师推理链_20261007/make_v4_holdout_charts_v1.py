"""引擎第四版（推理链）：生成 600 张新的留出随机命盘（依据《23_倪师推理链_20261007/00_推理链方案_v1.md》七、2；由 make_v3_holdout_charts_v1.py 改来，生成办法相同，只换种子）。
出生资料按种子 METIS-V4-留出随机盘-20261007 的 SHA-256 逐项生成：阳历 1930–2010 年、日期合法、时 0–23、分 0–59、性别各半随机、经度 120；
用 chart_runner_v1.cjs（正式站快照、默认十项设置）排盘。这批盘只用于第四版推理链的覆盖描述与命例复现检验的对照，只跑一次。
写出 <out>（排盘器输出原样）；文件已存在就停。用法：python3 make_v4_holdout_charts_v1.py --out <新文件>"""
import argparse, calendar, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005'))
from m4_build_v2 import run_charts

SEED = 'METIS-V4-留出随机盘-20261007'
N = 600


def num(i, key, lo, hi):
    h = int(hashlib.sha256(f'{SEED}|{i}|{key}'.encode()).hexdigest(), 16)
    return lo + h % (hi - lo + 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    forms = {}
    for i in range(N):
        y = num(i, 'year', 1930, 2010); m = num(i, 'month', 1, 12); d = num(i, 'day', 1, calendar.monthrange(y, m)[1])
        forms[f'h{i}'] = {'calendarType': 'solar', 'isLeapMonth': False, 'longitude': 120, 'unknownTime': False, 'city': '', 'province': '', 'name': '',
                          'year': str(y), 'month': str(m), 'day': str(d), 'clockHour': str(num(i, 'hour', 0, 23)), 'clockMinute': str(num(i, 'minute', 0, 59)),
                          'gender': 'male' if num(i, 'gender', 0, 1) else 'female'}
    rows = run_charts(forms)
    out = {'schema': 'v4-holdout-charts-v1', 'seed': SEED, 'rows': [rows[k] for k in forms]}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False) + '\n')
    print(json.dumps({'charts': len(out['rows']), 'errors': sum(1 for r in out['rows'] if 'error' in r),
                      'male': sum(1 for f in forms.values() if f['gender'] == 'male')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
