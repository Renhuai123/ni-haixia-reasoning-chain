"""三项补充研究（《00h_三项补充研究方案_v2.md》）通用的收卷与审计 v4。只审计、只存档，不读任何答案键，不打印交卷内容。
由 save_chain_returns_v3.py 改来，差别：
1. 认领规则由参数给：子任务描述须完全匹配 --pattern（正则，含命名组 id，可含 role、rerun），交卷名 = id[_role][_重跑n]；
2. 不论合格与否都写审计文件，审计里给出 ok（合格）与不合格的原因；合格的才存交卷 JSON；
   合格 = 子任务已写完、没有越权的工具调用、本文件夹里除 instructions.txt、output_template.json 以外每个文件每一行都读到、
          交卷文件存在且能解析为含 --key 的 JSON、与子任务记录里最后一次写入调用的内容解析后完全相同；
3. 只认写入型交卷（opus-high-writer）。
重跑（方案「共同规定」一）：不合格的由派活人另开新实例重跑，描述末尾加「 重跑1」「 重跑2」；每题最多重跑 2 次。本程序只记录，不判断要不要重跑。
用法：python3 save_returns_v4.py --pattern '认本人链 (?P<id>M\\d\\d)(?: 重跑(?P<rerun>[12]))?' --packets <材料目录> --returns <存档目录> --drop <交卷目录> --key 答案 [--sub <子任务记录目录>]"""
import argparse, glob, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005'))
from save_m4_returns_v3 import SUB, LINE, sha, finished, result_text


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pattern', required=True)
    ap.add_argument('--packets', required=True)
    ap.add_argument('--returns', required=True)
    ap.add_argument('--drop', required=True)
    ap.add_argument('--key', required=True)
    ap.add_argument('--sub', default=SUB)
    a = ap.parse_args()
    os.makedirs(a.returns, exist_ok=True)
    pat = re.compile(a.pattern)
    status, out = {}, {}
    for meta in sorted(glob.glob(os.path.join(a.sub, 'agent-*.meta.json'))):
        m = json.load(open(meta, encoding='utf-8'))
        d = pat.fullmatch(m.get('description', ''))
        if not d:
            continue
        g = d.groupdict()
        b = g['id']
        name = b + (f"_{g['role']}" if g.get('role') else '') + (f"_重跑{g['rerun']}" if g.get('rerun') else '')
        folder = os.path.join(a.packets, b)
        if not os.path.isdir(folder):
            continue
        if os.path.exists(os.path.join(a.returns, name + '.audit.json')):
            status[name] = 'done'; continue
        tp = meta.replace('.meta.json', '.jsonl')
        L = [json.loads(l) for l in open(tp, encoding='utf-8') if l.strip()]
        asst = [x for x in L if x.get('type') == 'assistant']
        uses = {c['id']: (c.get('name'), c.get('input', {})) for x in asst for c in x['message'].get('content', []) if c.get('type') == 'tool_use'}
        ins = [os.path.realpath(i.get('file_path', '')) for n, i in uses.values() if n == 'Read' and str(i.get('file_path', '')).endswith('instructions.txt')]
        if ins and os.path.dirname(ins[0]) != os.path.realpath(folder):
            status.setdefault(name, 'other-folder'); continue
        if not finished(L):
            status.setdefault(name, 'pending'); continue
        drop_path = os.path.realpath(os.path.join(a.drop, name + '.json'))
        writes = [i for n, i in uses.values() if n == 'Write']
        rf = os.path.realpath(folder)

        def ok_use(n, i):
            p = os.path.realpath(i.get('file_path', ''))
            if n == 'Read':
                return p.startswith(rf + os.sep) or p == rf
            return n == 'Write' and p == drop_path
        viol = [{'tool': n, 'path': str(i.get('file_path', ''))[:200]} for n, i in uses.values() if not ok_use(n, i)]
        jt, why = None, []
        if not os.path.exists(drop_path):
            why.append('没有交卷文件')
        else:
            body = open(drop_path, encoding='utf-8').read()
            last = [i for i in writes if os.path.realpath(i.get('file_path', '')) == drop_path]
            try:
                obj = json.loads(body)
                if a.key not in obj:
                    why.append(f'交卷里没有「{a.key}」')
                elif not last or json.loads(last[-1].get('content', '')) != obj:
                    why.append('交卷文件与最后一次写入不同')
                else:
                    jt = body
            except Exception:
                why.append('交卷不是合法 JSON')
        files = sorted(fn for fn in os.listdir(folder) if fn not in ('instructions.txt', 'output_template.json') and not fn.startswith('.'))
        seen = {fn: set() for fn in files}
        for x in L:
            if x.get('type') != 'user' or not isinstance(x.get('message', {}).get('content'), list):
                continue
            for c in x['message']['content']:
                if c.get('type') == 'tool_result' and c.get('tool_use_id') in uses:
                    n, i = uses[c['tool_use_id']]
                    fn = os.path.basename(i.get('file_path', ''))
                    if n == 'Read' and fn in seen and not c.get('is_error') and os.path.realpath(i.get('file_path', '')).startswith(rf + os.sep):
                        seen[fn] |= {int(k) for k in LINE.findall(result_text(c))}
        total = {fn: sum(1 for _ in open(os.path.join(folder, fn), encoding='utf-8')) for fn in files}
        cov = {fn: len({k for k in seen[fn] if 1 <= k <= total[fn]}) for fn in files}
        read_whole = bool(files) and all(cov[f] == total[f] for f in files)
        if viol:
            why.append('越权的工具调用')
        if not read_whole:
            why.append('材料没有每行读到')
        final = ''.join(y.get('text', '') for y in (asst[-1]['message'].get('content') or []) if y.get('type') == 'text') if asst else ''
        if jt is not None and not why:
            open(os.path.join(a.returns, name + '.json'), 'x', encoding='utf-8').write(jt)
        shutil.copyfile(tp, os.path.join(a.returns, name + '.transcript.jsonl'))
        audit = {'agent_meta': m, 'model_in_transcript': sorted({x['message'].get('model') for x in asst}), 'name': name, 'id': b, 'role': g.get('role'),
                 'rerun': int(g['rerun']) if g.get('rerun') else 0, 'ok': not why, 'why_not_ok': why, 'final_reply': final[:20],
                 'started': L[0].get('timestamp'), 'finished': L[-1].get('timestamp'), 'tool_calls': len(uses), 'writes': len(writes), 'violations': viol,
                 'files': files, 'lines': total, 'lines_returned': cov, 'read_whole': read_whole,
                 'sha256': {'json': sha(os.path.join(a.returns, name + '.json')) if not why else None, 'transcript': sha(os.path.join(a.returns, name + '.transcript.jsonl'))}}
        open(os.path.join(a.returns, name + '.audit.json'), 'x', encoding='utf-8').write(json.dumps(audit, ensure_ascii=False, indent=1) + '\n')
        out[name] = 'ok' if not why else '不合格：' + '、'.join(why)
        status[name] = 'done'
    print(json.dumps({'saved_now': out, 'done_total': sum(v == 'done' for v in status.values()),
                      'not_done': sorted(f'{k}（{v}）' for k, v in status.items() if v != 'done')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
