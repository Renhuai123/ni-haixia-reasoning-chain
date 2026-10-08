"""倪师推理链：建判断归一的裁定材料包 v1（依据《00_推理链方案_v1.md》五、3）。
每组要求甲、乙两份归类都已存档且审计合格（没有违规、每行都读到）；不合格的组不建包，列在 skipped 里。
每组写出：labels.json（从归一材料包逐字节复制，核对 SHA-256）、normalize_instructions.txt（甲乙所用的归类说明，原样复制）、
coder_甲.json、coder_乙.json（两人的归类结果，原样复制）、instructions.txt（裁定说明）、output_template.json。
写出 <out>/Gx/ 与 <out>/manifest.json；目录已存在就停。
用法：python3 build_chain_normalize_adjudicate_packets_v1.py --norm-packets <归一材料目录> --norm-returns <归一存档目录> --instructions <裁定说明> --out <新目录>"""
import argparse, hashlib, json, os, shutil

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
EX = {'结点名': '刚强', '层': '个性', '成员': ['L0012', 'L0345'], '说明': '示意：甲乙一致'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('norm-packets', 'norm-returns', 'instructions', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    nman = json.load(open(os.path.join(a.norm_packets, 'manifest.json'), encoding='utf-8'))
    os.makedirs(a.out)
    man = {'schema': 'chain-normalize-adjudicate-packets-v1', 'instructions_sha256': sha(a.instructions), 'groups': [], 'skipped': []}
    for g in nman['groups']:
        G = g['group']
        why = []
        for role in '甲乙':
            au = os.path.join(a.norm_returns, f'{G}_{role}.audit.json')
            if not os.path.exists(au):
                why.append(f'{role}没有存档'); continue
            ad = json.load(open(au, encoding='utf-8'))
            if ad['violations'] or not ad['read_whole']:
                why.append(f'{role}审计不合格')
        if why:
            man['skipped'].append({'group': G, 'why': why}); continue
        d = os.path.join(a.out, G)
        os.makedirs(d)
        shutil.copyfile(os.path.join(a.norm_packets, G, 'labels.json'), os.path.join(d, 'labels.json'))
        assert sha(os.path.join(d, 'labels.json')) == g['sha256']['labels.json']
        shutil.copyfile(os.path.join(a.norm_packets, G, 'instructions.txt'), os.path.join(d, 'normalize_instructions.txt'))
        for role in '甲乙':
            shutil.copyfile(os.path.join(a.norm_returns, f'{G}_{role}.json'), os.path.join(d, f'coder_{role}.json'))
        shutil.copyfile(a.instructions, os.path.join(d, 'instructions.txt'))
        open(os.path.join(d, 'output_template.json'), 'x', encoding='utf-8').write(
            json.dumps({'group': G, '结点': [], '改层': [], '结点示例': EX}, ensure_ascii=False, indent=1) + '\n')
        man['groups'].append({'group': G, 'label_ids': g['label_ids'], 'layers': g['layers'], 'sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    open(os.path.join(a.out, 'manifest.json'), 'x', encoding='utf-8').write(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'groups': len(man['groups']), 'skipped': man['skipped']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
