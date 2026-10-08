"""论文第七稿内审之后补的描述性数字（依据《00_写作提纲_v2_补记2.md》；只读登记过的文件，只作描述，不是检验）。
a 归一表 1084 个结点里，哪些没进知识库（1028 个）：逐个查它们只出现在哪类步里（核查不成立、归一后自推、格式不合格）。
b 知识库里条件（含附加条件）带「格:」的步：按先天与否、可操作与否计数；先天步按可操作与否、含格与否的交叉表。
c 覆盖检验里命宫最长链 5 步的盘：最长链终点结点的出现次数（前 5 个），以及其中一条最常见链的路径（用第四版引擎在同一批留出盘上重推）。
d 两位命主的具体例子：u 最小的一位与判断集一个也推不出的一位中编号最小者。列出判断集的结点（层、名、出处 T）、剔除后知识库里有没有以它为结论的步、本人盘有没有推出。
写出 <out>；文件已存在就停。用法：python3 chain_paper_extra_v1.py --out <新文件>"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W5 = os.path.dirname(HERE)
CH = os.path.join(W5, '23_倪师推理链_20261007')
sys.path.insert(0, CH)
sys.path.insert(0, os.path.join(W5, '21_倪师断法引擎_20261005'))
import ni_chain_engine_v1 as C
import chain_reproduce_v1 as RP
from chain_reproduce_v1 import E, run_charts


def jl(*p):
    return json.load(open(os.path.join(*p), encoding='utf-8'))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    M = os.path.join(CH, 'chain_merged_v1')
    adj, chk, norm = jl(M, 'adjudicated_v1.json'), jl(M, 'check_v1.json'), jl(M, 'normalized_v1.json')
    kb = jl(CH, 'chain_kb_v1.json')
    lab = {(l['层'], l['判断']): l['编号'] for l in jl(CH, 'chain_norm_packets_v1', 'labels_all.json')['labels']}
    out = {}
    # a
    dropped = sorted(set(norm['nodes']) - set(kb['nodes']))
    kind = collections.Counter()
    for n in dropped:
        mem = set(norm['nodes'][n]['成员'])
        where = set()
        for s in adj['steps']:
            if not s['valid']:
                continue
            ls = {lab.get((p['层'], str(p['判断']).strip())) for p in [s['结论']] + list(s.get('前提') or [])}
            if ls & mem:
                v = chk['verdicts'].get(s['step_id'], {}).get('结论')
                where.add('核查不成立' if v != '成立' else '核查成立')
        kind['只在核查不成立的步里' if where == {'核查不成立'} else ('也在核查成立的步里（归一后自推被剔）' if '核查成立' in where else '其他')] += 1
    out['a·没进知识库的结点'] = {'归一表结点': len(norm['nodes']), '知识库结点': len(kb['nodes']), '差': len(dropped), '去向': dict(kind)}
    # b
    def has(s, pre):
        return any(str(c).startswith(pre) for c in (s.get('条件') or []) + (s.get('附加条件') or []))
    cnt = collections.Counter()
    for s in kb['steps']:
        cnt[('先天' if s['适用'] == '先天' else '非先天', '可操作' if s['可操作'] else '不可操作', '含格' if has(s, '格') else '不含格')] += 1
    out['b·格与可操作'] = {'·'.join(k): v for k, v in sorted(cnt.items())}
    # c
    nodes, steps = C.load_kb(os.path.join(CH, 'chain_kb_v1.json'))
    by = {s['step_id']: s for s in steps}
    rows = [r for r in jl(CH, 'v4_holdout_v1', 'holdout_charts.json')['rows'] if 'error' not in r]
    ends, paths, n5 = collections.Counter(), collections.Counter(), 0
    for r in rows:
        ch = E.Chart(r)
        dp = C.infer(ch, nodes, steps)['命宫']
        if max((xs[0]['depth'] for xs in dp.values()), default=0) != 5:
            continue
        n5 += 1
        for n, xs in dp.items():
            if xs[0]['depth'] == 5:
                ends[nodes[n]['名']] += 1
                paths[' → '.join(C.chain_path(dp, nodes, by, n))] += 1
    out['c·最长链5步的盘'] = {'盘数': n5, '终点结点前5': ends.most_common(5), '最常见的链前3': paths.most_common(3)}
    # d
    rep = jl(CH, 'chain_results_v1', 'reproduce_v1.json')
    diag = jl(CH, 'chain_results_v1', 'reproduce_diag_v1.json')
    inc = [p for p in rep['各人'] if p['计入']]
    best = min(inc, key=lambda p: (p['u'], p['person_id']))
    none = sorted(r['person_id'] for r in diag['各人'] if r['实际可达'] == 0)[0]
    persons = {p['person_id']: p for p in jl(W5, '21_倪师断法引擎_20261005', 'm3_merged_v1', 'm3_statements_merged_v1.json')['persons']}
    eng_ids = {s['step_id'] for s in steps}
    exs = []
    for pid in (best['person_id'], none):
        p = persons[pid]
        rec = next(x for x in rep['各人'] if x['person_id'] == pid)
        gold_steps = [s for s in kb['steps'] if RP.in_segs(s, p['segments']) and s.get('命例特指') and s['适用'] == '先天' and s['宫'] in ('命宫', '身宫')]
        removed = {s['step_id'] for s in kb['steps'] if RP.in_segs(s, p['segments'])}
        allowed = eng_ids - removed
        concl = {n for s in steps if s['step_id'] in allowed for n in s['conclusions']}
        got = set(rec.get('本人盘推出的倪师判断') or [])
        items = []
        for n in sorted({n for s in gold_steps for n in s['conclusions']}):
            Ts = sorted({s['T'] for s in gold_steps if n in s['conclusions']}, key=lambda t: int(t[1:]))
            items.append({'层': kb['nodes'][n]['层'], '名': kb['nodes'][n]['名'], '出处': Ts, '剔除后还有步能推出': n in concl, '本人盘推出': n in got})
        exs.append({'person_id': pid, 'u': rec['u'], '候选盘数': rec['候选盘数'], '剔除的引擎步': rec['剔除的步'], '判断集': items})
    out['d·两位命主'] = exs
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
