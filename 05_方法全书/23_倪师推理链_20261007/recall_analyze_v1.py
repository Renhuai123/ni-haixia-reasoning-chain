"""丙 召回率：统计 v1（依据《00h_三项补充研究方案_v2.md》四、5 与 6；只作描述）。只读存档、知识库与抽样文件，只输出统计量。
1. 每包取第一份合格的裁定（save_returns_v4.py 的审计；原卷、重跑1、重跑2）；三份都不合格的包按缺失照报，它的原话不计入估计。
2. 每条原话的确认漏步：裁定为「明确漏」或「两可」的主张，按漏步号合并（两人报同一步算一条；同一漏步号里有一条判明确漏就算明确漏；
   漏步号空着的主张各算一条）；类型以裁定者为准（同一漏步号取甲的那条，没有就取乙的）。
3. 估计：各层每条原话的确认漏步数的平均 × 该层原话条数，相加得 M̂；召回率 = E ÷（E + M̂），E 为知识库收下的步（推理步 371、定性步 1314）。
   主口径只算明确漏，另报明确漏加两可。
4. 区间：每层漏步率取 Gamma(0.5 + 计数, 抽样条数) 后验，抽 100000 次（种子「METIS-V4-召回率区间-20261007」）合成召回率，报 95% 区间与单侧 95% 下界；
   另报每层「至少漏一条的原话比例」的 Clopper–Pearson 区间、每层漏步总数的泊松精确区间，以及层内按原话重抽 10000 次的百分位区间（对照）。
5. 敏感性：确认的推理步漏步里，与同一条原话核查判不成立的步结论判断相同的条数。
6. Chapman：两名找漏者各自报出、两人都报出的确认漏步（明确漏，推理步与定性步分开）；两人都报出的少于 5 条不报点估计。
   对照：原抽取甲、乙的重合（知识库来源类别），照算 Chapman。
7. 链长：确认的漏步（明确漏、适用先天），照 chain_validate_v1.check_step 校验并解析条件，前提与结论按归一表映射到结点（一个判断名只对应一个结点才算映射上），
   都能用的加进知识库的副本，在 600 张留出盘上重算命宫最长链（各结点最短推法深度的最大值）的分布，与原知识库比较。
写出 <out>；文件已存在就停。
用法：python3 recall_analyze_v1.py --sample recall_v1/sample_v1.json --finder-returns <找漏存档> --adj-returns <裁定存档> --kb chain_kb_v1.json
      --check chain_merged_v1/check_v1.json --normalized chain_merged_v1/normalized_v1.json --holdout v4_holdout_v1/holdout_charts.json
      --corpus <ni_corpus.txt> --out <新文件>"""
import argparse, collections, hashlib, json, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E
from chain_validate_v1 import check_step
from scipy.stats import beta as BETA, gamma as GAMMA

E_KB = {'推理步': 371, '定性步': 1314}
N_DRAW, N_BOOT = 100000, 10000
SEED_CI = 'METIS-V4-召回率区间-20261007'
LEVELS = ('明确漏', '两可')


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def accepted(rdir, name):
    for nm in (name, f'{name}_重跑1', f'{name}_重跑2'):
        f = os.path.join(rdir, nm + '.audit.json')
        if os.path.exists(f) and json.load(open(f, encoding='utf-8'))['ok']:
            return json.load(open(os.path.join(rdir, nm + '.json'), encoding='utf-8'))
    return None


def cp(k, n):
    lo = 0.0 if k == 0 else BETA.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else BETA.ppf(0.975, k + 1, n - k)
    return [round(float(lo), 4), round(float(hi), 4)]


def pois(x):
    lo = 0.0 if x == 0 else GAMMA.ppf(0.025, x)
    return [round(float(lo), 3), round(float(GAMMA.ppf(0.975, x + 1)), 3)]


def chapman(n1, n2, m):
    if m < 5:
        return {'n1': n1, 'n2': n2, 'm': m, '点估计': None, '说明': '两人都报出的少于 5 条，不报点估计'}
    N = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    return {'n1': n1, 'n2': n2, 'm': m, '总数估计': round(N, 2), '两人都漏的估计': round(N - (n1 + n2 - m), 2)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('sample', 'finder-returns', 'adj-returns', 'kb', 'check', 'normalized', 'holdout', 'corpus', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    smp = json.load(open(a.sample, encoding='utf-8'))
    N_h = smp['strata_sizes']
    kb = json.load(open(a.kb, encoding='utf-8'))
    text = {}
    for ln in open(a.corpus, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜', 4)
        text[t[0]] = t[4]
    out = {'schema': 'recall-v1', 'strata_sizes': N_h}
    # 1–2 收集
    missing_packs, per_T, judged = [], {}, collections.Counter()
    finder_sets = {'甲': collections.defaultdict(set), '乙': collections.defaultdict(set)}
    reps = {}
    for pk, ts in smp['packs'].items():
        J = accepted(a.adj_returns, pk)
        F = {w: accepted(a.finder_returns, f'{pk}_{w}') for w in '甲乙'}
        if J is None or None in F.values():
            missing_packs.append(pk); continue
        claims = {}
        for w, X in F.items():
            for it in X.get('items', []):
                for k, c in enumerate(it.get('漏步') or [], 1):
                    claims[(w, it['T'], k)] = c
        for t in ts:
            per_T[t] = {}
        for r in J.get('裁定', []):
            key = (r.get('来源'), r.get('T'), int(r.get('序号') or 0))
            lvl = str(r.get('判定', '')).strip()
            judged[lvl] += 1
            if lvl not in LEVELS or r.get('T') not in per_T:
                continue
            sid = str(r.get('漏步号') or '').strip() or f"{key[0]}{key[2]}"
            slot = per_T[r['T']].setdefault(sid, {'level': '两可', 'type': None, 'who': set(), 'content': None})
            if lvl == '明确漏':
                slot['level'] = '明确漏'
            if slot['type'] is None or key[0] == '甲':
                slot['type'] = r.get('类型') if r.get('类型') in E_KB else slot['type']
            slot['who'].add(key[0])
            if slot['content'] is None or key[0] == '甲':
                slot['content'] = claims.get(key)
    out['缺失的包'] = missing_packs
    out['裁定档次分布（主张条数）'] = dict(judged)
    used = {t: smp['stratum_of'][t] for t in per_T}
    n_h = collections.Counter(used.values())
    out['计入的原话条数'] = dict(n_h)

    def counts(typ, levels):
        return {t: sum(1 for s in per_T[t].values() if s['type'] == typ and s['level'] in levels) for t in per_T}
    r = rng(SEED_CI)
    res = {}
    for typ in E_KB:
        for vname, levels in (('明确漏', ('明确漏',)), ('明确漏加两可', LEVELS)):
            x = counts(typ, levels)
            xs = {h: sum(v for t, v in x.items() if used[t] == h) for h in N_h}
            M = sum(N_h[h] * xs[h] / n_h[h] for h in N_h if n_h[h])
            R = E_KB[typ] / (E_KB[typ] + M)
            draws = []
            for _ in range(N_DRAW):
                Md = sum(N_h[h] * r.gammavariate(0.5 + xs[h], 1.0 / n_h[h]) for h in N_h if n_h[h])
                draws.append(E_KB[typ] / (E_KB[typ] + Md))
            draws.sort()
            boots = []
            byh = {h: [x[t] for t in x if used[t] == h] for h in N_h}
            for _ in range(N_BOOT):
                Mb = 0.0
                for h, v in byh.items():
                    if v:
                        s = [v[r.randrange(len(v))] for _ in v]
                        Mb += N_h[h] * sum(s) / len(s)
                boots.append(E_KB[typ] / (E_KB[typ] + Mb))
            boots.sort()
            res[f'{typ}·{vname}'] = {
                '各层确认漏步数': xs, '各层抽样条数': dict(n_h), 'M估计': round(M, 2), '召回率': round(R, 4),
                '95%区间（Gamma后验合成）': [round(draws[int(0.025 * N_DRAW)], 4), round(draws[int(0.975 * N_DRAW)], 4)],
                '单侧95%下界': round(draws[int(0.05 * N_DRAW)], 4),
                '对照·层内重抽95%': [round(boots[int(0.025 * N_BOOT)], 4), round(boots[int(0.975 * N_BOOT)], 4)],
                '各层至少漏一条的原话比例': {h: {'条数': sum(1 for t in x if used[t] == h and x[t] > 0), 'n': n_h[h],
                                          'CP95': cp(sum(1 for t in x if used[t] == h and x[t] > 0), n_h[h])} for h in N_h if n_h[h]},
                '各层漏步总数泊松精确95%（换算到全层）': {h: [round(v * N_h[h] / n_h[h], 1) for v in pois(xs[h])] for h in N_h if n_h[h]}}
    out['召回率'] = res
    # 5 敏感性
    failed = {(u['T'], u['结论判断']) for u in json.load(open(a.check, encoding='utf-8'))['不成立']}
    hit = 0
    for t, ss in per_T.items():
        for s in ss.values():
            if s['level'] == '明确漏' and s['type'] == '推理步' and s['content'] and (t, (s['content'].get('结论') or {}).get('判断')) in failed:
                hit += 1
    out['敏感性·推理步漏步与核查不成立的步结论相同'] = hit
    # 6 Chapman
    ch = {}
    for typ in E_KB:
        s1 = {(t, sid) for t, ss in per_T.items() for sid, s in ss.items() if s['level'] == '明确漏' and s['type'] == typ and '甲' in s['who']}
        s2 = {(t, sid) for t, ss in per_T.items() for sid, s in ss.items() if s['level'] == '明确漏' and s['type'] == typ and '乙' in s['who']}
        ch[typ] = chapman(len(s1), len(s2), len(s1 & s2))
    src = collections.Counter((s['类型'], s['来源类别']) for s in kb['steps'])
    ctrl = {typ: chapman(src[(typ, '甲乙')] + src[(typ, '只甲')], src[(typ, '甲乙')] + src[(typ, '只乙')], src[(typ, '甲乙')]) for typ in E_KB}
    out['Chapman·找漏者'] = ch
    out['Chapman·对照·原抽取甲乙'] = ctrl
    # 7 链长
    nrm = json.load(open(a.normalized, encoding='utf-8'))
    lab = collections.defaultdict(list)
    for L, v in nrm['labels'].items():
        lab[(v['层'], v['判断'])] += nrm['label_to_nodes'][L]
    def node_of(p):
        ns = sorted(set(lab.get((p.get('层'), p.get('判断')), [])))
        return ns[0] if len(ns) == 1 else None
    nodes, steps = C.load_kb(a.kb)
    add, why = [], collections.Counter()
    for t, ss in sorted(per_T.items(), key=lambda kv: int(kv[0][1:])):
        for sid, s in sorted(ss.items()):
            if s['level'] != '明确漏' or not s['content']:
                continue
            c = dict(s['content'], 类型=s['type'])
            if c.get('适用') != '先天':
                why['不是先天'] += 1; continue
            errs, _, parsed, parsed_extra = check_step(c, text[t])
            if errs:
                why['格式或条件写法不合规'] += 1; continue
            if not c.get('可操作'):
                why['不可操作'] += 1; continue
            con = node_of(c.get('结论') or {})
            pre = [node_of(p) for p in (c.get('前提') or [])] if s['type'] == '推理步' else []
            if con is None or any(p is None for p in pre):
                why['判断映射不到唯一结点'] += 1; continue
            add.append({'step_id': f'漏-{t}-{sid}', 'T': t, '类型': s['type'], '宫': c.get('宫'), '适用': '先天', '可操作': True,
                        'parsed_conditions': parsed, 'parsed_extra': parsed_extra, 'premises': pre, 'conclusions': [con],
                        '方向': (c.get('结论') or {}).get('方向', '中'), '强度': (c.get('结论') or {}).get('强度', '倾向'), '条件': c.get('条件'), '附加条件': c.get('附加条件')})
    why['加进副本'] = len(add)
    out['链长·漏步去向'] = dict(why)
    out['链长·加进副本的步'] = {'推理步': sum(1 for x in add if x['类型'] == '推理步'), '定性步': sum(1 for x in add if x['类型'] == '定性步')}
    hold = [E.Chart(r) for r in json.load(open(a.holdout, encoding='utf-8'))['rows'] if 'error' not in r]

    def longest(stps):
        return [max((xs[0]['depth'] for xs in C.infer(ch_, nodes, stps)['命宫'].values()), default=0) for ch_ in hold]
    base = longest(steps)
    aug = longest(steps + add) if add else base
    desc = lambda v: {'中位数': statistics.median(v), '4步以上比例': round(sum(1 for x in v if x >= 4) / len(v), 4), '最大': max(v)}
    out['链长·留出盘命宫最长链'] = {'原知识库': desc(base), '加进漏步后': desc(aug), '变长的盘数': sum(1 for x, y in zip(base, aug) if y > x), '盘数': len(hold)}
    out['链长·判定'] = '样本里确认的漏步不改变「明说出来的推导很短」' if statistics.median(aug) == 2 else '加进漏步后最长链中位数不再是 2，如实描述'
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    show = {k: {kk: v[kk] for kk in ('M估计', '召回率', '95%区间（Gamma后验合成）', '单侧95%下界', '对照·层内重抽95%', '各层确认漏步数')} for k, v in res.items()}
    print(json.dumps({'召回率': show, '裁定档次': out['裁定档次分布（主张条数）'], '缺失的包': missing_packs, 'Chapman': ch, '对照': ctrl,
                      '链长': out['链长·留出盘命宫最长链'], '漏步去向': out['链长·漏步去向'], '敏感性': hit}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
