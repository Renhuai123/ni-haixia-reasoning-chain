"""M4e 认本人检验：收卷汇总与统计 v1（依据《00h_三项补充研究方案_v2.md》甲、五至七）。分两步，第一步不读答案表。
第一步 audit：读三组的审计文件（save_returns_v4.py 写的），每组每题按「原卷、重跑1、重跑2」的次序取第一份合格的；
  三份都不合格记为「不合格作废」（按答错计）；还没有合格卷、重跑又没用完的记为「待重跑」。写出 <汇总>（已存在就覆盖；不读答案表）。
第二步 analyze：汇总里不许有「待重跑」，否则停。读答案表 key_m4e_v1.json，算：
- 各组：认对题数 k（满分 28）、单尾精确二项检验（p₀=1/4）、认对率的 Clopper–Pearson 95% 区间；真论断名次之和 S 的单尾精确检验
  （零假设下每题名次在 1–4 均匀、各题独立，卷积求 P(S ≤ 实测)）、真论断平均名次。
  格式不合法（最符合不是 A–D 之一，或排序不是 A–D 的一个排列）与「不合格作废」一样：按答错计，名次记 4。
- 配对（只作描述）：链组对平铺组、平铺组对第三版先天组、链组对第三版先天组：只一组认出的题数 b、c，配对差 (b−c)/28 及其条件精确 95% 区间
  （先求 b/(b+c) 的 Clopper–Pearson 区间，再换算），精确 McNemar 双侧 p 放附表。
- 子集与描述：陪衬与本人同性别的 22 题（陪衬档次都不超过 1）及其单尾二项 p；剔除身份存疑；只看第 0 档；陈述含干支或生肖纪年的题之外；
  不同性别陪衬的题里，审者选中的论断与本人性别不同的题数；按陈述「不带年龄」条数的中位数分高低两半各自的认对数；
  审者选中最长一份（按字数）的题数、真论断恰是最长一份的题数；真论断字母分布、审者所选字母分布；认对与没认对的题四份论断平均 Jaccard；
  与前作 M4d 全文组、综合论断组逐题对照（只作描述：审者批次、说明、候选盘处理都不同）。
写出 <out>；文件已存在就停。只打印统计量。
用法：python3 m4e_analyze_v1.py audit --root <m4e_v1> --summary <汇总.json>
      python3 m4e_analyze_v1.py analyze --root <m4e_v1> --summary <汇总.json> --sources <陈述源T表> --m4d <m4d_v1> --out <新文件>"""
import argparse, glob, json, math, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, E_DIR)
from m4_leak_check_v2 import GZ, SX

ARMS = ('链', '平', '三')
N_ITEMS = 28


def binom_tail(n, k, p=0.25):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def beta_ppf(q, a, b):
    """正则化不完全贝塔函数的反函数（二分法），用于 Clopper–Pearson。"""
    if a <= 0:
        return 0.0
    if b <= 0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def betainc(a, b, x):
    """正则化不完全贝塔 I_x(a,b)；a、b 为正整数时用二项和精确算。"""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    n = int(round(a + b - 1))
    k0 = int(round(a))
    return sum(math.comb(n, j) * x ** j * (1 - x) ** (n - j) for j in range(k0, n + 1))


def clopper_pearson(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else beta_ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta_ppf(1 - alpha / 2, k + 1, n - k)
    return [round(lo, 4), round(hi, 4)]


def ranksum_p(s, n=N_ITEMS):
    dist = {0: 1.0}
    for _ in range(n):
        nd = {}
        for t, pr in dist.items():
            for r in (1, 2, 3, 4):
                nd[t + r] = nd.get(t + r, 0.0) + pr / 4
        dist = nd
    return sum(pr for t, pr in dist.items() if t <= s)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n)


def paired(h1, h2):
    items = sorted(h1)
    b = sum(1 for i in items if h1[i] and not h2[i])
    c = sum(1 for i in items if h2[i] and not h1[i])
    n = len(items)
    if b + c == 0:
        ci = [0.0, 0.0]
    else:
        lo, hi = clopper_pearson(b, b + c)
        ci = [round((b + c) / n * (2 * lo - 1), 4), round((b + c) / n * (2 * hi - 1), 4)]
    return {'都认出': sum(1 for i in items if h1[i] and h2[i]), '只前一组': b, '只后一组': c, '都没认出': sum(1 for i in items if not h1[i] and not h2[i]),
            '配对差': round((b - c) / n, 4), '配对差95%区间（条件精确）': ci, '附表·精确McNemar双侧p': mcnemar_exact(b, c)}


def do_audit(a):
    out = {'说明': '第一步：只看审计，不读答案表', 'arms': {}}
    pend = []
    for arm in ARMS:
        rd = os.path.join(a.root, f'judge_returns_{arm}')
        res = {}
        for k in range(1, N_ITEMS + 1):
            pk = f'M{k:02d}'
            tries = []
            for name in (pk, f'{pk}_重跑1', f'{pk}_重跑2'):
                f = os.path.join(rd, name + '.audit.json')
                if os.path.exists(f):
                    au = json.load(open(f, encoding='utf-8'))
                    tries.append({'name': name, 'ok': au['ok'], 'why': au['why_not_ok']})
            acc = next((t['name'] for t in tries if t['ok']), None)
            if acc:
                st = '合格'
            elif len(tries) == 3:
                st = '不合格作废'
            else:
                st = '待重跑'
                pend.append(f'{arm}{pk}（已有 {len(tries)} 份）')
            res[pk] = {'status': st, 'accepted': acc, 'tries': tries}
        out['arms'][arm] = res
    out['待重跑'] = pend
    json.dump(out, open(a.summary, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({arm: {s: sum(1 for x in v.values() if x['status'] == s) for s in ('合格', '不合格作废', '待重跑')} for arm, v in out['arms'].items()} | {'待重跑': pend}, ensure_ascii=False))


def valid(ans):
    return isinstance(ans.get('最符合'), str) and ans['最符合'] in ('A', 'B', 'C', 'D') and sorted(ans.get('排序') or []) == ['A', 'B', 'C', 'D']


def do_analyze(a):
    assert not os.path.exists(a.out)
    summ = json.load(open(a.summary, encoding='utf-8'))
    assert not summ['待重跑'], ('还有待重跑的', summ['待重跑'])
    key = json.load(open(os.path.join(a.root, 'key_m4e_v1.json'), encoding='utf-8'))
    man = json.load(open(os.path.join(a.root, 'manifest.json'), encoding='utf-8'))
    desc = json.load(open(os.path.join(a.root, 'describe_m4e_v1.json'), encoding='utf-8'))
    src = json.load(open(a.sources, encoding='utf-8'))
    items = {i: v['true'] for i, v in key['items'].items()}
    pack_of = {pk['items'][0]: pk['pack'] for pk in man['arms']['链']}
    leak = {i for i in items if any(GZ.search(ln) or SX.search(ln) for ln in open(os.path.join(a.root, 'judge_packets_链', pack_of[i], f'{i}_陈述.txt'), encoding='utf-8'))}
    same_gender = {i for i, v in key['items'].items() if all(t <= 1 for t in v['tiers'].values())}
    tier0 = {i for i, v in key['items'].items() if all(t == 0 for t in v['tiers'].values())}
    noage = {i: src['items'][i]['不带年龄'] for i in items}
    med = statistics.median(noage.values())
    hi_half = {i for i in items if noage[i] > med}
    res = {'schema': 'm4e-analysis-v1', 'n_items': len(items), 'arms': {}, 'subset_defs': {'陪衬同性别': sorted(same_gender), '第0档': sorted(tier0),
           '陈述含干支或生肖纪年': sorted(leak), '不带年龄条数中位数': med, '不带年龄较多的一半': sorted(hi_half)},
           '真论断字母分布': {L: sum(1 for t in items.values() if t == L) for L in 'ABCD'}}
    hits = {}
    for arm in ARMS:
        per = {}
        for i in sorted(items):
            st = summ['arms'][arm][pack_of[i]]
            ans = None
            if st['status'] == '合格':
                obj = json.load(open(os.path.join(a.root, f'judge_returns_{arm}', st['accepted'] + '.json'), encoding='utf-8'))
                ans = next((x for x in obj['答案'] if x.get('题') == i), None)
            ok = ans is not None and valid(ans)
            pick = ans['最符合'] if ok else None
            rank = ans['排序'].index(items[i]) + 1 if ok else 4
            per[i] = {'status': st['status'], 'format_ok': ok, 'pick': pick, 'true': items[i], 'hit': ok and pick == items[i], 'rank_of_true': rank,
                      'pick_not_first_in_order': ok and ans['排序'][0] != pick}
        hit = {i: x['hit'] for i, x in per.items()}
        hits[arm] = hit
        k = sum(hit.values())
        S = sum(x['rank_of_true'] for x in per.values())

        def sub(ids):
            ids = sorted(ids)
            kk = sum(hit[i] for i in ids)
            return {'n_items': len(ids), 'hits': kk, 'p_binomial_one_sided': binom_tail(len(ids), kk) if ids else None}
        lengths = {i: {L: desc['items'][i]['各份'][f'{arm}{L}']['字数'] for L in 'ABCD'} for i in items}
        longest = {i: max('ABCD', key=lambda L: lengths[i][L]) for i in items}
        diff_gender = [i for i in items if i not in same_gender]
        res['arms'][arm] = {
            'hits': k, 'p_binomial_one_sided': binom_tail(len(items), k), 'passed_top1': binom_tail(len(items), k) < 0.05,
            'rate_CP95': clopper_pearson(k, len(items)),
            'rank_sum': S, 'p_rank_sum_one_sided': ranksum_p(S), 'passed_rank_sum': ranksum_p(S) < 0.05,
            'mean_rank_of_true': round(S / len(items), 4),
            'status_counts': {s: sum(1 for x in per.values() if x['status'] == s) for s in ('合格', '不合格作废')},
            'format_invalid': sum(1 for x in per.values() if x['status'] == '合格' and not x['format_ok']),
            'pick_not_first_in_order': sum(1 for x in per.values() if x['pick_not_first_in_order']),
            '所选字母分布': {L: sum(1 for x in per.values() if x['pick'] == L) for L in 'ABCD'},
            '选中最长一份的题数': sum(1 for i, x in per.items() if x['pick'] and x['pick'] == longest[i]),
            '真论断恰是最长一份的题数': sum(1 for i in items if longest[i] == items[i]),
            'subsets': {'陪衬同性别22题': sub(same_gender), '剔除身份存疑': sub(i for i in items if not key['items'][i]['identity_doubt']),
                        '只看第0档': sub(tier0), '剔除陈述含干支或生肖纪年': sub(set(items) - leak),
                        '不带年龄较多的一半': sub(hi_half), '不带年龄较少的一半': sub(set(items) - hi_half)},
            '不同性别陪衬的题里选中异性论断的题数': sum(1 for i in diff_gender if per[i]['pick'] and key['items'][i]['genders'].get(per[i]['pick'])
                                         and key['items'][i]['genders'][per[i]['pick']] != key['items'][i]['genders'][items[i]]),
            '认对与没认对的题四份论断平均Jaccard': {'认对': round(statistics.mean([desc['items'][i]['Jaccard'][arm] for i in items if hit[i]]), 4) if k else None,
                                         '没认对': round(statistics.mean([desc['items'][i]['Jaccard'][arm] for i in items if not hit[i]]), 4) if k < len(items) else None},
            'per_item': per}
    res['paired'] = {'链组对平铺组': paired(hits['链'], hits['平']), '平铺组对第三版先天组': paired(hits['平'], hits['三']), '链组对第三版先天组': paired(hits['链'], hits['三'])}
    km = json.load(open(os.path.join(a.m4d, 'key_m4d_v1.json'), encoding='utf-8'))
    mm = json.load(open(os.path.join(a.m4d, 'manifest.json'), encoding='utf-8'))
    assert {i: v['true'] for i, v in km['items'].items()} == items, '答案表与 M4d 不同'
    m4d = {}
    for arm in ('full', 'syn'):
        h = {}
        for pk in mm['arms'][arm]:
            for x in json.load(open(os.path.join(a.m4d, f'judge_returns_{arm}', f"{pk['pack']}.json"), encoding='utf-8'))['答案']:
                h[x['题']] = x['最符合'] == items[x['题']]
        m4d[arm] = h
    res['与M4d逐题对照（只作描述）'] = {f'{a1}组对M4d{a2}': paired(hits[a1], m4d[a2]) for a1 in ARMS for a2 in ('full', 'syn')}
    res['M4d认对题数'] = {arm: sum(v.values()) for arm, v in m4d.items()}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    show = {arm: {k: res['arms'][arm][k] for k in ('hits', 'p_binomial_one_sided', 'rate_CP95', 'rank_sum', 'p_rank_sum_one_sided', 'mean_rank_of_true', 'status_counts', 'format_invalid')}
            for arm in ARMS}
    print(json.dumps(show | {'paired': {k: {kk: v[kk] for kk in ('只前一组', '只后一组', '配对差', '配对差95%区间（条件精确）')} for k, v in res['paired'].items()},
                             '陪衬同性别22题': {arm: res['arms'][arm]['subsets']['陪衬同性别22题'] for arm in ARMS}}, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('audit', 'analyze'))
    ap.add_argument('--root', required=True)
    ap.add_argument('--summary', required=True)
    ap.add_argument('--sources')
    ap.add_argument('--m4d')
    ap.add_argument('--out')
    a = ap.parse_args()
    if a.cmd == 'audit':
        do_audit(a)
    else:
        assert a.sources and a.m4d and a.out
        do_analyze(a)


if __name__ == '__main__':
    main()
