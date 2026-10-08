"""倪师推理链：建裁定材料包 v2（依据《00_推理链方案_v1.md》四、3）。与 v1 只差一处：加 --append，可以往已有的裁定材料目录里追加新的批（已有的批不动、不重建），
清单 manifest.json 随之增补（边抽边裁用）。不加 --append 时与 v1 相同（目录已存在就停）。以下为 v1 原说明。
每批要求甲、乙两份抽取都已存档且审计合格（没有违规、每行都读到）；不合格的批不建包，列在 skipped 里。
每批写出：
- batch.json、context.txt：从抽取材料包逐字节复制，核对 SHA-256；
- extract_instructions.txt：抽取材料包里的 instructions.txt 原样复制（甲、乙所用的说明）；
- extractions.json：甲、乙的结果按条目排好，每一步加编号「T号-甲j」「T号-乙j」（j 从 1 起，按原次序），步的内容原样不改；
- instructions.txt：裁定说明；output_template.json：本批每条一项（T、步、不收、方法），另附定稿步与不收的写法示例。
写出 <out>/Kxx/ 与 <out>/manifest.json；目录已存在就停。
用法：python3 build_chain_adjudicate_packets_v2.py --packets <抽取材料目录> --returns <抽取存档目录> --instructions <裁定说明> --out <新目录> [--batches K06,K10]"""
import argparse, hashlib, json, os, shutil

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
EX_STEP = {'类型': '推理步', '宫': '命宫', '适用': '先天', '前提': [{'层': '定性', '判断': '将星', '原话说法': '将星'}], '附加条件': [],
           '结论': {'层': '路线', '判断': '适合当武官', '原话说法': '适合当武官', '方向': '中', '强度': '倾向'}, '连接': '所以',
           '原话摘录': '甲星坐命的人是将星，所以这种人适合当武官', '命例特指': False, '可操作': True, '说明': '示意，不是原话',
           '来源': ['T0-甲2', 'T0-乙1'], '改动': '判断名统一为「适合当武官」'}
EX_DROP = {'编号': 'T0-乙2', '理由': '示意：原话只是并列几个特征，没有推导'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('packets', 'returns', 'instructions', 'out'):
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--batches')
    ap.add_argument('--append', action='store_true')
    a = ap.parse_args()
    pman = json.load(open(os.path.join(a.packets, 'manifest.json'), encoding='utf-8'))
    want = a.batches.split(',') if a.batches else [b['batch'] for b in pman['batches']]
    if a.append and os.path.exists(a.out):
        man = json.load(open(os.path.join(a.out, 'manifest.json'), encoding='utf-8'))
        assert man['instructions_sha256'] == sha(a.instructions), '裁定说明与已有材料包不同'
        man['skipped'] = []
    else:
        assert not os.path.exists(a.out)
        os.makedirs(a.out)
        man = {'schema': 'chain-adjudicate-packets-v1', 'instructions_sha256': sha(a.instructions), 'batches': [], 'skipped': []}
    have = {b['batch'] for b in man['batches']}
    for pb in pman['batches']:
        b = pb['batch']
        if b not in want or b in have:
            continue
        ok, why = True, []
        for role in '甲乙':
            au = os.path.join(a.returns, f'{b}_{role}.audit.json')
            if not os.path.exists(au):
                ok = False; why.append(f'{role}没有存档'); continue
            ad = json.load(open(au, encoding='utf-8'))
            if ad['violations'] or not ad['read_whole']:
                ok = False; why.append(f'{role}审计不合格')
        if not ok:
            man['skipped'].append({'batch': b, 'why': why}); continue
        d = os.path.join(a.out, b)
        os.makedirs(d)
        for fn in ('batch.json', 'context.txt'):
            shutil.copyfile(os.path.join(a.packets, b, fn), os.path.join(d, fn))
            assert sha(os.path.join(d, fn)) == pb['sha256'][fn]
        shutil.copyfile(os.path.join(a.packets, b, 'instructions.txt'), os.path.join(d, 'extract_instructions.txt'))
        assert sha(os.path.join(d, 'extract_instructions.txt')) == pb['sha256']['instructions.txt']
        ret = {role: {it['T']: it for it in json.load(open(os.path.join(a.returns, f'{b}_{role}.json'), encoding='utf-8'))['items']} for role in '甲乙'}
        rows = []
        for T in pb['items']:
            row = {'T': T}
            for role in '甲乙':
                it = ret[role].get(T) or {'步': [], '方法': ''}
                row[role] = {'步': [dict({'编号': f'{T}-{role}{j}'}, **s) for j, s in enumerate(it.get('步') or [], 1)], '方法': it.get('方法', '')}
            rows.append(row)
        open(os.path.join(d, 'extractions.json'), 'x', encoding='utf-8').write(json.dumps({'batch': b, '条目': rows}, ensure_ascii=False, indent=1) + '\n')
        shutil.copyfile(a.instructions, os.path.join(d, 'instructions.txt'))
        tmpl = {'batch': b, 'items': [{'T': T, '步': [], '不收': [], '方法': ''} for T in pb['items']], '定稿步示例': EX_STEP, '不收示例': EX_DROP}
        open(os.path.join(d, 'output_template.json'), 'x', encoding='utf-8').write(json.dumps(tmpl, ensure_ascii=False, indent=1) + '\n')
        ids = [s['编号'] for r in rows for role in '甲乙' for s in r[role]['步']]
        man['batches'].append({'batch': b, 'items': pb['items'], 'step_ids': ids, 'returns_sha256': {role: sha(os.path.join(a.returns, f'{b}_{role}.json')) for role in '甲乙'},
                               'sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    man['batches'].sort(key=lambda b: b['batch'])
    open(os.path.join(a.out, 'manifest.json'), 'w', encoding='utf-8').write(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'batches': len(man['batches']), 'skipped': man['skipped'], 'steps': sum(len(b['step_ids']) for b in man['batches'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
