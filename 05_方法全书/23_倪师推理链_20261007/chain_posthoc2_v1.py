"""推理链：论文第二轮内审之后的补充描述 Q1—Q7（依据《00g_第二轮内审后的补充描述_v1.md》；只作描述，不报 p 值）。
人、候选盘、判断集、剔除办法、600 张留出盘与 chain_reproduce_v1.py 相同（直接调用它的函数）。
写出 <out>；文件已存在就停。
用法：python3 chain_posthoc2_v1.py --kb <chain_kb> --persons <m3_statements_merged_v1.json> --holdout <v4 留出盘> --main <reproduce_v1.json> --out <新文件>"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain_reproduce_v1 as R
import ni_chain_engine_v1 as C
from chain_reproduce_v1 import E, run_charts


def has(s, pre):
    return any(str(c).startswith(pre) for c in (s.get('条件') or []) + (s.get('附加条件') or []))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'persons', 'holdout', 'main', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    kb = json.load(open(a.kb, encoding='utf-8'))
    nodes, steps = C.load_kb(a.kb)
    eng_ids = {s['step_id'] for s in steps}
    main = {p['person_id']: p for p in json.load(open(a.main, encoding='utf-8'))['各人']}
    persons = [p for p in json.load(open(a.persons, encoding='utf-8'))['persons'] if p.get('eligible')]
    hold = [r for r in json.load(open(a.holdout, encoding='utf-8'))['rows'] if 'error' not in r]
    hc = [E.Chart(r) for r in hold]
    hp = [C.prepare(c, nodes, steps) for c in hc]
    rows = run_charts({f"{p['person_id']}#{i}": c['form'] for p in persons for i, c in enumerate(p['candidates'])})
    cands = {}
    for p in persons:
        cch = [E.Chart(rows[f"{p['person_id']}#{i}"]) for i in range(len(p['candidates']))]
        cands[p['person_id']] = (cch, [C.prepare(c, nodes, steps) for c in cch])
    gold, gold_steps_of, segs_of = {}, {}, {p['person_id']: p['segments'] for p in persons}
    for p in persons:
        gs = [s for s in kb['steps'] if R.in_segs(s, p['segments']) and s.get('命例特指') and s['适用'] == '先天' and s['宫'] in ('命宫', '身宫')]
        if gs:
            gold[p['person_id']] = {n for s in gs for n in s['conclusions']}
            gold_steps_of[p['person_id']] = gs
    out = {'说明': '第二轮内审后的补充描述，只作描述，不报 p 值；主检验结论以 reproduce_v1.json 为准（未通过）'}

    # Q1 拆开 P6
    q1 = collections.Counter()
    for pid, gs in gold_steps_of.items():
        cch, cpp = cands[pid]
        full = [C.infer(c, nodes, steps, prep=pp) for c, pp in zip(cch, cpp)]
        for s in gs:
            if not s['可操作']:
                q1['原话没说出盘面'] += 1; continue
            if has(s, '格'):
                q1['含格'] += 1; continue
            if s['类型'] == '定性步':
                oks = [('命宫' if s['宫'] == '命宫' else c.shen) in pp['q'].get(s['step_id'], {}) for c, pp in zip(cch, cpp)]
                q1['起步·' + ('各候选都成立' if all(oks) else ('部分候选成立' if any(oks) else '条件都不成立'))] += 1
            else:
                st = []
                for c, pp, der in zip(cch, cpp, full):
                    pal = '命宫' if s['宫'] == '命宫' else c.shen
                    ex = pal in pp['r'].get(s['step_id'], {})
                    pr = all(x in der[pal] for x in s['premises'])
                    st.append('都成立' if ex and pr else ('前提没推出' if ex else '附加条件不成立'))
                if all(x == '都成立' for x in st):
                    k = '各候选都成立'
                elif any(x == '都成立' for x in st):
                    k = '部分候选成立'
                elif any(x == '前提没推出' for x in st):
                    k = '附加条件成立但前提没推出'
                else:
                    k = '附加条件不成立'
                q1['推理步·' + k] += 1
    out['Q1·判断集的步在本人盘上（拆开）'] = dict(sorted(q1.items()))

    # Q2 去重
    cnt = collections.Counter(n for g in gold.values() for n in g)
    step_ids = [s['step_id'] for gs in gold_steps_of.values() for s in gs]
    unreach = {}
    for pid, G in gold.items():
        removed = {s['step_id'] for s in kb['steps'] if R.in_segs(s, segs_of[pid])}
        concl = {n for s in steps if s['step_id'] in eng_ids - removed for n in s['conclusions']}
        unreach[pid] = G - concl
    out['Q2·去重'] = {'判断集结点·按人累计': sum(len(g) for g in gold.values()), '判断集结点·不重复': len(cnt), '出现在两人以上判断集里的结点': sum(1 for v in cnt.values() if v > 1),
                    '判断集的步·按人累计': len(step_ids), '判断集的步·不重复': len(set(step_ids)),
                    '剔除后推不出·按人累计': sum(len(v) for v in unreach.values()), '剔除后推不出·不重复': len(set().union(*unreach.values()))}

    # Q3 整个知识库查推不出的结点
    q3 = collections.Counter()
    for pid, U in unreach.items():
        for n in U:
            outside = [s for s in kb['steps'] if n in s['conclusions'] and not R.in_segs(s, segs_of[pid])]
            if any(s['适用'] == '先天' and not s['可操作'] for s in outside):
                q3['本人时段外有先天但不可操作的步'] += 1
            elif any(s['适用'] != '先天' for s in outside):
                q3['本人时段外只有大限流年小限的步'] += 1
            elif outside:
                q3['本人时段外另有步（其他情形）'] += 1
            else:
                q3['整个知识库在本人时段外都没有以它为结论的步'] += 1
    out['Q3·推不出的结点在整个知识库里（按人累计）'] = dict(q3)

    # Q4 推得出的判断，本人盘推出多少
    reach_people, zero_people, reach_nodes, own_nodes = 0, [], 0, 0
    for pid, G in gold.items():
        r = len(G) - len(unreach[pid])
        if r == 0:
            continue
        reach_people += 1; reach_nodes += r
        got = len(main[pid].get('本人盘推出的倪师判断') or [])
        own_nodes += got
        if got == 0:
            zero_people.append(pid)
    out['Q4·推得出的判断本人盘推出多少'] = {'至少一个结点剔除后仍有步可推的人数': reach_people, '其中本人盘一个也没推出的人数': len(zero_people),
                                 '这些人': zero_people, '剔除后仍有步可推的结点·按人累计': reach_nodes, '本人盘推出的': own_nodes}

    # Q5 按时段重叠量混入
    allp = {p['person_id']: p['segments'] for p in persons}
    in_other, people_aff = 0, set()
    for pid, gs in gold_steps_of.items():
        for s in gs:
            if any(R.in_segs(s, sg) for q, sg in allp.items() if q != pid):
                in_other += 1; people_aff.add(pid)
    def overlap(g1, g2):
        return sum(max(0, min(a['end_s'], b['end_s']) - max(a['start_s'], b['start_s'])) for a in g1 for b in g2 if int(a['分P']) == int(b['分P']))
    pairs = [(x, y) for x in gold for y in gold if x < y and overlap(allp[x], allp[y]) > 0]
    shared = {f'{x}-{y}': len(gold[x] & gold[y]) for x, y in pairs}
    out['Q5·按时段重叠量混入'] = {'判断集的步·按人累计': len(step_ids), '其中同时落在别人时段内的': in_other, '涉及人数': len(people_aff),
                            '计入者之间时段重叠的两人对': len(pairs), '其中共有判断集结点的对数': sum(1 for v in shared.values() if v), '共有结点合计': sum(shared.values()),
                            '明细': shared}

    # Q6 不加前后 2 分钟
    us = []
    for p in persons:
        pid = p['person_id']
        segs2 = [dict(g, start_s=g['start_s'] + 120, end_s=g['end_s'] - 120) for g in p['segments'] if g['end_s'] - g['start_s'] > 240]
        gs = [s for s in kb['steps'] if R.in_segs(s, segs2) and s.get('命例特指') and s['适用'] == '先天' and s['宫'] in ('命宫', '身宫')]
        G = {n for s in gs for n in s['conclusions']}
        if not G:
            continue
        removed = {s['step_id'] for s in kb['steps'] if R.in_segs(s, segs2)}
        allowed = eng_ids - removed
        cch, cpp = cands[pid]
        own = set.intersection(*[R.person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allowed), c) for c, pp in zip(cch, cpp)])
        hs = [len(G & R.person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allowed), c)) / len(G) for c, pp in zip(hc, hp)]
        us.append((pid, round(R.u_of(len(G & own) / len(G), hs), 4), len(G)))
    out['Q6·不加前后2分钟'] = {'计入人数': len(us), '平均u': round(sum(u for _, u, _ in us) / len(us), 4) if us else None, '判断集结点·按人累计': sum(g for _, _, g in us),
                           '各人': us}

    # Q7 候选盘性别不一的人
    mixed = []
    for pid in gold:
        sexes = sorted({c.gender for c in cands[pid][0]})
        if len(sexes) > 1:
            mixed.append({'person_id': pid, '性别': sexes, 'u': main[pid]['u']})
    out['Q7·候选盘性别不一'] = {'人数': len(mixed), '各人': mixed, '平均u': round(sum(m['u'] for m in mixed) / len(mixed), 4) if mixed else None}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k not in ('Q5·按时段重叠量混入',)}, ensure_ascii=False, indent=1)[:5000])
    print(json.dumps({k: v for k, v in out['Q5·按时段重叠量混入'].items() if k != '明细'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
