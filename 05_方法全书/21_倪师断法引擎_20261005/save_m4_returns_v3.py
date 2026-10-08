"""收取 M4 判包的回复并审计 v3（原样存档、另存子任务记录；不打印回复内容）。
v3 与 v2 只差一处：读取工具读本包文件夹本身（目录）不算违规，另记次数 folder_reads（见《11a_M4存档审计读目录不算违规_v1.md》）。
v2 与 v1 只差读全核对：判包改为分文件（m4_build_v2.py），逐个核对包内除 instructions.txt 以外的每个 .txt 文件是否每一行都被读取工具返回过；另可指定子任务记录目录（测试用）。
- 主检验：子任务描述「配对盲审 M01 甲」「配对盲审 M01 乙」，材料 <m4目录>/judge_packets/Mxx，存为 <m4目录>/judge_returns/Mxx_甲.json 等；
- 次要检验：子任务描述「陈述判定 S01」，材料 <m4目录>/stmt_packets/Sxx，存为 <m4目录>/stmt_returns/Sxx.json。
审计：工具调用只许读本包文件夹；按读取工具实际返回的行号，核对包内每个题目文本文件（题NN_*.txt 或 组NN_*.txt）是否读完；
只在子任务写完后才存档（最后一条助手记录是文字、不是因输出上限截断，回复能解析）；最终回复若被截成几段，把最后一次工具调用之后的文字接起来再解析。
可重复运行：已存档的不重写。用法：python3 save_m4_returns_v3.py <m4目录> [子任务记录目录]"""
import glob, hashlib, json, os, re, shutil, sys

SUB = os.path.expanduser('~/.claude/projects/-Users-<用户名>-Downloads/6fdaa369-bf21-4599-80fb-0d72265e8b2c/subagents')
LINE = re.compile(r'^\s*(\d+)\t', re.M)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def finished(L):
    a = [x for x in L if x.get('type') == 'assistant']
    if not a:
        return False
    last = a[-1]['message']
    types = [c.get('type') for c in last.get('content') or [] if isinstance(c, dict)]
    return last.get('stop_reason') != 'max_tokens' and bool(types) and types[-1] == 'text'


def result_text(c):
    x = c.get('content')
    if isinstance(x, list):
        return ''.join(y.get('text', '') for y in x if isinstance(y, dict))
    return x if isinstance(x, str) else ''


def parse(final):
    for t in (final, (re.fullmatch(r'\s*```(?:json)?[ \t]*\n(.*)\n```\s*', final, re.S) or [None, None])[1]):
        if t:
            try:
                json.loads(t); return t
            except Exception:
                pass
    return None


def main():
    root = sys.argv[1]
    sub = sys.argv[2] if len(sys.argv) > 2 else SUB
    done, pending, out = [], [], {}
    for meta in sorted(glob.glob(os.path.join(sub, 'agent-*.meta.json'))):
        m = json.load(open(meta, encoding='utf-8'))
        d1 = re.fullmatch(r'配对盲审 (M\d\d) ([甲乙])', m.get('description', ''))
        d2 = re.fullmatch(r'陈述判定 (S\d\d)', m.get('description', ''))
        if d1:
            pack, name, folder, corpus, kind = d1.group(1), f'{d1.group(1)}_{d1.group(2)}', os.path.join(root, 'judge_packets', d1.group(1)), None, 'judge'
            outdir = os.path.join(root, 'judge_returns'); want = '"答案"'
        elif d2:
            pack, name, folder, corpus, kind = d2.group(1), d2.group(1), os.path.join(root, 'stmt_packets', d2.group(1)), None, 'stmt'
            outdir = os.path.join(root, 'stmt_returns'); want = '"判定"'
        else:
            continue
        if not os.path.isdir(folder):
            continue
        os.makedirs(outdir, exist_ok=True)
        if os.path.exists(os.path.join(outdir, name + '.audit.json')):
            done.append(name); continue
        tp = meta.replace('.meta.json', '.jsonl')
        L = [json.loads(l) for l in open(tp, encoding='utf-8') if l.strip()]
        if not finished(L):
            pending.append(name); continue
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
        jt = parse(final) if want in final else None
        if jt is None:
            pending.append(name + '（回复解析不了，未存档）'); continue
        rf = os.path.realpath(folder)
        uses = {c['id']: (c.get('name'), c.get('input', {})) for x in asst for c in x['message'].get('content', []) if c.get('type') == 'tool_use'}
        viol = [{'tool': n, 'path': str(i.get('file_path', ''))[:200]} for n, i in uses.values()
                if n != 'Read' or not (os.path.realpath(i.get('file_path', '')).startswith(rf + os.sep) or os.path.realpath(i.get('file_path', '')) == rf)]
        folder_reads = sum(1 for n, i in uses.values() if n == 'Read' and os.path.realpath(i.get('file_path', '')) == rf)
        files = sorted(fn for fn in os.listdir(folder) if fn.endswith('.txt') and fn != 'instructions.txt')
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
        open(os.path.join(outdir, name + '.json'), 'x', encoding='utf-8').write(jt)
        shutil.copyfile(tp, os.path.join(outdir, name + '.transcript.jsonl'))
        cov = {fn: len({k for k in seen[fn] if 1 <= k <= total[fn]}) for fn in files}
        audit = {'agent_meta': m, 'model_in_transcript': sorted({x['message'].get('model') for x in asst}), 'kind': kind, 'pack': pack,
                 'started': L[0].get('timestamp'), 'finished': L[-1].get('timestamp'), 'tool_calls': len(uses), 'violations': viol, 'folder_reads': folder_reads,
                 'corpus': files, 'corpus_lines': total, 'corpus_lines_returned': cov, 'read_whole': bool(files) and all(cov[f] == total[f] for f in files), 'final_reply_parts': len(parts),
                 'sha256': {'json': sha(os.path.join(outdir, name + '.json')), 'transcript': sha(os.path.join(outdir, name + '.transcript.jsonl'))}}
        open(os.path.join(outdir, name + '.audit.json'), 'x', encoding='utf-8').write(json.dumps(audit, ensure_ascii=False, indent=1) + '\n')
        out[name] = {'violations': len(viol), 'read_whole': audit['read_whole']}
    print(json.dumps({'saved_now': out, 'done_total': len(done), 'pending': sorted(set(pending))}, ensure_ascii=False))


if __name__ == '__main__':
    main()
