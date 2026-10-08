"""倪师推理链：建逐步核查材料包 v1（依据《00_推理链方案_v1.md》七、1）。
输入：裁定核验后的合并文件（chain_adjudicate_validate_v1.py 的输出），只取 valid 的定稿步，按批分包。
每批写出：
- batch.json、context.txt：从抽取材料包逐字节复制，核对 SHA-256；
- steps.json：待核的步。每步只给核查需要的字段：编号、T、类型、宫、适用、条件或前提与附加条件、结论（层、判断、原话说法）、连接、原话摘录；
  不给整理者与裁定者的说明、来源、改动，免得影响核查者独立判断；
- instructions.txt：核查说明（写入型）；output_template.json：每步一项（编号、结论、理由）。
写出 <out>/Kxx/ 与 <out>/manifest.json；目录已存在就停。
用法：python3 build_chain_check_packets_v1.py --adjudicated <合并文件> --packets <抽取材料目录> --instructions <核查说明> --out <新目录>"""
import argparse, collections, hashlib, json, os, shutil

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
FIELDS_Q = ('类型', '宫', '适用', '条件')
FIELDS_R = ('类型', '宫', '适用', '前提', '附加条件')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('adjudicated', 'packets', 'instructions', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    adj = json.load(open(a.adjudicated, encoding='utf-8'))
    pman = {b['batch']: b for b in json.load(open(os.path.join(a.packets, 'manifest.json'), encoding='utf-8'))['batches']}
    by = collections.defaultdict(list)
    for s in adj['steps']:
        if s['valid']:
            by[s['batch']].append(s)
    os.makedirs(a.out)
    man = {'schema': 'chain-check-packets-v1', 'adjudicated_sha256': sha(a.adjudicated), 'instructions_sha256': sha(a.instructions), 'batches': []}
    for b in sorted(by):
        d = os.path.join(a.out, b)
        os.makedirs(d)
        for fn in ('batch.json', 'context.txt'):
            shutil.copyfile(os.path.join(a.packets, b, fn), os.path.join(d, fn))
            assert sha(os.path.join(d, fn)) == pman[b]['sha256'][fn]
        rows = []
        for s in by[b]:
            keep = FIELDS_Q if s['类型'] == '定性步' else FIELDS_R
            x = {'编号': s['step_id'], 'T': s['T'], **{k: s.get(k) for k in keep},
                 '结论': {k: (s.get('结论') or {}).get(k) for k in ('层', '判断', '原话说法')}}
            if s['类型'] == '推理步':
                x['连接'] = s.get('连接')
            x['原话摘录'] = s.get('原话摘录')
            rows.append(x)
        open(os.path.join(d, 'steps.json'), 'x', encoding='utf-8').write(json.dumps({'batch': b, '步': rows}, ensure_ascii=False, indent=1) + '\n')
        shutil.copyfile(a.instructions, os.path.join(d, 'instructions.txt'))
        tmpl = {'batch': b, 'items': [{'编号': r['编号'], '结论': '', '理由': ''} for r in rows]}
        open(os.path.join(d, 'output_template.json'), 'x', encoding='utf-8').write(json.dumps(tmpl, ensure_ascii=False, indent=1) + '\n')
        man['batches'].append({'batch': b, 'step_ids': [r['编号'] for r in rows], 'sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    open(os.path.join(a.out, 'manifest.json'), 'x', encoding='utf-8').write(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'batches': len(man['batches']), 'steps': sum(len(b['step_ids']) for b in man['batches'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
