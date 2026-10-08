"""M4 统计（照《01》第四、五节与《05_M4执行细则_v1》第六节；只读存档的判定与答案表，只输出统计量）。
主检验：
- 每题两次判定（甲、乙）；命中＝「最符合」等于真论断的字母。H＝甲、乙命中数的平均。
- 零分布：保持审者的实际选择不变，每题真论断位置在 A–D 中均匀随机，Monte Carlo 10⁵ 次（random.Random(20261005)），单尾 p＝P(H_sim ≥ H_obs)。
  另报同一零假设下的精确 p（按每题两人选择相同或不同，精确卷积）作核对。
- 另报：甲、乙各自命中数与精确二项检验（p=1/4，单尾）；真论断平均名次（随机期望 2.5）。
次要检验：每人本盘、他盘两组；支持率＝支持条数/陈述条数，矛盾率同理；
  差值＝本盘支持率−他盘支持率，配对符号置换检验（10⁵ 次，同一种子），单尾；按类别分组再算一遍。
敏感性：剔除身份存疑者后重算主检验。
用法：python3 m4_analyze_v1.py <m4目录> --out <新文件>"""
import argparse, collections, json, math, os, random

GROUPS = {'长相个性': {'长相', '个性', '行为'}, '路线成就': {'路线', '成就', '财'}, '婚姻六亲': {'婚姻', '子女', '父母', '兄弟', '朋友'}, '健康意外': {'健康', '意外', '官非'}}
N_MC, SEED = 100000, 20261005


def binom_tail(n, k, p=0.25):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def primary(items, picks):
    """items: {题: 真字母}；picks: {题: (甲最符合, 乙最符合)}。"""
    ids = sorted(items)
    hits = {w: sum(picks[i][j] == items[i] for i in ids) for j, w in enumerate('甲乙')}
    H = (hits['甲'] + hits['乙']) / 2
    rng = random.Random(SEED)
    ge = 0
    for _ in range(N_MC):
        s = 0
        for i in ids:
            t = rng.choice('ABCD')
            s += (picks[i][0] == t) + (picks[i][1] == t)
        ge += (s / 2 >= H - 1e-9)
    # 精确分布：两人同选一题时命中 2 或 0（概率 1/4、3/4）；不同时命中 1 或 0（概率 1/2、1/2）
    dist = {0: 1.0}
    for i in ids:
        opts = [(2, .25), (0, .75)] if picks[i][0] == picks[i][1] else [(1, .5), (0, .5)]
        nd = collections.defaultdict(float)
        for v, pv in dist.items():
            for d, pd in opts:
                nd[v + d] += pv * pd
        dist = nd
    exact = sum(pv for v, pv in dist.items() if v / 2 >= H - 1e-9)
    n = len(ids)
    return {'n_items': n, 'hits': hits, 'H': H, 'p_mc': ge / N_MC, 'p_exact_check': exact,
            'binomial_one_sided': {w: binom_tail(n, hits[w]) for w in '甲乙'}, 'chance_H': n / 4}


def sign_flip(ds):
    if not ds:
        return None
    obs = sum(ds) / len(ds)
    rng = random.Random(SEED)
    ge = sum(1 for _ in range(N_MC) if sum(d if rng.random() < .5 else -d for d in ds) / len(ds) >= obs - 1e-12)
    return {'n_persons': len(ds), 'mean_diff': obs, 'p_one_sided': ge / N_MC}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('root')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    key = json.load(open(os.path.join(a.root, 'key_v1.json'), encoding='utf-8'))
    man = json.load(open(os.path.join(a.root, 'manifest.json'), encoding='utf-8'))
    ans = {}
    for pk in man['judge_packs']:
        for w in '甲乙':
            p = os.path.join(a.root, 'judge_returns', f"{pk['pack']}_{w}.json")
            aud = json.load(open(p.replace('.json', '.audit.json'), encoding='utf-8'))
            assert not aud['violations'] and aud['read_whole'], (pk['pack'], w, '审计不干净')
            for x in json.load(open(p, encoding='utf-8'))['答案']:
                ans[(x['题'], w)] = x
    items = {i: v['true'] for i, v in key['items'].items()}
    for i in items:
        for w in '甲乙':
            x = ans[(i, w)]
            assert x['最符合'] in 'ABCD' and len(x['最符合']) == 1, (i, w)
    picks = {i: (ans[(i, '甲')]['最符合'], ans[(i, '乙')]['最符合']) for i in items}
    ranks = {w: [] for w in '甲乙'}
    for i, t in items.items():
        for w in '甲乙':
            r = ans[(i, w)].get('排序') or []
            if sorted(r) == list('ABCD'):
                ranks[w].append(r.index(t) + 1)
    res = {'schema': 'm4-analysis-v1', 'primary': primary(items, picks),
           'mean_rank_of_true': {w: (sum(v) / len(v) if v else None) for w, v in ranks.items()} | {'both': (sum(ranks['甲'] + ranks['乙']) / max(1, len(ranks['甲'] + ranks['乙'])))},
           'rank_counts': {w: len(v) for w, v in ranks.items()}, 'chance_mean_rank': 2.5}
    sens = {i: t for i, t in items.items() if not key['items'][i]['identity_doubt']}
    res['sensitivity_without_identity_doubt'] = primary(sens, {i: picks[i] for i in sens}) if sens else None
    # 次要检验
    jud = {}
    for pk in man['stmt_packs']:
        p = os.path.join(a.root, 'stmt_returns', f"{pk['pack']}.json")
        aud = json.load(open(p.replace('.json', '.audit.json'), encoding='utf-8'))
        assert not aud['violations'] and aud['read_whole'], (pk['pack'], '审计不干净')
        for g in json.load(open(p, encoding='utf-8'))['判定']:
            jud[g['组']] = {x['序号']: x['判定'] for x in g['逐条']}
    per = collections.defaultdict(dict)
    for gid, meta in key['pairs'].items():
        per[meta['person']][meta['kind']] = jud[gid]
    cats = {key['items'][i]['person']: key['items'][i]['categories'] for i in key['items']}
    def rates(sel):
        out = {'本盘': collections.Counter(), '他盘': collections.Counter()}
        ds = []
        for person, kinds in per.items():
            idx = [k for k, c in enumerate(cats[person], 1) if sel(c)]
            if not idx:
                continue
            sr = {}
            for kind in ('本盘', '他盘'):
                vals = [kinds[kind].get(k, '缺') for k in idx]
                out[kind].update(vals)
                sr[kind] = sum(v == '支持' for v in vals) / len(idx)
            ds.append(sr['本盘'] - sr['他盘'])
        tot = {k: sum(c.values()) for k, c in out.items()}
        return {'counts': {k: dict(c) for k, c in out.items()},
                'support_rate': {k: (out[k]['支持'] / tot[k] if tot[k] else None) for k in out},
                'contradiction_rate': {k: (out[k]['矛盾'] / tot[k] if tot[k] else None) for k in out},
                'paired_sign_flip_support_diff': sign_flip(ds)}
    res['secondary'] = {'all': rates(lambda c: True), **{g: rates(lambda c, s=s: c in s) for g, s in GROUPS.items()}}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    pr = res['primary']
    print(json.dumps({'n_items': pr['n_items'], 'hits': pr['hits'], 'H': pr['H'], 'chance_H': pr['chance_H'], 'p_mc': pr['p_mc'], 'p_exact_check': pr['p_exact_check'],
                      'mean_rank': res['mean_rank_of_true'], 'secondary_all': res['secondary']['all']['support_rate'],
                      'secondary_p': (res['secondary']['all']['paired_sign_flip_support_diff'] or {}).get('p_one_sided')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
