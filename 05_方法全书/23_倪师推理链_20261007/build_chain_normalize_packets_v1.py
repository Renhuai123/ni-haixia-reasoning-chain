"""倪师推理链：建判断归一材料包 v1（依据《00_推理链方案_v1.md》五）。
输入：裁定核验后的合并文件（chain_adjudicate_validate_v1.py 的输出），只取 valid 的步。
把各步前提与结论里出现的判断名，按（层, 判断）原样去重，编号 L0001 起（按组、层、出现次数从多到少、判断名排序）；
每个判断名附出现次数，以及最多两例不同的原话说法与出处。
按层分六组，每组一个材料包（同组的层之间可以改层）：
  G1 定性；G2 长相、个性、行为；G3 路线、成败；G4 财、祖业田宅、福德；G5 婚姻、子女、父母、兄弟、朋友合伙；G6 健康、意外、官非、寿元、其他。
每组写出 labels.json、instructions.txt（归一说明原样复制）、output_template.json；另写 <out>/labels_all.json（全部判断名与编号）与 manifest.json。
目录已存在就停。用法：python3 build_chain_normalize_packets_v1.py --adjudicated <合并文件> --instructions <归一说明> --out <新目录>"""
import argparse, collections, hashlib, json, os, shutil

GROUPS = [('G1', ['定性']), ('G2', ['长相', '个性', '行为']), ('G3', ['路线', '成败']), ('G4', ['财', '祖业田宅', '福德']),
          ('G5', ['婚姻', '子女', '父母', '兄弟', '朋友合伙']), ('G6', ['健康', '意外', '官非', '寿元', '其他'])]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
EX = {'结点名': '刚强', '层': '个性', '成员': ['L0012', 'L0345'], '说明': '示意：两个判断名说的都是性情刚硬'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('adjudicated', 'instructions', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    adj = json.load(open(a.adjudicated, encoding='utf-8'))
    cnt, ex = collections.Counter(), collections.defaultdict(list)
    for s in adj['steps']:
        if not s['valid']:
            continue
        for p in [s['结论']] + list(s.get('前提') or []):
            k = (p['层'], p['判断'].strip())
            cnt[k] += 1
            e = {'原话说法': p.get('原话说法', ''), 'T': s['T']}
            if len(ex[k]) < 2 and all(x['原话说法'] != e['原话说法'] for x in ex[k]):
                ex[k].append(e)
    g_of = {lay: g for g, lays in GROUPS for lay in lays}
    keys = sorted(cnt, key=lambda k: ([g for g, _ in GROUPS].index(g_of[k[0]]), [l for _, ls in GROUPS for l in ls].index(k[0]), -cnt[k], k[1]))
    labels = [{'编号': f'L{i:04d}', '层': k[0], '判断': k[1], '次数': cnt[k], '例': ex[k]} for i, k in enumerate(keys, 1)]
    os.makedirs(a.out)
    open(os.path.join(a.out, 'labels_all.json'), 'x', encoding='utf-8').write(json.dumps({'labels': labels}, ensure_ascii=False, indent=1) + '\n')
    man = {'schema': 'chain-normalize-packets-v1', 'adjudicated_sha256': sha(a.adjudicated), 'instructions_sha256': sha(a.instructions), 'groups': []}
    for g, lays in GROUPS:
        ls = [l for l in labels if l['层'] in lays]
        d = os.path.join(a.out, g)
        os.makedirs(d)
        open(os.path.join(d, 'labels.json'), 'x', encoding='utf-8').write(json.dumps({'组': g, '本组的层': lays, '判断名': ls}, ensure_ascii=False, indent=1) + '\n')
        shutil.copyfile(a.instructions, os.path.join(d, 'instructions.txt'))
        open(os.path.join(d, 'output_template.json'), 'x', encoding='utf-8').write(
            json.dumps({'group': g, '结点': [], '改层': [], '结点示例': EX}, ensure_ascii=False, indent=1) + '\n')
        man['groups'].append({'group': g, 'layers': lays, 'n_labels': len(ls), 'label_ids': [l['编号'] for l in ls],
                              'sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    open(os.path.join(a.out, 'manifest.json'), 'x', encoding='utf-8').write(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'labels': len(labels), 'per_group': {g['group']: g['n_labels'] for g in man['groups']}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
