"""倪师推理链：收取子代理回复并审计 v1（依据《00_推理链方案_v1.md》四；由 21_倪师断法引擎_20261005/save_m4d_returns_v1.py 改来；不打印回复内容）。
按子任务描述认领：「<前缀><角色> Kxx」，例如「推理链试抽甲 K06」「推理链抽取乙 K21」「推理链裁定 K03」；
材料取 <材料目录>/Kxx，存为 <存档目录>/Kxx_<角色>.json（另存子任务记录与审计）。
审计：
- 工具调用只许读本批文件夹（读文件夹本身不算违规，另记次数）；
- 本批文件夹里除 instructions.txt、output_template.json 以外的每个文件，每一行都要被读取工具返回过（记 read_whole）；
- 只在子任务写完后存档：最后一条助手记录是文字、不是因输出上限截断，回复能解析为含 items 的 JSON；
- 最终回复若被截成几段，把最后一次工具调用之后的文字接起来再解析。
可重复运行：已存档的不重写。用法：python3 save_chain_returns_v1.py --prefix 推理链试抽 --packets <材料目录> --returns <存档目录> [--sub <子任务记录目录>]"""
import argparse, glob, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005'))
from save_m4_returns_v3 import SUB, LINE, sha, finished, result_text, parse


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prefix', required=True)
    ap.add_argument('--packets', required=True)
    ap.add_argument('--returns', required=True)
    ap.add_argument('--sub', default=SUB)
    a = ap.parse_args()
    os.makedirs(a.returns, exist_ok=True)
    pat = re.compile(re.escape(a.prefix) + r'(甲|乙|裁定|核查) (K\d\d)')
    status, out = {}, {}
    for meta in sorted(glob.glob(os.path.join(a.sub, 'agent-*.meta.json'))):
        m = json.load(open(meta, encoding='utf-8'))
        d = pat.fullmatch(m.get('description', ''))
        if not d:
            continue
        role, b = d.group(1), d.group(2)
        key = f'{b}_{role}'
        folder = os.path.join(a.packets, b)
        if not os.path.isdir(folder):
            continue
        if os.path.exists(os.path.join(a.returns, key + '.audit.json')):
            status[key] = 'done'; continue
        tp = meta.replace('.meta.json', '.jsonl')
        L = [json.loads(l) for l in open(tp, encoding='utf-8') if l.strip()]
        if not finished(L):
            status.setdefault(key, 'pending'); continue
        asst = [x for x in L if x.get('type') == 'assistant']
        parts = []
        for x in reversed(L):
            c = x.get('message', {}).get('content')
            if x.get('type') == 'user' and isinstance(c, list) and any(isinstance(y, dict) and y.get('type') == 'tool_result' for y in c):
                break
            if x.get('type') == 'assistant' and isinstance(c, list):
                t = ''.join(y.get('text', '') for y in c if y.get('type') == 'text')
                if t:
                    parts.append(t)
        final = ''.join(reversed(parts))
        jt = parse(final) if '"items"' in final else None
        if jt is None:
            status.setdefault(key, 'unparsable'); continue
        rf = os.path.realpath(folder)
        uses = {c['id']: (c.get('name'), c.get('input', {})) for x in asst for c in x['message'].get('content', []) if c.get('type') == 'tool_use'}
        viol = [{'tool': n, 'path': str(i.get('file_path', ''))[:200]} for n, i in uses.values()
                if n != 'Read' or not (os.path.realpath(i.get('file_path', '')).startswith(rf + os.sep) or os.path.realpath(i.get('file_path', '')) == rf)]
        folder_reads = sum(1 for n, i in uses.values() if n == 'Read' and os.path.realpath(i.get('file_path', '')) == rf)
        files = sorted(fn for fn in os.listdir(folder) if fn not in ('instructions.txt', 'output_template.json') and not fn.startswith('.'))
        seen = {fn: set() for fn in files}
        for x in L:
            if x.get('type') != 'user' or not isinstance(x.get('message', {}).get('content'), list):
                continue
            for c in x['message']['content']:
                if c.get('type') == 'tool_result' and c.get('tool_use_id') in uses:
                    n, i = uses[c['tool_use_id']]
                    fn = os.path.basename(i.get('file_path', ''))
                    if n == 'Read' and fn in seen and not c.get('is_error'):
                        seen[fn] |= {int(k) for k in LINE.findall(result_text(c))}
        total = {fn: sum(1 for _ in open(os.path.join(folder, fn), encoding='utf-8')) for fn in files}
        open(os.path.join(a.returns, key + '.json'), 'x', encoding='utf-8').write(jt)
        shutil.copyfile(tp, os.path.join(a.returns, key + '.transcript.jsonl'))
        cov = {fn: len({k for k in seen[fn] if 1 <= k <= total[fn]}) for fn in files}
        audit = {'agent_meta': m, 'model_in_transcript': sorted({x['message'].get('model') for x in asst}), 'kind': 'chain-' + role, 'batch': b,
                 'started': L[0].get('timestamp'), 'finished': L[-1].get('timestamp'), 'tool_calls': len(uses), 'violations': viol, 'folder_reads': folder_reads,
                 'files': files, 'lines': total, 'lines_returned': cov, 'read_whole': bool(files) and all(cov[f] == total[f] for f in files),
                 'final_reply_parts': len(parts), 'sha256': {'json': sha(os.path.join(a.returns, key + '.json')), 'transcript': sha(os.path.join(a.returns, key + '.transcript.jsonl'))}}
        open(os.path.join(a.returns, key + '.audit.json'), 'x', encoding='utf-8').write(json.dumps(audit, ensure_ascii=False, indent=1) + '\n')
        out[key] = {'violations': len(viol), 'read_whole': audit['read_whole']}
        status[key] = 'done'
    print(json.dumps({'saved_now': out, 'done_total': sum(v == 'done' for v in status.values()),
                      'not_done': sorted(f'{k}（{v}）' for k, v in status.items() if v != 'done')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
