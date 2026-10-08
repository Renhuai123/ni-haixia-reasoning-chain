"""推理链：论文第一轮内审之后的事后补充分析 P1—P10（依据《00f_内审后更正与事后补充分析_v1.md》二；只作描述，报 p 值的都是事后，仅供参考）。
人、候选盘、判断集、剔除办法、600 张留出盘都与 chain_reproduce_v1.py 相同（直接调用它的函数）。
写出 <out>；文件已存在就停。
用法：python3 chain_posthoc_v1.py --kb <chain_kb> --persons <m3_statements_merged_v1.json> --holdout <v4 留出盘> --main <reproduce_v1.json>
      --adjudicated <adjudicated_v1.json> --out <新文件>"""
import argparse, collections, json, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain_reproduce_v1 as R
import ni_chain_engine_v1 as C
from chain_reproduce_v1 import E, run_charts

SEED = 'METIS-V4-事后-20261007'
MAIN6 = ['定性', '长相', '个性', '行为', '路线', '成败']


def q4(xs):
    xs = sorted(xs)
    qs = statistics.quantiles(xs, n=4, method='inclusive')
    return {'中位数': statistics.median(xs), '下四分位': qs[0], '上四分位': qs[2], '最大': xs[-1]}


def cov_one(der, nodes):
    dp = der['命宫']
    lays = {nodes[n]['层'] for n, xs in dp.items() if any(x['premises'] for x in xs)}
    return lays, max((xs[0]['depth'] for xs in dp.values()), default=0), len({x['step'] for xs in dp.values() for x in xs if x['premises']})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'persons', 'holdout', 'main', 'adjudicated', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    kb = json.load(open(a.kb, encoding='utf-8'))
    nodes, steps = C.load_kb(a.kb)
    by = {s['step_id']: s for s in steps}
    eng_ids = {s['step_id'] for s in steps}
    gen_ids = {s['step_id'] for s in steps if not s['命例特指']}
    main = {p['person_id']: p for p in json.load(open(a.main, encoding='utf-8'))['各人']}
    persons = [p for p in json.load(open(a.persons, encoding='utf-8'))['persons'] if p.get('eligible')]
    hold = [r for r in json.load(open(a.holdout, encoding='utf-8'))['rows'] if 'error' not in r]
    hc = [E.Chart(r) for r in hold]
    hp = [C.prepare(c, nodes, steps) for c in hc]
    rows = run_charts({f"{p['person_id']}#{i}": c['form'] for p in persons for i, c in enumerate(p['candidates'])})
    out = {'说明': '事后补充分析，只作描述；报 p 值的都是事后，仅供参考；主检验结论以 reproduce_v1.json 为准（未通过）'}

    # P1a 只用通则步的覆盖
    reach, depths, nr, any3, win = collections.Counter(), [], [], 0, 0
    for c, pp in zip(hc, hp):
        lays, d, k = cov_one(C.infer(c, nodes, steps, prep=pp, allowed=gen_ids), nodes)
        for l in lays:
            reach[l] += 1
        depths.append(d); nr.append(k); any3 += bool(lays & {'行为', '路线', '成败'}); win += '成败' in lays
    out['P1a·只用通则步的覆盖'] = {'通则步': len(gen_ids), '其中推理步': sum(1 for s in steps if s['step_id'] in gen_ids and s['类型'] == '推理步'),
                             '盘数': len(hc), '推到行为路线成败任一层': any3, '推到成败': win, '各层盘数': {l: reach[l] for l in MAIN6},
                             '最长链分布': dict(sorted(collections.Counter(depths).items())), '最长链': q4(depths), '用上的推理步条数': q4(nr)}

    # 逐人：主检验口径重算（核对）＋ P1b ＋ P2 ＋ P3 ＋ P5 ＋ P6
    allgold = {}
    per = []
    us_main, us_gen, nulls_gen, us_cand, us_sex = [], [], [], [], []
    for p in persons:
        pid, segs = p['person_id'], p['segments']
        gold_steps = [s for s in kb['steps'] if R.in_segs(s, segs) and s.get('命例特指') and s['适用'] == '先天' and s['宫'] in ('命宫', '身宫')]
        G = {n for s in gold_steps for n in s['conclusions']}
        if not G:
            continue
        allgold[pid] = G
        removed = {s['step_id'] for s in kb['steps'] if R.in_segs(s, segs)}
        allowed = eng_ids - removed
        allowed_g = gen_ids - removed
        crs = [rows[f'{pid}#{i}'] for i in range(len(p['candidates']))]
        cch = [E.Chart(r) for r in crs]
        cpp = [C.prepare(c, nodes, steps) for c in cch]
        own_each = [R.person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allowed), c) for c, pp in zip(cch, cpp)]
        own = set.intersection(*own_each)
        hs = [len(G & R.person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allowed), c)) / len(G) for c, pp in zip(hc, hp)]
        s_own = len(G & own) / len(G)
        u = R.u_of(s_own, hs)
        assert abs(u - main[pid]['u']) < 5e-5, (pid, '与主检验结果不一致')
        us_main.append(u)
        # P1b
        own_g = set.intersection(*[R.person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allowed_g), c) for c, pp in zip(cch, cpp)])
        hs_g = [len(G & R.person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allowed_g), c)) / len(G) for c, pp in zip(hc, hp)]
        ug = R.u_of(len(G & own_g) / len(G), hs_g)
        us_gen.append(ug); nulls_gen.append(R.null_us(hs_g))
        # P2 每张候选盘各算
        uc = sum(R.u_of(len(G & o) / len(G), hs) for o in own_each) / len(own_each)
        us_cand.append(uc)
        # P3 同性别
        sexes = {c.gender for c in cch}
        us3 = None
        if len(sexes) == 1 and next(iter(sexes)) in ('男', '女'):
            g = next(iter(sexes))
            sub = [h for h, c in zip(hs, hc) if c.gender == g]
            us3 = R.u_of(s_own, sub)
            us_sex.append(us3)
        # P5 推不出的结点
        concl = {n for s in steps if s['step_id'] in allowed for n in s['conclusions']}
        gen_in_seg = {n for s in kb['steps'] if R.in_segs(s, segs) and not s.get('命例特指') for n in s['conclusions']}
        gen_in_seg_eng = {n for s in kb['steps'] if s['step_id'] in eng_ids and R.in_segs(s, segs) and not s.get('命例特指') for n in s['conclusions']}
        unreach = sorted(G - concl)
        # P6 判断集的步在本人盘上成不成立（不剔除）
        full = [C.infer(c, nodes, steps, prep=pp) for c, pp in zip(cch, cpp)]
        p6 = collections.Counter()
        for s in gold_steps:
            conds = (s.get('条件') or []) + (s.get('附加条件') or [])
            if not s['可操作']:
                p6['原话没说出盘面'] += 1; continue
            if any(str(x).startswith('格') for x in conds):
                p6['含格'] += 1; continue
            oks = []
            for c, pp, der in zip(cch, cpp, full):
                pal = '命宫' if s['宫'] == '命宫' else c.shen
                if s['类型'] == '定性步':
                    oks.append(pal in pp['q'].get(s['step_id'], {}))
                else:
                    oks.append(pal in pp['r'].get(s['step_id'], {}) and all(x in der[pal] for x in s['premises']))
            p6['各候选都成立' if all(oks) else ('至少一张成立' if any(oks) else '都不成立')] += 1
        per.append({'person_id': pid, '候选盘数': len(cch), '性别': sorted(sexes), 'u': round(u, 4), '本人盘得分': round(s_own, 4),
                    'P1b·只用通则步u': round(ug, 4), 'P2·每张候选各算u平均': round(uc, 4), 'P3·同性别u': round(us3, 4) if us3 is not None else None,
                    'P5·推不出的结点': len(unreach), 'P5·其中时段内有通则步以它为结论': sum(1 for n in unreach if n in gen_in_seg),
                    'P5·其中时段内有引擎可用的通则步以它为结论': sum(1 for n in unreach if n in gen_in_seg_eng), 'P5·推不出的结点表': unreach,
                    'P6': dict(p6)})
    n = len(per)
    # P5 另一半：是否出现在别人的判断集里
    for r in per:
        others = set().union(*[g for q, g in allgold.items() if q != r['person_id']])
        r['P5·其中出现在别人判断集里'] = sum(1 for x in r['P5·推不出的结点表'] if x in others)
        r['P4·判断集结点也在别人判断集里'] = len(allgold[r['person_id']] & others)
    mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None
    out['P1b·只用通则步的主检验（事后）'] = {'人数': n, '平均u': mean(us_gen), 'p_单侧_事后': R.mc_p(sum(us_gen) / n, nulls_gen, SEED + '-P1'),
                                    '对照·原主检验平均u': mean(us_main)}
    single = [r['u'] for r in per if r['候选盘数'] == 1]
    multi = [r for r in per if r['候选盘数'] > 1]
    out['P2·候选盘'] = {'每张候选各算再平均的平均u': mean(us_cand), '原平均u': mean(us_main), '单候选人数': len(single), '单候选平均u': mean(single),
                     '多候选人数': len(multi), '多候选原平均u': mean([r['u'] for r in multi]), '多候选每张各算平均u': mean([r['P2·每张候选各算u平均'] for r in multi])}
    out['P3·同性别对照'] = {'人数': len(us_sex), '平均u': mean(us_sex), '这些人的原平均u': mean([r['u'] for r in per if r['P3·同性别u'] is not None]),
                       '留出盘性别': dict(collections.Counter(c.gender for c in hc))}
    # P4 时段重叠
    allp = [(p['person_id'], p['segments']) for p in persons]
    pairs = []
    for i in range(len(allp)):
        for j in range(i + 1, len(allp)):
            ov = 0
            for g in allp[i][1]:
                for h in allp[j][1]:
                    if int(g['分P']) == int(h['分P']):
                        ov += max(0, min(g['end_s'], h['end_s']) - max(g['start_s'], h['start_s']))
            if ov > 0:
                pairs.append({'两人': [allp[i][0], allp[j][0]], '重叠秒数': ov})
    multi_seg = sum(1 for s in kb['steps'] if sum(1 for _, sg in allp if R.in_segs(s, sg)) >= 2)
    out['P4·讲述时段重叠'] = {'有重叠的两人对': len(pairs), '明细': pairs, '落在两人以上时段内的知识库步': multi_seg,
                         '计入者里判断集结点也在别人判断集里的人数': sum(1 for r in per if r['P4·判断集结点也在别人判断集里'] > 0),
                         '计入者判断集结点里也在别人判断集里的结点合计': sum(r['P4·判断集结点也在别人判断集里'] for r in per)}
    tot_un = sum(r['P5·推不出的结点'] for r in per)
    out['P5·推不出的结点'] = {'合计': tot_un, '时段内有通则步以它为结论': sum(r['P5·其中时段内有通则步以它为结论'] for r in per),
                          '时段内有引擎可用的通则步以它为结论': sum(r['P5·其中时段内有引擎可用的通则步以它为结论'] for r in per),
                          '出现在别人判断集里': sum(r['P5·其中出现在别人判断集里'] for r in per)}
    p6 = collections.Counter()
    for r in per:
        p6.update(r['P6'])
    out['P6·判断集的步在本人盘上'] = dict(p6)
    # P7
    zero = [r['person_id'] for r in per if r['本人盘得分'] == 0]
    rng = random.Random(SEED)
    boots = sorted(sum(rng.choice(us_main) for _ in range(n)) / n for _ in range(10000))
    out['P7·分布'] = {'本人盘得分为0的人数': len(zero), '这些人': zero, 'u小于0.5的人数': sum(1 for x in us_main if x < .5),
                     'u小于0.5恰是得分大于0的人': {r['person_id'] for r in per if r['u'] < .5} == {r['person_id'] for r in per if r['本人盘得分'] > 0},
                     'u大于0.8的人': [r['person_id'] for r in per if r['u'] > .8], '平均u的自助法95%区间': [round(boots[249], 4), round(boots[9749], 4)]}
    # P8 连线方向
    dirc = collections.Counter()
    for s in kb['steps']:
        if s['类型'] != '推理步':
            continue
        for p_ in s['premises']:
            for c_ in s['conclusions']:
                lp, lc = kb['nodes'][p_]['层'], kb['nodes'][c_]['层']
                if lp in MAIN6 and lc in MAIN6:
                    d = MAIN6.index(lc) - MAIN6.index(lp)
                    dirc['往后推' if d > 0 else ('同层' if d == 0 else '往回推')] += 1
                else:
                    dirc['涉及其余领域'] += 1
    out['P8·连线方向'] = dict(dirc)
    # P9 两说落在哪一层
    tw = collections.Counter()
    for c, pp in zip(hc, hp):
        for lay in C.two_sayings(C.infer(c, nodes, steps, prep=pp)['命宫'], nodes):
            tw[lay] += 1
    out['P9·命宫两说按层的盘数'] = dict(tw.most_common())
    # P10 抽取一致细分
    adj = json.load(open(a.adjudicated, encoding='utf-8'))
    src = collections.Counter()
    for s in adj['steps']:
        roles = {str(x).split('-')[-1][:1] for x in (s.get('来源') or [])}
        src[(s['类型'], '甲乙' if roles >= {'甲', '乙'} else ('只甲' if roles == {'甲'} else ('只乙' if roles == {'乙'} else '补入')))] += 1
    g = adj['一致程度']['按条']
    out['P10·抽取一致'] = {'定稿来源按类型': {'·'.join(k): v for k, v in sorted(src.items())},
                        '至少一人说有推理步的条目': g['两人都有推理步'] + g['只一人有推理步'],
                        '其中两人都说有的比例': round(g['两人都有推理步'] / (g['两人都有推理步'] + g['只一人有推理步']), 4)}
    out['各人'] = per
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1, default=list) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k != '各人' and k != 'P4·讲述时段重叠'}, ensure_ascii=False, indent=1, default=list))
    print(json.dumps({k: v for k, v in out['P4·讲述时段重叠'].items() if k != '明细'}, ensure_ascii=False), out['P4·讲述时段重叠']['明细'][:20])


if __name__ == '__main__':
    main()
