"""倪师推理链：逐步核查结果的核验与汇总 v1（依据《00_推理链方案_v1.md》七、1；只核验、计数，不改内容）。
逐批核对 <核查存档目录>/Kxx_核查.json：每个待核步号都有且只有一项；「结论」只许「成立」「不成立」；理由不为空。
汇总：成立与不成立的步数与比例（按步的类型分开）；不成立的步逐条列出（步号、T、类型、结论判断、核查理由）。
有任何不合格（缺项、重项、结论取值不对）：照样写出，该批列入 problems；没有有效核查结论的步，按方案不进引擎。
写出 <out>；文件已存在就停。用法：python3 chain_check_merge_v1.py --check-packets <核查材料目录> --check-returns <核查存档目录> --adjudicated <合并文件> --out <新文件>"""
import argparse, collections, hashlib, json, os

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('check-packets', 'check-returns', 'adjudicated', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    man = json.load(open(os.path.join(a.check_packets, 'manifest.json'), encoding='utf-8'))
    steps = {s['step_id']: s for s in json.load(open(a.adjudicated, encoding='utf-8'))['steps'] if s['valid']}
    verdict, problems, inputs = {}, [], {}
    for b in man['batches']:
        p = os.path.join(a.check_returns, f"{b['batch']}_核查.json")
        if not os.path.exists(p):
            problems.append({'batch': b['batch'], 'problem': '没有核查结果'}); continue
        inputs[b['batch']] = sha(p)
        items = json.load(open(p, encoding='utf-8')).get('items', [])
        got = collections.Counter(i.get('编号') for i in items)
        want = set(b['step_ids'])
        bad = {'缺项': sorted(want - set(got)), '多出': sorted(set(got) - want), '重项': sorted(k for k, n in got.items() if n > 1)}
        if any(bad.values()):
            problems.append({'batch': b['batch'], 'problem': '步号不一一对应', **bad})
        for i in items:
            k = i.get('编号')
            if k not in want or got[k] > 1:
                continue
            if i.get('结论') not in ('成立', '不成立') or not str(i.get('理由', '')).strip():
                problems.append({'step_id': k, 'problem': '结论取值不对或没写理由'}); continue
            verdict[k] = {'结论': i['结论'], '理由': i['理由']}
    c = collections.Counter((steps[k]['类型'], v['结论']) for k, v in verdict.items() if k in steps)
    res = {'schema': 'chain-check-merged-v1', 'inputs_sha256': inputs,
           'counts': {'待核': sum(len(b['step_ids']) for b in man['batches']), '有有效结论': len(verdict),
                      '定性步成立': c[('定性步', '成立')], '定性步不成立': c[('定性步', '不成立')],
                      '推理步成立': c[('推理步', '成立')], '推理步不成立': c[('推理步', '不成立')], 'problems': len(problems)},
           'verdicts': verdict,
           '不成立': [{'step_id': k, 'T': steps[k]['T'], '类型': steps[k]['类型'], '结论判断': (steps[k].get('结论') or {}).get('判断'), '理由': v['理由']}
                    for k, v in sorted(verdict.items()) if v['结论'] == '不成立' and k in steps],
           'problems': problems}
    for t in ('定性步', '推理步'):
        n = c[(t, '成立')] + c[(t, '不成立')]
        res['counts'][f'{t}成立比例'] = round(c[(t, '成立')] / n, 4) if n else None
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(res['counts'], ensure_ascii=False))


if __name__ == '__main__':
    main()
