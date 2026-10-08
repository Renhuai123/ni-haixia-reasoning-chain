"""倪师推理链：编译推理链知识库 v1（依据《00_推理链方案_v1.md》五、六、七、1；只合并与换算，不改任何步的内容）。
输入：裁定核验后的合并文件（chain_adjudicate_validate_v1.py）、逐步核查汇总（chain_check_merge_v1.py）、定稿归一表（chain_normalize_merge_v1.py）、
归一材料包里的 labels_all.json（判断名 → 编号）。
收哪些步：格式合格（valid）且核查结论为「成立」。不收的分类计数：格式不合格、核查不成立、没有有效核查结论。
换算：每步的结论与各前提，按（层, 判断）找到判断名编号，再按归一表换成结点号（一个判断名可对应几个结点）；
前提结点取并集（全部要推出来这一步才成立），结论结点取并集。找不到编号或结点的，该步不收并列入 problems。
推理步换算后结论结点全部已在前提里的（归一后成了自己推自己），不进引擎，另计「归一后同义自推」。
写出 <out>：nodes、steps（全部收下的步，含不可操作的与大限流年的；引擎自己只取可操作且适用先天的）、counts、excluded、problems。
文件已存在就停。用法：python3 compile_chain_kb_v1.py --adjudicated <合并文件> --check <核查汇总> --norm <归一表> --labels <labels_all.json> --out <新文件>"""
import argparse, collections, hashlib, json, os

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('adjudicated', 'check', 'norm', 'labels', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    adj = json.load(open(a.adjudicated, encoding='utf-8'))
    chk = json.load(open(a.check, encoding='utf-8'))['verdicts']
    norm = json.load(open(a.norm, encoding='utf-8'))
    lab = {(l['层'], l['判断']): l['编号'] for l in json.load(open(a.labels, encoding='utf-8'))['labels']}
    l2n = norm['label_to_nodes']
    excluded, problems, steps = collections.Counter(), [], []

    def to_nodes(p):
        k = (p.get('层'), str(p.get('判断', '')).strip())
        lid = lab.get(k)
        return (lid, l2n.get(lid)) if lid else (None, None)
    for s in adj['steps']:
        if not s['valid']:
            excluded['格式不合格'] += 1; continue
        v = chk.get(s['step_id'])
        if v is None:
            excluded['没有有效核查结论'] += 1; continue
        if v['结论'] != '成立':
            excluded['核查不成立'] += 1; continue
        lid, cn = to_nodes(s['结论'])
        if not cn:
            problems.append({'step_id': s['step_id'], 'problem': f"结论找不到结点：{s['结论'].get('层')} {s['结论'].get('判断')}"}); continue
        pn, bad = [], False
        for p in s.get('前提') or []:
            plid, ns = to_nodes(p)
            if not ns:
                problems.append({'step_id': s['step_id'], 'problem': f"前提找不到结点：{p.get('层')} {p.get('判断')}"}); bad = True; break
            pn += ns
        if bad:
            continue
        pn = sorted(set(pn)); cn = sorted(set(cn))
        if s['类型'] == '推理步' and set(cn) <= set(pn):
            excluded['归一后同义自推'] += 1; continue
        steps.append({**{k: s.get(k) for k in ('step_id', 'T', '分P', '时间', 'batch', '类型', '宫', '适用', '条件', '附加条件', 'parsed_conditions', 'parsed_extra',
                                               '前提', '结论', '连接', '原话摘录', '命例特指', '可操作', '来源类别')},
                      'premises': pn if s['类型'] == '推理步' else [], 'conclusions': cn,
                      '方向': s['结论'].get('方向'), '强度': s['结论'].get('强度'), '核查理由': v['理由']})
    used = {n for s in steps for n in s['premises'] + s['conclusions']}
    nodes = {k: {'层': v['层'], '名': v['名']} for k, v in norm['nodes'].items() if k in used}
    c = collections.Counter((s['类型'], s['适用'], bool(s['可操作'])) for s in steps)
    res = {'schema': 'chain-kb-v1', 'inputs_sha256': {k: sha(getattr(a, k)) for k in ('adjudicated', 'check', 'norm', 'labels')},
           'counts': {'收下的步': len(steps), '定性步': sum(s['类型'] == '定性步' for s in steps), '推理步': sum(s['类型'] == '推理步' for s in steps),
                      '引擎可用（可操作且先天）': sum(1 for s in steps if s['可操作'] and s['适用'] == '先天'),
                      '引擎可用的推理步': sum(1 for s in steps if s['可操作'] and s['适用'] == '先天' and s['类型'] == '推理步'),
                      '结点': len(nodes), '按类型适用可操作': {f'{k[0]}·{k[1]}·{"可操作" if k[2] else "不可操作"}': n for k, n in sorted(c.items())}},
           'excluded': dict(excluded), 'problems': problems, 'nodes': nodes, 'steps': steps}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'counts': res['counts'], 'excluded': res['excluded'], 'problems': len(problems)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
