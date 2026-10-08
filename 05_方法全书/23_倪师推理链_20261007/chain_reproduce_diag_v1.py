"""倪师推理链：主检验未通过后的事后诊断（依据《00e_主检验未通过后的事后诊断_v1.md》；只作描述，不报 p 值，不改知识库与引擎）。
人、候选盘、倪师判断集、剔除办法与 chain_reproduce_v1.py 完全相同（直接调用它的函数）。
D1 可达性：倪师判断集的每个结点，剔除后的引擎可用步里有没有以它为结论的步（结构上可达）；600 张留出盘上有没有任何一张推出来（实际可达）。
D2 分组描述：倪师判断集里至少一个结点实际可达的人，u 的平均数与 u < 0.5 的人数（u 取主检验结果文件里的值，不重算）。
D3 不剔除时（机制核对）：用全部引擎可用步推本人盘（各候选都推出才算）与 600 张留出盘，报得分与 u。
D4 判断集的构成：倪师判断集的步按类型、可不可操作、条件（含附加条件）里有没有「格」「其他」计数；结点按层计数。
写出 <out>；文件已存在就停。
用法：python3 chain_reproduce_diag_v1.py --kb <chain_kb> --persons <m3_statements_merged_v1.json> --holdout <v4 留出盘> --main <reproduce_v1.json> --out <新文件>"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain_reproduce_v1 as R
import ni_chain_engine_v1 as C
from chain_reproduce_v1 import E, run_charts


def kinds(s):
    xs = (s.get('条件') or []) + (s.get('附加条件') or [])
    return {'格': any(x.startswith('格') for x in xs), '其他': any(x.startswith('其他') for x in xs)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'persons', 'holdout', 'main', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    kb = json.load(open(a.kb, encoding='utf-8'))
    nodes, steps = C.load_kb(a.kb)
    eng_ids = {s['step_id'] for s in steps}
    main_u = {p['person_id']: p.get('u') for p in json.load(open(a.main, encoding='utf-8'))['各人']}
    persons = [p for p in json.load(open(a.persons, encoding='utf-8'))['persons'] if p.get('eligible')]
    hold = [r for r in json.load(open(a.holdout, encoding='utf-8'))['rows'] if 'error' not in r]
    hcharts = [E.Chart(r) for r in hold]
    hprep = [C.prepare(c, nodes, steps) for c in hcharts]
    hder_all = [C.infer(c, nodes, steps, prep=pp) for c, pp in zip(hcharts, hprep)]   # D3：不剔除，留出盘只推一次
    hnodes_all = [R.person_nodes(d, c) for d, c in zip(hder_all, hcharts)]
    rows = run_charts({f"{p['person_id']}#{i}": c['form'] for p in persons for i, c in enumerate(p['candidates'])})
    people, comp_steps, comp_layers = [], collections.Counter(), collections.Counter()
    tot = collections.Counter()
    for p in persons:
        pid, segs = p['person_id'], p['segments']
        gold_steps = [s for s in kb['steps'] if R.in_segs(s, segs) and s.get('命例特指') and s['适用'] == '先天' and s['宫'] in ('命宫', '身宫')]
        G = {n for s in gold_steps for n in s['conclusions']}
        if not G:
            continue
        for s in gold_steps:
            k = kinds(s)
            comp_steps[(s['类型'], '可操作' if s['可操作'] else '不可操作', '含格' if k['格'] else ('含其他' if k['其他'] else '无格无其他'))] += 1
        for n in G:
            comp_layers[kb['nodes'][n]['层']] += 1
        removed = {s['step_id'] for s in kb['steps'] if R.in_segs(s, segs)}
        allowed = eng_ids - removed
        concl = {n for s in steps if s['step_id'] in allowed for n in s['conclusions']}
        struct = G & concl
        reach = set()
        for c, pp in zip(hcharts, hprep):
            reach |= G & R.person_nodes(C.infer(c, nodes, steps, prep=pp, allowed=allowed), c)
        crs = [rows[f'{pid}#{i}'] for i in range(len(p['candidates']))]
        assert all('error' not in r for r in crs), pid
        cch = [E.Chart(r) for r in crs]
        own_all = set.intersection(*[R.person_nodes(C.infer(c, nodes, steps), c) for c in cch])
        s_all = len(G & own_all) / len(G)
        hs_all = [len(G & hn) / len(G) for hn in hnodes_all]
        rec = {'person_id': pid, '倪师判断集结点数': len(G), '结构上可达': len(struct), '实际可达': len(reach), '主检验u': main_u.get(pid),
               '不剔除·本人盘得分': round(s_all, 4), '不剔除·留出盘平均得分': round(sum(hs_all) / len(hs_all), 4), '不剔除·u': round(R.u_of(s_all, hs_all), 4),
               '不剔除·本人盘推出的倪师判断': sorted(G & own_all)}
        people.append(rec)
        tot['结点'] += len(G); tot['结构上可达'] += len(struct); tot['实际可达'] += len(reach)
    grp = [r for r in people if r['实际可达'] > 0]
    res = {'schema': 'chain-reproduce-diag-v1', '说明': '事后诊断，只作描述，不报 p 值；主检验结论以 reproduce_v1.json 为准（未通过）',
           'D1可达性': {'计入人数': len(people), '倪师判断集结点合计': tot['结点'], '结构上可达的结点': tot['结构上可达'], '实际可达的结点': tot['实际可达'],
                     '至少一个结点结构上可达的人数': sum(1 for r in people if r['结构上可达']), '至少一个结点实际可达的人数': len(grp)},
           'D2分组描述': {'人数': len(grp), '平均u': round(sum(r['主检验u'] for r in grp) / len(grp), 4) if grp else None,
                      'u小于0.5的人数': sum(1 for r in grp if r['主检验u'] < 0.5),
                      '其余人数': len(people) - len(grp), '其余人的平均u': round(sum(r['主检验u'] for r in people if r['实际可达'] == 0) / max(1, len(people) - len(grp)), 4)},
           'D3不剔除': {'平均u': round(sum(r['不剔除·u'] for r in people) / len(people), 4), 'u小于0.5的人数': sum(1 for r in people if r['不剔除·u'] < 0.5),
                      '本人盘得分平均': round(sum(r['不剔除·本人盘得分'] for r in people) / len(people), 4),
                      '留出盘得分平均': round(sum(r['不剔除·留出盘平均得分'] for r in people) / len(people), 4)},
           'D4构成': {'步': {'·'.join(k): n for k, n in sorted(comp_steps.items())}, '结点按层': dict(comp_layers.most_common())},
           '各人': people}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != '各人'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
