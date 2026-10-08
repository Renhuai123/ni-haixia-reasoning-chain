"""M4 事后敏感性分析 v2：干支纪年泄露与大限岁数泄露（依据《11b》《11c_M4事后敏感性_大限岁数泄露_v1.md》；只打印题号、计数与统计量，不打印陈述或理由内容）。
v2 比 v1 多：审者理由里引用大限岁数分段（如「26-35」）的计数；用答案表时另算「三份干扰都是同性别同局（第 0 档）的题目」与「其中再剔除干支泄露题目」两组。
1. 泄露题目（不用答案表）：在每题的陈述文件里找干支纪年（天干紧接地支，如「甲戌」）与生肖纪年（「属狗」「狗年」之类），列出含有的题号与条数。
2. 审者是否用了年份对照（不用答案表）：审者的理由里同时出现「虚岁」与「某支年」（如「戌年」）的，按题、按审者计数。
3. 敏感性（用答案表，在全部回复收齐、m4_analyze_v1.py 跑完之后运行）：剔除泄露题目，用 m4_analyze_v1.primary 重算 H 与 p。
用法：python3 m4_leak_check_v2.py <m4目录> [--with-key] --out <新文件>"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
GZ = re.compile(r'[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]')
SX = re.compile(r'属[鼠牛虎兔龙蛇马羊猴鸡狗猪]|[鼠牛虎兔龙蛇马羊猴鸡狗猪]年')
YB = re.compile(r'[子丑寅卯辰巳午未申酉戌亥]年')
DX = re.compile(r'\d+\s*[–—~-]\s*\d+')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root'); ap.add_argument('--with-key', action='store_true'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    leak = {}
    for f in sorted(glob.glob(os.path.join(a.root, 'judge_packets', 'M*', '题*_陈述.txt'))):
        q = os.path.basename(f).split('_')[0]
        lines = open(f, encoding='utf-8').read().splitlines()
        n = sum(1 for ln in lines if GZ.search(ln) or SX.search(ln))
        if n:
            leak[q] = n
    used, used_dx = {}, {}
    for f in sorted(glob.glob(os.path.join(a.root, 'judge_returns', 'M*_*.json'))):
        if f.endswith('.audit.json'):
            continue
        name = os.path.basename(f)[:-5]
        d = json.loads(open(f, encoding='utf-8').read().strip().removeprefix('```json').removesuffix('```'))
        for x in d.get('答案', []):
            k = sum(1 for t in (x.get('理由') or {}).values() if '虚岁' in t and YB.search(t))
            used[f"{x['题']}|{name.split('_')[1]}"] = k
            used_dx[f"{x['题']}|{name.split('_')[1]}"] = sum(1 for t in (x.get('理由') or {}).values() if '大限' in t and DX.search(t))
    res = {'leak_items': leak, 'n_leak_items': len(leak), 'reason_year_matching': used, 'reason_daxian_span_mentions': used_dx}
    if a.with_key:
        import m4_analyze_v1 as A
        key = json.load(open(os.path.join(a.root, 'key_v1.json'), encoding='utf-8'))
        man = json.load(open(os.path.join(a.root, 'manifest.json'), encoding='utf-8'))
        ans = {}
        for pk in man['judge_packs']:
            for w in '甲乙':
                p = os.path.join(a.root, 'judge_returns', f"{pk['pack']}_{w}.json")
                for x in json.loads(open(p, encoding='utf-8').read().strip().removeprefix('```json').removesuffix('```'))['答案']:
                    ans[(x['题'], w)] = x['最符合']
        items = {i: v['true'] for i, v in key['items'].items() if i not in leak}
        res['sensitivity_without_leak_items'] = A.primary(items, {i: (ans[(i, '甲')], ans[(i, '乙')]) for i in items}) if items else None
        t0 = {i: v['true'] for i, v in key['items'].items() if v['tiers'] and all(t == 0 for t in v['tiers'].values())}
        res['tier0_items'] = sorted(t0)
        res['sensitivity_tier0_only'] = A.primary(t0, {i: (ans[(i, '甲')], ans[(i, '乙')]) for i in t0}) if t0 else None
        t0n = {i: t for i, t in t0.items() if i not in leak}
        res['sensitivity_tier0_without_leak'] = A.primary(t0n, {i: (ans[(i, '甲')], ans[(i, '乙')]) for i in t0n}) if t0n else None
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'n_leak_items': len(leak), 'leak_items': sorted(leak), 'reasons_with_year_matching': sum(1 for v in used.values() if v),
                      'reasons_with_daxian_spans': sum(1 for v in used_dx.values() if v),
                      'sensitivity': {s: (res.get(s) or {}) and {k: res[s][k] for k in ('n_items', 'hits', 'H', 'chance_H', 'p_mc')}
                                      for s in ('sensitivity_without_leak_items', 'sensitivity_tier0_only', 'sensitivity_tier0_without_leak')}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
