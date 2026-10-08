"""第四轮内审后的补充描述 S1–S9（依据《00j_第四轮内审后的更正与补充描述_v1.md》；只读已登记的结果、存档与知识库，只作描述）。
写出 <out>；文件已存在就停。用法：python3 supp_posthoc_v1.py --out chain_results_v1/supp_posthoc_v1.json"""
import argparse, collections, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from types_analyze_v1 import accepted, TYPES
from types_build_v1 import QS, norm_q

jl = lambda *p: json.load(open(os.path.join(HERE, *p), encoding='utf-8'))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    kb = jl('chain_kb_v1.json')
    steps = {s['step_id']: s for s in kb['steps']}
    t = jl('chain_results_v1', 'types_final_v1.json')
    ft = t['最终类型']
    out = {'说明': '第四轮内审后的补充描述，只作描述，不报 p 值'}
    # 最终答案（与 types_analyze_v1 相同的取法）
    man = jl('types_v1', 'formal', 'batches.json')
    fin = {}
    for b in man['batches']:
        A, _ = accepted(os.path.join(HERE, 'types_v1', 'formal_returns'), f"{b['batch']}_甲")
        B, _ = accepted(os.path.join(HERE, 'types_v1', 'formal_returns'), f"{b['batch']}_乙")
        J, _ = accepted(os.path.join(HERE, 'types_v1', 'adj_returns'), b['batch'])
        adj = {(x['编号'], x['项']): x for x in J['裁定']}
        ia, ib = {x['编号']: x for x in A['归类']}, {x['编号']: x for x in B['归类']}
        for i in b['steps']:
            row = {}
            for k in QS + ['标A', '标B', '标C']:
                nz = norm_q if k in QS else (lambda v: str(v or '').strip())
                va, vb = nz(ia[i].get(k)), nz(ib[i].get(k))
                row[k] = va if va == vb else nz(adj[(i, k)]['裁定'])
            row['问4依据'] = {'甲': ia[i].get('问4依据', ''), '乙': ib[i].get('问4依据', ''), '裁定': adj.get((i, '问4'), {}).get('依据', '')}
            fin[i] = row
    C = set(t['标C为是的编号'])
    out['S1·标C按类型'] = dict(collections.Counter(ft[i] for i in C))
    out['S2·标A×类型'] = {f: dict(collections.Counter(ft[i] for i in ft if fin[i]['标A'] == f)) for f in ('主要靠附加条件', '不主要靠附加条件', '无附加条件')}
    bx = t['标B×知识库命例特指']
    out['S3·标B与命例特指不一致'] = {'命例特指但原话不是在讲具体的人': bx['True'].get('原话不是在讲具体的人', 0),
                               '通则但在讲具体的人': bx['False'].get('仍成立', 0) + bx['False'].get('不成立', 0)}
    # 认本人
    m = jl('chain_results_v1', 'm4e_analysis_v1.json')
    key = jl('m4e_v1', 'key_m4e_v1.json')
    desc = jl('m4e_v1', 'describe_m4e_v1.json')
    diff = [i for i, v in key['items'].items() if not all(x <= 1 for x in v['tiers'].values())]
    out['S4·陪衬不按性别的题'] = {'题': sorted(diff), **{arm: sum(1 for i in diff if m['arms'][arm]['per_item'][i]['hit']) for arm in '链平三'}}
    s5 = {}
    for arm in '链平三':
        longest = {i: max('ABCD', key=lambda L: desc['items'][i]['各份'][f'{arm}{L}']['字数']) for i in key['items']}
        picks = {i: m['arms'][arm]['per_item'][i]['pick'] for i in key['items']}
        sel = [i for i in key['items'] if picks[i] == longest[i]]
        s5[arm] = {'选中最长一份的题数': len(sel), '其中恰是真论断': sum(1 for i in sel if key['items'][i]['true'] == longest[i]),
                   '真论断本身最长的题数': sum(1 for i in key['items'] if key['items'][i]['true'] == longest[i])}
    out['S5·选中最长'] = s5
    groups = collections.defaultdict(list)
    for i, v in key['items'].items():
        groups[tuple(sorted(v['letters'].values()))].append(i)
    out['S6·当事人完全相同的题组'] = sorted((sorted(g) for g in groups.values() if len(g) > 1), key=lambda g: g[0])
    out['S6·涉及题数'] = sum(len(g) for g in out['S6·当事人完全相同的题组'])
    # 召回率：两可的推理步主张
    c7 = collections.Counter()
    why8 = collections.Counter()
    for f in sorted(glob.glob(os.path.join(HERE, 'recall_v1', 'adj_returns', 'R??.json'))):
        pk = os.path.basename(f)[:3]
        J = json.load(open(f, encoding='utf-8'))
        F = {w: json.load(open(os.path.join(HERE, 'recall_v1', 'finder_returns', f'{pk}_{w}.json'), encoding='utf-8')) for w in '甲乙'}
        cl = {(w, it['T'], k): x for w, X in F.items() for it in X['items'] for k, x in enumerate(it.get('漏步') or [], 1)}
        for r in J['裁定']:
            x = cl.get((r['来源'], r['T'], int(r['序号'])))
            if x and r.get('判定') == '两可' and r.get('类型') == '推理步':
                c7['紧接承上' if '紧接' in str(x.get('连接', '')) else '其他连接'] += 1
    out['S7·两可的推理步主张按连接'] = dict(c7)
    rc = jl('chain_results_v1', 'recall_v1.json')
    out['S8·说明'] = '链长分析的去向只按全部 46 条记了总数；推理步 12 条的去向由同一规则重算'
    # S8：用 recall_analyze_v1 的同一判定重算推理步的去向
    import recall_analyze_v1 as RA
    from chain_validate_v1 import check_step
    nrm = jl('chain_merged_v1', 'normalized_v1.json')
    lab = collections.defaultdict(list)
    for L, v in nrm['labels'].items():
        lab[(v['层'], v['判断'])] += nrm['label_to_nodes'][L]
    node_of = lambda p: (lambda ns: ns[0] if len(ns) == 1 else None)(sorted(set(lab.get((p.get('层'), p.get('判断')), []))))
    text = {}
    for ln in open(os.path.join(os.path.dirname(HERE), '20_全书倪师全面比对_20261005', 'packets_v1', 'Q01', 'ni_corpus.txt'), encoding='utf-8'):
        q = ln.rstrip('\n').split('｜', 4)
        text[q[0]] = q[4]
    smp = jl('recall_v1', 'sample_v1.json')
    per = {}
    for pk, ts in smp['packs'].items():
        J = RA.accepted(os.path.join(HERE, 'recall_v1', 'adj_returns'), pk)
        F = {w: RA.accepted(os.path.join(HERE, 'recall_v1', 'finder_returns'), f'{pk}_{w}') for w in '甲乙'}
        cl = {(w, it['T'], k): x for w, X in F.items() for it in X.get('items', []) for k, x in enumerate(it.get('漏步') or [], 1)}
        for r in J.get('裁定', []):
            key_ = (r.get('来源'), r.get('T'), int(r.get('序号') or 0))
            if r.get('判定') not in ('明确漏', '两可'):
                continue
            sid = str(r.get('漏步号') or '').strip() or f'{key_[0]}{key_[2]}'
            slot = per.setdefault((r['T'], sid), {'level': '两可', 'type': None, 'content': None, 'who': key_[0]})
            if r.get('判定') == '明确漏':
                slot['level'] = '明确漏'
            if slot['type'] is None or key_[0] == '甲':
                slot['type'] = r.get('类型') if r.get('类型') in ('推理步', '定性步') else slot['type']
            if slot['content'] is None or key_[0] == '甲':
                slot['content'] = cl.get(key_)
    for (T, sid), s in per.items():
        if s['level'] != '明确漏' or s['type'] != '推理步' or not s['content']:
            continue
        c = dict(s['content'], 类型='推理步')
        if c.get('适用') != '先天':
            why8['不是先天'] += 1; continue
        errs, _, _, _ = check_step(c, text[T])
        if errs:
            why8['格式或条件写法不合规'] += 1; continue
        if not c.get('可操作'):
            why8['不可操作'] += 1; continue
        if node_of(c.get('结论') or {}) is None or any(node_of(p) is None for p in (c.get('前提') or [])):
            why8['判断映射不到唯一结点'] += 1; continue
        why8['加进副本'] += 1
    out['S8·明确漏的推理步去向'] = dict(why8)
    assert sum(why8.values()) == sum(rc['召回率']['推理步·明确漏']['各层确认漏步数'].values()) and why8.get('加进副本', 0) == rc['链长·加进副本的步']['推理步']
    out['S9·T96-c2问4依据'] = fin['T96-c2']['问4依据'] | {'最终类型': ft['T96-c2']}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
