"""第十四稿内审：经 Claude API 批量接口，请 Claude Fable 5.1 的独立实例按不同角度审读正文与补充材料的 PDF。
每个角度一次独立调用；材料是两份 PDF（document 块）加审稿说明。调用、计价与账本沿用 23_倪师推理链_20261007/api_runner_v1.py（同一份账本、同一上限）。
用法：
  python3 paper_review_api_v1.py build  --run <运行目录> --main <正文.pdf> --supp <补充材料.pdf> --instr <审稿说明.md> --lenses <审稿角度.json>
  python3 paper_review_api_v1.py count  --run <运行目录>
  python3 paper_review_api_v1.py submit --run <运行目录> [--cap 185]
  python3 paper_review_api_v1.py status --run <运行目录>
  python3 paper_review_api_v1.py fetch  --run <运行目录> --out <交卷目录>
交卷：每个角度存 <名>.api.json（原样）、<名>.json（解析后的意见）、<名>.audit.json（审计：是否合格、用量、花费、材料指纹）。"""
import argparse, base64, datetime, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CH = os.path.join(os.path.dirname(HERE), '23_倪师推理链_20261007')
_spec = importlib.util.spec_from_file_location('api_runner_v1', os.path.join(CH, 'api_runner_v1.py'))
ar = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ar)

MAX_TOKENS = 64000
ASSUME_OUT = 20000
LEVELS = ('必须改', '建议改', '可不改')


def cmd_build(a):
    os.makedirs(a.run, exist_ok=False)
    instr = open(a.instr, encoding='utf-8').read()
    lenses = json.load(open(a.lenses, encoding='utf-8'))
    pdfs = [open(a.main, 'rb').read(), open(a.supp, 'rb').read()]
    docs = [{'type': 'document', 'source': {'type': 'base64', 'media_type': 'application/pdf', 'data': base64.b64encode(b).decode()}, 'title': t}
            for b, t in zip(pdfs, ('论文正文（第十四稿）', '补充材料（第十四稿）'))]
    mp = {'kind': 'reviewer', 'model': ar.MODEL, 'effort': ar.EFFORT, 'max_tokens': MAX_TOKENS,
          'materials_sha256': {'main': ar.sha(pdfs[0]), 'supp': ar.sha(pdfs[1]), 'instr': ar.sha(instr), 'lenses': ar.sha(open(a.lenses, 'rb').read())}, 'tasks': {}}
    with open(os.path.join(a.run, 'requests.jsonl'), 'x', encoding='utf-8') as f:
        for name, lens in lenses.items():
            text = instr.replace('{角度}', lens)
            assert '{角度}' not in text
            cid = f'review-v14-{name}'
            params = {'model': ar.MODEL, 'max_tokens': MAX_TOKENS, 'output_config': {'effort': ar.EFFORT},
                      'messages': [{'role': 'user', 'content': docs + [{'type': 'text', 'text': text}]}]}
            f.write(json.dumps({'custom_id': cid, 'params': params}, ensure_ascii=False) + '\n')
            mp['tasks'][cid] = {'name': name, 'prompt_sha256': ar.sha(text)}
    open(os.path.join(a.run, 'map.json'), 'x', encoding='utf-8').write(json.dumps(mp, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'请求数': len(lenses), '运行目录': a.run}, ensure_ascii=False))


def cmd_count(a):
    reqs = ar.load_requests(a.run)
    out, tot = {}, 0
    for r in reqs:
        p = r['params']
        n = ar.call('POST', ar.API + '/messages/count_tokens', {'model': p['model'], 'messages': p['messages']})['input_tokens']
        out[r['custom_id']] = n; tot += n
    est = tot * ar.PRICE['input'] / 1e6 + len(reqs) * ASSUME_OUT * ar.PRICE['output'] / 1e6
    json.dump({'input_tokens': out, '合计': tot, '估算花费美元（输出按每条 %d 估）' % ASSUME_OUT: round(est, 2)},
              open(os.path.join(a.run, 'count.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'请求数': len(reqs), '输入token合计': tot, '估算花费美元': round(est, 2)}, ensure_ascii=False))


def cmd_submit(a):
    reqs = ar.load_requests(a.run)
    assert not os.path.exists(os.path.join(a.run, 'batch.json')), '这一批已经提交过'
    cnt = json.load(open(os.path.join(a.run, 'count.json'), encoding='utf-8'))
    est = cnt['合计'] * ar.PRICE['input'] / 1e6 + len(reqs) * ASSUME_OUT * ar.PRICE['output'] / 1e6
    L = ar.ledger()
    pending = sum(r.get('估算美元', 0) for r in L['runs'].values() if r.get('状态') == '已提交')
    if ar.spent(L) + pending + est > a.cap:
        sys.exit(f'超过上限：已花 {ar.spent(L)}，在途估算 {round(pending, 2)}，本批估算 {round(est, 2)}，上限 {a.cap}。不提交。')
    b = ar.call('POST', ar.API + '/messages/batches', {'requests': reqs})
    rec = {'batch_id': b['id'], 'submitted_at': datetime.datetime.now().astimezone().isoformat(),
           'requests_sha256': ar.sha(open(os.path.join(a.run, 'requests.jsonl'), 'rb').read()), '估算美元': round(est, 2)}
    open(os.path.join(a.run, 'batch.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    L['runs'][os.path.relpath(a.run, CH)] = {'状态': '已提交', '估算美元': round(est, 2), 'batch_id': b['id']}
    json.dump(L, open(ar.LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'已提交': b['id'], '请求数': len(reqs), '本批估算美元': round(est, 2), '账本已花': ar.spent(L)}, ensure_ascii=False))


def check(obj):
    why = []
    for k in ('角度', '总体判断', '分数', '写得好的地方', '问题'):
        if k not in obj:
            why.append(f'缺 {k}')
    if not isinstance(obj.get('分数'), int) or not 0 <= obj.get('分数', -1) <= 100:
        why.append('分数不是 0–100 的整数')
    for q in obj.get('问题', []):
        miss = [k for k in ('级别', '位置', '原文', '问题', '改法') if not str(q.get(k, '')).strip()]
        if miss:
            why.append(f"第 {q.get('编号')} 条缺 {'、'.join(miss)}")
        if q.get('级别') not in LEVELS:
            why.append(f"第 {q.get('编号')} 条级别不合：{q.get('级别')}")
    return why


def cmd_fetch(a):
    b = json.load(open(os.path.join(a.run, 'batch.json'), encoding='utf-8'))
    mp = json.load(open(os.path.join(a.run, 'map.json'), encoding='utf-8'))
    s = ar.call('GET', f"{ar.API}/messages/batches/{b['batch_id']}")
    if s['processing_status'] != 'ended':
        sys.exit(f"批次还没结束：{s['processing_status']} {json.dumps(s['request_counts'])}")
    raw = ar.call('GET', s['results_url'], raw=True)
    rawp = os.path.join(a.run, 'results_raw.jsonl')
    if not os.path.exists(rawp):
        open(rawp, 'xb').write(raw)
    os.makedirs(a.out, exist_ok=True)
    total, ok, bad = 0.0, [], []
    for line in raw.decode('utf-8').splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        t = mp['tasks'][r['custom_id']]
        name = t['name']
        if os.path.exists(os.path.join(a.out, name + '.audit.json')):
            continue
        res = r['result']
        why, obj, usage, msg = [], None, {}, {}
        if res['type'] != 'succeeded':
            why.append(f"结果类型 {res['type']}")
        else:
            msg = res['message']
            usage = msg.get('usage', {})
            total += ar.cost(usage)
            if msg.get('stop_reason') != 'end_turn':
                why.append(f"stop_reason={msg.get('stop_reason')}")
            text = ''.join(c.get('text', '') for c in msg.get('content', []) if c.get('type') == 'text')
            try:
                obj = ar.parse_json(text)
                why += check(obj)
            except Exception:
                why.append('回复不是合法 JSON')
        open(os.path.join(a.out, name + '.api.json'), 'x', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=1) + '\n')
        if obj is not None:
            open(os.path.join(a.out, name + '.json'), 'x', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1) + '\n')
        audit = {'name': name, 'ok': not why, 'why_not_ok': why, 'custom_id': r['custom_id'], 'batch_id': b['batch_id'], 'model': msg.get('model'),
                 'message_id': msg.get('id'), 'stop_reason': msg.get('stop_reason'), 'usage': usage, '花费美元': round(ar.cost(usage), 4),
                 'prompt_sha256': t['prompt_sha256'], 'materials_sha256': mp['materials_sha256']}
        open(os.path.join(a.out, name + '.audit.json'), 'x', encoding='utf-8').write(json.dumps(audit, ensure_ascii=False, indent=1) + '\n')
        (ok if not why else bad).append(name if not why else f"{name}（{'、'.join(why)}）")
    L = ar.ledger()
    rk = os.path.relpath(a.run, CH)
    L['runs'][rk] = {'状态': '已取回', '花费美元': round(total + L['runs'].get(rk, {}).get('花费美元', 0), 4), 'batch_id': b['batch_id']}
    json.dump(L, open(ar.LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'合格': len(ok), '不合格': bad, '本批花费美元': round(total, 2), '账本已花美元': ar.spent(L)}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('build'); p.add_argument('--run', required=True); p.add_argument('--main', required=True); p.add_argument('--supp', required=True)
    p.add_argument('--instr', required=True); p.add_argument('--lenses', required=True)
    for c in ('count', 'status'):
        sp.add_parser(c).add_argument('--run', required=True)
    p = sp.add_parser('submit'); p.add_argument('--run', required=True); p.add_argument('--cap', type=float, default=185)
    p = sp.add_parser('fetch'); p.add_argument('--run', required=True); p.add_argument('--out', required=True)
    a = ap.parse_args()
    if a.cmd == 'status':
        b = json.load(open(os.path.join(a.run, 'batch.json'), encoding='utf-8'))
        s = ar.call('GET', f"{ar.API}/messages/batches/{b['batch_id']}")
        print(json.dumps({'状态': s['processing_status'], '计数': s['request_counts']}, ensure_ascii=False)); return
    {'build': cmd_build, 'count': cmd_count, 'submit': cmd_submit, 'fetch': cmd_fetch}[a.cmd](a)


if __name__ == '__main__':
    main()
