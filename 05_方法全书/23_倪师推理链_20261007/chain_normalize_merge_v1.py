"""倪师推理链：判断归一的核验、一致程度与定稿归一表 v1（依据《00_推理链方案_v1.md》五；只核验、计数、合并，不改内容）。
逐组核对甲、乙、裁定三份归类：编号都出自本组；每个编号至少归进一个结点；结点的层只许是本组的层；改层只许改成本组的层。
一致程度（只作描述，甲对乙）：
- 两两配对：本组任意两个判断名，甲是否放进同一个结点、乙是否放进同一个结点；报两人都合的对数、任一人合的对数、二者之比（合并一致率），
  以及全部配对里两人判断相同的比例；
- 判断名：在甲、乙里「同结点伙伴」完全相同的判断名所占比例。
定稿：以裁定结果为准；同一组里层与结点名都相同的结点合成一个；结点按组、层、结点名排序后编号 N0001 起。
写出 <out>：nodes（结点号 → 层、名、成员）、label_to_nodes（判断名编号 → 结点号列表）、labels（编号 → 原层、判断）、agreement、problems。
文件已存在就停。用法：python3 chain_normalize_merge_v1.py --norm-packets <归一材料目录> --norm-returns <归一存档目录> --adj-returns <裁定存档目录> --out <新文件>"""
import argparse, collections, hashlib, itertools, json, os

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def read_coding(p, ids, layers, problems, tag):
    d = json.load(open(p, encoding='utf-8'))
    mem = collections.defaultdict(set)      # 编号 → {(层, 结点名)}
    for n in d.get('结点') or []:
        lay, name = n.get('层'), str(n.get('结点名', '')).strip()
        if lay not in layers or not name:
            problems.append({'which': tag, 'problem': f'结点层或名不合法：{lay} {name}'}); continue
        for x in n.get('成员') or []:
            if x not in ids:
                problems.append({'which': tag, 'problem': f'成员编号不在本组：{x}'}); continue
            mem[x].add((lay, name))
    missing = sorted(set(ids) - set(mem))
    if missing:
        problems.append({'which': tag, 'problem': '有编号没有归进任何结点', 'ids': missing})
    for r in d.get('改层') or []:
        if r.get('新层') not in layers:
            problems.append({'which': tag, 'problem': f"改层不合法：{r}"})
    return mem, d.get('改层') or []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('norm-packets', 'norm-returns', 'adj-returns', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    nman = json.load(open(os.path.join(a.norm_packets, 'manifest.json'), encoding='utf-8'))
    labels = {l['编号']: {'层': l['层'], '判断': l['判断']} for l in json.load(open(os.path.join(a.norm_packets, 'labels_all.json'), encoding='utf-8'))['labels']}
    problems, agreement, inputs, final = [], {}, {}, []
    for g in nman['groups']:
        G, ids, layers = g['group'], g['label_ids'], g['layers']
        paths = {'甲': os.path.join(a.norm_returns, f'{G}_甲.json'), '乙': os.path.join(a.norm_returns, f'{G}_乙.json'), '裁定': os.path.join(a.adj_returns, f'{G}_裁定.json')}
        if not all(os.path.exists(p) for p in paths.values()):
            problems.append({'group': G, 'problem': '缺少归类或裁定结果', 'missing': [k for k, p in paths.items() if not os.path.exists(p)]}); continue
        inputs[G] = {k: sha(p) for k, p in paths.items()}
        cod = {k: read_coding(p, set(ids), layers, problems, f'{G}_{k}') for k, p in paths.items()}
        mj, my = cod['甲'][0], cod['乙'][0]
        both = either = same = total = 0
        for x, y in itertools.combinations(ids, 2):
            a_ = bool(mj[x] & mj[y]); b_ = bool(my[x] & my[y])
            both += a_ and b_; either += a_ or b_; same += a_ == b_; total += 1
        mates = lambda m, x: frozenset(y for y in ids if y != x and m[x] & m[y])
        agreement[G] = {'判断名': len(ids), '甲结点数': len({n for s in mj.values() for n in s}), '乙结点数': len({n for s in my.values() for n in s}),
                        '裁定结点数': len({n for s in cod['裁定'][0].values() for n in s}),
                        '两人都合的对数': both, '任一人合的对数': either, '合并一致率': round(both / either, 4) if either else None,
                        '全部配对判断相同比例': round(same / total, 6) if total else None,
                        '同结点伙伴完全相同的判断名比例': round(sum(mates(mj, x) == mates(my, x) for x in ids) / len(ids), 4) if ids else None,
                        '甲改层': len(cod['甲'][1]), '乙改层': len(cod['乙'][1]), '裁定改层': len(cod['裁定'][1])}
        for x in ids:
            for lay, name in sorted(cod['裁定'][0].get(x, ())):
                final.append((G, lay, name, x))
    order = [g['group'] for g in nman['groups']]
    lay_order = [l for g in nman['groups'] for l in g['layers']]
    keys = sorted({(G, lay, name) for G, lay, name, _ in final}, key=lambda k: (order.index(k[0]), lay_order.index(k[1]), k[2]))
    nid = {k: f'N{i:04d}' for i, k in enumerate(keys, 1)}
    nodes = {nid[k]: {'层': k[1], '名': k[2], '组': k[0], '成员': []} for k in keys}
    l2n = collections.defaultdict(list)
    for G, lay, name, x in final:
        n = nid[(G, lay, name)]
        nodes[n]['成员'].append(x); l2n[x].append(n)
    res = {'schema': 'chain-normalized-v1', 'inputs_sha256': inputs, 'agreement': agreement,
           'counts': {'判断名': len(labels), '有结点的判断名': len(l2n), '结点': len(nodes), '拆成多个结点的判断名': sum(len(v) > 1 for v in l2n.values()),
                      'problems': len(problems)},
           'nodes': nodes, 'label_to_nodes': dict(l2n), 'labels': labels, 'problems': problems}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'counts': res['counts'], 'agreement': agreement}, ensure_ascii=False))


if __name__ == '__main__':
    main()
