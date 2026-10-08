"""M4f 认本人检验：审计与统计 v1（依据《00l_三项深化方案》v2 戊「判据与统计」）。
两步：
  audit  ：只读收卷程序（api_runner_v1.py fetch）写的 *.audit.json，按包汇总合格、待重跑、重跑用尽；不读答案表 key_m4f_v1.json。
  analyze：汇总里没有「待重跑」「未交」才读答案表与交卷，算全部统计量，写 <out>。
每包的有效交卷：原卷合格取原卷，否则取第一份合格的重跑卷；三份都不合格，记为无效卷。
内容合法性（不重跑）：「最符合」须是 A、B、C、D 之一；「排序」须是 A–D 的一个排列；缺键、类型不对，都记无效卷。
  「最符合」与「排序」第一位不一致的：以「最符合」为准，把它移到排序第一位，其余三份保持原相对次序（计数报出）。
  无效卷不选任何一份（选择计数都不加），排序对四份都记 2.5（不带信息）。
记号：每题 i、每组（正题、换陈述、换论断）、每名审者 j；四份论断按所属记为「焦点」与陪衬1–3。
  焦点：正题与换陈述组 = 本人盘那份；换论断组 = 他人真盘那份。n_i(o) = 选 o 的审者数；r_ij(o) = 审者 j 给 o 的名次。
零假设（条件精确）：四份论断对审者可交换，焦点是四份里任一份的概率各 1/4，与审者怎么选无关；各题材料互不共用（同八字两对除外），因而独立。
  可交换性不由设计保证（真人盘与随机盘生成机制不同），两种对照组用来检查这一点。
  X = Σ_i n_i(焦点)；零分布：每题 n_i(焦点) 等可能取 {n_i(o)} 四值之一，各题卷积。S = Σ_i Σ_j r_ij(焦点)，同理。
  多数票：Y_i = 焦点得票严格最多；零下 P(Y_i=1) = 1/4（有唯一最多）或 0（并列）；各题卷积。
  每组都报上、下两个单尾 p（X、S、多数票各两个）。
正负对比（三组同题配对）：
  对比甲 = 正题 − 换陈述（论断相同，陈述不同）；对比乙 = 正题 − 换论断（陈述相同，焦点论断不同）。
  d_i = 两组各自「有效卷里选中焦点的比例」之差；符号翻转精确检验：零下各题 d_i 的正负号等可能，单尾 P(Σ±d_i ≥ 实测)。
  另报名次对比：每题两组焦点平均名次之差（负对正），同样做符号翻转，单尾。
区间：各组认对率（X ÷ 有效卷数）与对比的平均差，按题成团重抽 20000 次（种子「METIS-M4f-区间-20261008」）取 2.5%、97.5% 分位。
子集（只作描述；每组按该组实际出现的人筛）：陈述满 K 条（该组所用陈述）；去掉涉及身份存疑者的题；去掉涉及同八字两对的题；
  去掉含「十四主星排布与本人相同」陪衬的题；去掉本人论断与本人陈述的 4 字相同片段数超过三张陪衬最大值 2 倍以上的题；本人论断不是严格最长的题。
审者一致：每组各题审者对四份的选择，自由边际 κ（Randolph，期望一致取 1/4）。
理由里的「都对不上」类说法：每组有效卷里出现正则 NONE_RE 的卷数（只作描述）。
用法：python3 m4f_analyze_v1.py audit --returns <存档目录> --manifest <manifest.json>
      python3 m4f_analyze_v1.py analyze --returns … --manifest … --key <key_m4f_v1.json> --describe <describe_m4f_v1.json> --persons <m3_statements_merged_v1.json> --out <结果.json>"""
import argparse, glob, hashlib, json, os, random, re, statistics
from collections import Counter, defaultdict

ARMS = ('正', '换陈述', '换论断')
SEED_CI = 'METIS-M4f-区间-20261008'
B = 20000
NONE_RE = re.compile(r'都不太?(?:符合|相符|对得上|吻合)|都对不上|没有一份(?:真正)?(?:符合|相符)|均不(?:符|相符)|皆不(?:符|相符)|四份都不')


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def conv(dists):
    out = {0: 1.0}
    for d in dists:
        nxt = defaultdict(float)
        for a, pa in out.items():
            for b, pb in d.items():
                nxt[round(a + b, 6)] += pa * pb
        out = dict(nxt)
    return out


def tail_ge(dist, x):
    return sum(p for v, p in dist.items() if v >= x - 1e-9)


def tail_le(dist, x):
    return sum(p for v, p in dist.items() if v <= x + 1e-9)


def uniform4(vals):
    d = defaultdict(float)
    for v in vals:
        d[round(v, 6)] += 0.25
    return dict(d)


OWN = ('焦点', '陪衬1', '陪衬2', '陪衬3')


def status(returns, manifest):
    packs = [p['pack'] for p in json.load(open(manifest, encoding='utf-8'))['packets']]
    st = {}
    for pk in packs:
        audits = {}
        for f in glob.glob(os.path.join(returns, f'{pk}*.audit.json')):
            a = json.load(open(f, encoding='utf-8'))
            if a['id'] == pk:
                audits[a['rerun']] = a
        ok = [r for r in sorted(audits) if audits[r]['ok']]
        if ok:
            st[pk] = ('合格', ok[0])
        elif not audits:
            st[pk] = ('未交', None)
        elif max(audits) >= 2:
            st[pk] = ('重跑用尽', None)
        else:
            st[pk] = ('待重跑', None)
    return st


def do_audit(a):
    st = status(a.returns, a.manifest)
    c = Counter(v[0] for v in st.values())
    print(json.dumps({'汇总': dict(c), '用了重跑卷的包': sorted(k for k, v in st.items() if v[0] == '合格' and v[1]),
                      '待重跑': sorted(k for k, v in st.items() if v[0] in ('待重跑', '未交')), '重跑用尽': sorted(k for k, v in st.items() if v[0] == '重跑用尽')},
                     ensure_ascii=False))


def answer(returns, pk, rerun):
    """返回 (最符合, 排序, 是否改过排序, 理由文字)；不合法返回 (None, None, False, '')。"""
    fn = os.path.join(returns, pk + (f'_重跑{rerun}' if rerun else '') + '.json')
    try:
        ans = json.load(open(fn, encoding='utf-8'))['答案'][0]
        best = str(ans.get('最符合', '')).strip()
        order = [str(x).strip() for x in ans.get('排序', [])]
        reasons = ' '.join(str(v) for v in (ans.get('理由') or {}).values()) if isinstance(ans.get('理由'), dict) else str(ans.get('理由', ''))
    except Exception:
        return None, None, False, ''
    if best not in ('A', 'B', 'C', 'D') or sorted(order) != ['A', 'B', 'C', 'D']:
        return None, None, False, ''
    moved = order[0] != best
    if moved:
        order = [best] + [x for x in order if x != best]
    return best, order, moved, reasons


def randolph(tables, k_expected):
    rows = [t for t in tables if sum(t.values()) == k_expected and k_expected >= 2]
    if not rows:
        return None
    n = k_expected
    P = [(sum(v * v for v in t.values()) - n) / (n * (n - 1)) for t in rows]
    pbar = statistics.mean(P)
    return round((pbar - 0.25) / (1 - 0.25), 4)


def arm_stats(items, data):
    X = sum(data[i]['n']['焦点'] for i in items)
    S = sum(data[i]['rank']['焦点'] for i in items)
    dX = conv([uniform4([data[i]['n'][o] for o in OWN]) for i in items])
    dS = conv([uniform4([data[i]['rank'][o] for o in OWN]) for i in items])
    ys, dY = 0, []
    for i in items:
        n = data[i]['n']
        mx = max(n.values())
        uniq = sum(1 for v in n.values() if v == mx) == 1 and mx > 0
        ys += 1 if uniq and n['焦点'] == mx else 0
        dY.append({1: 0.25, 0: 0.75} if uniq else {0: 1.0})
    dY = conv(dY)
    V = sum(data[i]['valid'] for i in items)
    return {'题数': len(items), '有效卷数': V, '选中焦点的卷数X': X, '认对率': round(X / V, 4) if V else None,
            'X零均值': round(sum(v * p for v, p in dX.items()), 4), 'P(X≥实测)': tail_ge(dX, X), 'P(X≤实测)': tail_le(dX, X),
            '焦点名次和S': S, 'P(S≤实测)': tail_le(dS, S), 'P(S≥实测)': tail_ge(dS, S),
            '焦点平均名次': round(S / sum(data[i]['k'] for i in items), 4) if items else None,
            '多数票认对题数': ys, 'P(多数票≥实测)': tail_ge(dY, ys), 'P(多数票≤实测)': tail_le(dY, ys)}


def boot(items, f, seed):
    r = rng(seed)
    vals = []
    for _ in range(B):
        s = [items[r.randrange(len(items))] for _ in items]
        v = f(s)
        if v is not None:
            vals.append(v)
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 4), round(vals[int(0.975 * len(vals)) - 1], 4)] if vals else None


def prop(D):
    return D['n']['焦点'] / D['valid'] if D['valid'] else None


def mean_rank(D):
    return D['rank']['焦点'] / D['k'] if D['k'] else None


def contrast(items, A_, B_, f, seed):
    pairs = [(f(A_[i]), f(B_[i])) for i in items]
    d = [round(x - y, 6) for x, y in pairs if x is not None and y is not None]
    dist = conv([{x: 0.5, -x: 0.5} if x else {0: 1.0} for x in d])
    return {'题数': len(d), 'Σd': round(sum(d), 4), '平均差': round(sum(d) / len(d), 4) if d else None,
            '符号翻转单尾p(正>对照)': tail_ge(dist, sum(d)) if d else None,
            '平均差95%区间': boot(items, lambda s: (lambda dd: sum(dd) / len(dd) if dd else None)([f(A_[i]) - f(B_[i]) for i in s if f(A_[i]) is not None and f(B_[i]) is not None]), seed)}


def do_analyze(a):
    st = status(a.returns, a.manifest)
    assert not [k for k, v in st.items() if v[0] in ('待重跑', '未交')], '还有待重跑或未交的包'
    key = json.load(open(a.key, encoding='utf-8'))
    desc = json.load(open(a.describe, encoding='utf-8'))
    persons = {p['person_id']: p for p in json.load(open(a.persons, encoding='utf-8'))['persons']}
    items = sorted(key['items'])
    kj = key['judges_per_arm']
    data = {arm: {i: {'n': {o: 0 for o in OWN}, 'rank': {o: 0.0 for o in OWN}, 'valid': 0, 'k': kj, 'choices': [], 'none_phrases': 0} for i in items} for arm in ARMS}
    invalid, moved, reruns = [], [], Counter()
    for pk, info in key['packets'].items():
        s, rr = st[pk]
        best, order, mv, reasons = (None, None, False, '') if s != '合格' else answer(a.returns, pk, rr)
        if s == '合格' and rr:
            reruns[info['arm']] += 1
        D = data[info['arm']][info['item']]
        L2o = {L: ('焦点' if o == info['focal'] else o) for L, o in info['letters'].items()}
        if best is None:
            invalid.append(pk)
            for o in OWN:
                D['rank'][o] += 2.5
            continue
        if mv:
            moved.append(pk)
        D['valid'] += 1
        D['n'][L2o[best]] += 1
        D['choices'].append(L2o[best])
        D['none_phrases'] += 1 if NONE_RE.search(reasons) else 0
        for k, L in enumerate(order, 1):
            D['rank'][L2o[L]] += k
    shas = {nm: hashlib.sha256(open(p, 'rb').read()).hexdigest() for nm, p in (('key', a.key), ('manifest', a.manifest), ('describe', a.describe))}
    res = {'说明': __doc__.split('\n')[0], 'inputs_sha256': shas, '每组每题审者数': kj,
           '无效卷': sorted(invalid), '排序第一位被改成「最符合」的卷': sorted(moved), '用了重跑卷的包数': dict(reruns), '组': {}, '对比': {}, '子集': {}, '逐题': {}}
    for arm in ARMS:
        g = arm_stats(items, data[arm])
        g['认对率95%区间'] = boot(items, lambda s, arm=arm: (sum(data[arm][i]['n']['焦点'] for i in s) / sum(data[arm][i]['valid'] for i in s))
                              if sum(data[arm][i]['valid'] for i in s) else None, SEED_CI + '|' + arm)
        g['审者一致Randolphκ'] = randolph([Counter(data[arm][i]['choices']) for i in items], kj)
        g['理由里「都对不上」类说法的卷数'] = sum(data[arm][i]['none_phrases'] for i in items)
        res['组'][arm] = g
    for nm, other in (('对比甲：正题−换陈述', '换陈述'), ('对比乙：正题−换论断', '换论断')):
        res['对比'][nm] = {'按比例': contrast(items, data['正'], data[other], prop, SEED_CI + '|' + nm),
                         '按名次（对照−正题，越大越偏正题）': contrast(items, data[other], data['正'], mean_rank, SEED_CI + '|名次|' + nm)}
    doubt = {pid for pid, p in persons.items() if p['identity_doubt']}
    bazi = {'H30', 'H31', 'H33', 'H34'}
    involved = {arm: {i: ({key['items'][i]['person']} | ({key['items'][i]['换陈述_person']} if arm == '换陈述' else set())
                          | ({key['items'][i]['换论断_person']} if arm == '换论断' else set())) for i in items} for arm in ARMS}
    iid_of = {key['items'][j]['person']: j for j in items}
    stmt_n = {arm: {i: desc['items'][iid_of[key['items'][i]['换陈述_person']]]['陈述条数'] if arm == '换陈述' else desc['items'][i]['陈述条数']
                    for i in items} for arm in ARMS}

    def overlap_out(i):
        v = desc['items'][i]['各份']
        mx = max(v[f'陪衬{j}']['与本人陈述相同4字片段'] for j in (1, 2, 3))
        return v['本人']['与本人陈述相同4字片段'] > 2 * mx and v['本人']['与本人陈述相同4字片段'] > 0
    subsets = {'陈述满K条': lambda arm, i: stmt_n[arm][i] >= key['K'],
               '去掉涉及身份存疑者': lambda arm, i: not involved[arm][i] & doubt,
               '去掉涉及同八字两对': lambda arm, i: not involved[arm][i] & bazi,
               '去掉含十四主星排布相同陪衬的题': lambda arm, i: not any(desc['items'][i]['各份'][f'陪衬{j}']['十四主星排布与本人相同'] for j in (1, 2, 3)),
               '去掉本人4字片段超过陪衬最大值2倍的题': lambda arm, i: not overlap_out(i),
               '本人论断不是严格最长': lambda arm, i: not desc['items'][i]['本人论断严格最长']}
    for nm, f in subsets.items():
        res['子集'][nm] = {arm: arm_stats([i for i in items if f(arm, i)], data[arm]) for arm in ARMS}
        its = [i for i in items if all(f(arm, i) for arm in ARMS)]
        res['子集'][nm]['对比甲（三组都满足的题）'] = contrast(its, data['正'], data['换陈述'], prop, SEED_CI + '|子集甲|' + nm)
        res['子集'][nm]['对比乙（三组都满足的题）'] = contrast(its, data['正'], data['换论断'], prop, SEED_CI + '|子集乙|' + nm)
    for i in items:
        res['逐题'][i] = {arm: {'焦点得票': data[arm][i]['n']['焦点'], '各份得票': data[arm][i]['n'], '焦点名次和': data[arm][i]['rank']['焦点'], '有效卷': data[arm][i]['valid']} for arm in ARMS}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({arm: {k: res['组'][arm][k] for k in ('选中焦点的卷数X', '认对率', 'P(X≥实测)', 'P(X≤实测)', 'P(S≤实测)')} for arm in ARMS}
                     | {nm: v['按比例'] for nm, v in res['对比'].items()}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('audit', 'analyze'))
    for k in ('returns', 'manifest', 'key', 'describe', 'persons', 'out'):
        ap.add_argument('--' + k)
    a = ap.parse_args()
    {'audit': do_audit, 'analyze': do_analyze}[a.cmd](a)


if __name__ == '__main__':
    main()
