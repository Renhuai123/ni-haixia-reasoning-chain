"""三项深化研究（《00l_三项深化方案》）的批量调用程序 v1：用 Claude API 的批量接口（Message Batches）派审者、归类者、裁定者。
每个任务 = 一个材料文件夹（审者包、归类批、裁定包），一次独立的 API 调用，不共享任何上下文。
提示的拼法（固定，写进登记）：
  该文件夹的 instructions.txt 全文（任务表给了「instructions」的，用那份说明代替）
  + 一行分隔线与说明「以下是全部材料。每份材料以单独一行【文件】文件名开头……」
  + 其余文件逐个附上，次序为：codebook、陈述、units、sentences、论断（A–D）、归类甲、归类乙、切分甲、切分乙、待裁定、其他（各按文件名升序），
    output_template.json 放最后；
    每个文件前写一行「【文件】文件名」。
  材料全文都在提示里，所以「每个文件每行都读到」由构造保证，不再另行审计。
请求参数：model = claude-fable-5-1；output_config.effort = high；max_tokens 按任务类型（judge 48000、coder 100000、adjudicator 64000）；
  不设系统提示、不用工具、不用提示缓存；思考为该模型固定的自适应思考。
审计（只看格式，不读任何答案键）：结果类型为 succeeded、stop_reason 为 end_turn、回复能解析为 JSON（允许外面包一层 ```json 代码块）、
  且合乎任务类型：judge 有非空的「答案」；coder 的「归类」编号与 units.json 完全相同、各项取值合规（问A、问B、C1–C5、问D 只许说明规定的值，
  该空的可空）；adjudicator 的「裁定」（编号，项）与待裁定.json 完全相同、取值合规；segmenter 的「切分」编号与 sentences.json 相同、
  判断原文都能在句中找到；seg_adjudicator 的「裁定」编号与待裁定.json 相同、判断原文都能在句中找到。
  合格的写 <名>.json；不论合格与否都写 <名>.audit.json（含 ok、why_not_ok、用量、模型、消息 id、提示的 SHA-256）与 <名>.api.json（原样结果）。
  不合格的另发新请求重跑，名字加「_重跑1」「_重跑2」（custom_id 加 _r1、_r2），提示与参数逐字节相同；每个任务最多重跑 2 次。
花费：按批量接口价格（claude-fable-5-1：输入 5 美元／百万 token、输出 25 美元／百万 token；2026-10-08 核于官方定价页）由每条结果的 usage 计算，
  记进账本 api_runs/ledger.json；提交前估算本批花费（输入 token 用免费的计数接口实数，输出按 --assume-output 估），
  账本已花 + 本批估算超过 --cap 就不提交。
密钥：只从 ~/.config/anthropic/api_key 读（由研究发起人自己存入），程序不显示、不打印、不写进任何文件。
子命令：
  build  --tasks <任务表.json> --run <运行目录>：按任务表拼出请求，写 <运行目录>/requests.jsonl 与 map.json（custom_id ↔ 名字、材料目录、提示 SHA-256）；目录已存在就停。
  count  --run …：用计数接口数每条请求的输入 token，写 <运行目录>/count.json，打印合计与估算花费。
  submit --run … --cap 185 [--assume-output N]：检查上限后提交，写 <运行目录>/batch.json。
  status --run …：查批次进度。
  fetch  --run … --out <存档目录>：批次结束后取回结果，逐条审计、存档，更新账本；打印合格与不合格的名字。
  rerun  --run <原运行目录> --new <新运行目录> --out <存档目录>：把存档里不合格且未用尽重跑次数的任务，拼成新一批请求（名字加「_重跑n」）。
任务表格式：{"kind": "judge"|"coder"|"adjudicator"|"segmenter"|"seg_adjudicator", "tasks": [{"name": "J001", "id": "J001", "role": null, "dir": "<材料目录>",
  "instructions": "<可选：用这份说明代替材料目录里的 instructions.txt>"} …]}；
  custom_id 由名字转成：中文「甲」「乙」→「A」「B」，「_重跑n」→「_rn」；裁定包的名字就是批名，custom_id 加「_ADJ」。"""
import argparse, datetime, hashlib, http.client, json, os, re, sys, time, urllib.request, urllib.error

MODEL = 'claude-fable-5-1'
EFFORT = 'high'
MAX_TOKENS = {'judge': 48000, 'coder': 100000, 'adjudicator': 64000, 'segmenter': 64000, 'seg_adjudicator': 48000}
ASSUME_OUT = {'judge': 8000, 'coder': 30000, 'adjudicator': 15000, 'segmenter': 15000, 'seg_adjudicator': 8000}
PRICE = {'input': 5.0, 'output': 25.0, 'cache_write': 6.25, 'cache_read': 0.125}   # 美元／百万 token，批量接口，claude-fable-5-1
API = 'https://api.anthropic.com/v1'
KEY_FILE = os.path.expanduser('~/.config/anthropic/api_key')
HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'api_runs', 'ledger.json')
SEP = '\n\n==========\n以下是全部材料。每份材料以单独一行「【文件】文件名」开头，到下一个「【文件】」或全文结尾为止。\n\n'
sha = lambda b: hashlib.sha256(b if isinstance(b, bytes) else b.encode('utf-8')).hexdigest()


def key():
    if not os.path.exists(KEY_FILE):
        sys.exit('找不到密钥文件 ~/.config/anthropic/api_key，请研究发起人先存入密钥。')
    k = open(KEY_FILE, encoding='utf-8').read().strip()
    if not k:
        sys.exit('密钥文件是空的。')
    return k


def call(method, url, body=None, raw=False):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode('utf-8') if body is not None else None,
                                 headers={'x-api-key': key(), 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
                return data if raw else json.loads(data)
        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf-8', 'replace')[:500]
            if e.code in (429, 500, 502, 503, 529) and attempt < 5:
                time.sleep(10 * (attempt + 1)); continue
            sys.exit(f'接口返回错误 {e.code}：{msg}')
        except (urllib.error.URLError, http.client.HTTPException, ConnectionError, TimeoutError, OSError) as e:
            if attempt < 5:
                time.sleep(10 * (attempt + 1)); continue
            sys.exit(f'连不上接口：{e}')


def cid(name, kind):
    c = name.replace('甲', 'A').replace('乙', 'B')
    c = re.sub(r'_重跑(\d)', r'_r\1', c)
    if kind in ('adjudicator', 'seg_adjudicator'):
        base, _, r = c.partition('_r')
        c = base + '_ADJ' + ('_r' + r if r else '')
    assert re.fullmatch(r'[A-Za-z0-9_-]{1,64}', c), c
    return c


ORDER = ('codebook', '陈述', 'units', 'sentences', '论断', '归类甲', '归类乙', '切分甲', '切分乙', '待裁定')


def rank(f):
    if f == 'output_template.json':
        return (99, f)
    return (next((k for k, w in enumerate(ORDER) if w in f), 50), f)


def prompt(folder, instr=None):
    fs = sorted((f for f in os.listdir(folder) if not f.startswith('.') and f != 'instructions.txt'), key=rank)
    text = open(instr or os.path.join(folder, 'instructions.txt'), encoding='utf-8').read().rstrip('\n') + SEP
    for f in fs:
        text += f'【文件】{f}\n' + open(os.path.join(folder, f), encoding='utf-8').read().rstrip('\n') + '\n\n'
    return text


def params(text, kind):
    return {'model': MODEL, 'max_tokens': MAX_TOKENS[kind], 'output_config': {'effort': EFFORT}, 'messages': [{'role': 'user', 'content': text}]}


def cmd_build(a):
    T = json.load(open(a.tasks, encoding='utf-8'))
    kind = T['kind']
    assert not os.path.exists(a.run)
    os.makedirs(a.run)
    mp = {'kind': kind, 'model': MODEL, 'effort': EFFORT, 'max_tokens': MAX_TOKENS[kind], 'tasks': {}}
    with open(os.path.join(a.run, 'requests.jsonl'), 'x', encoding='utf-8') as f:
        for t in T['tasks']:
            text = prompt(t['dir'], t.get('instructions'))
            c = cid(t['name'], kind)
            assert c not in mp['tasks'], c
            mp['tasks'][c] = {'name': t['name'], 'id': t['id'], 'role': t.get('role'), 'rerun': t.get('rerun', 0), 'dir': os.path.relpath(t['dir'], HERE),
                              'instructions': os.path.relpath(t['instructions'], HERE) if t.get('instructions') else None, 'prompt_sha256': sha(text)}
            f.write(json.dumps({'custom_id': c, 'params': params(text, kind)}, ensure_ascii=False) + '\n')
    open(os.path.join(a.run, 'map.json'), 'x', encoding='utf-8').write(json.dumps(mp, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'请求数': len(mp['tasks']), '类型': kind}, ensure_ascii=False))


def load_requests(run):
    return [json.loads(l) for l in open(os.path.join(run, 'requests.jsonl'), encoding='utf-8')]


def ledger():
    return json.load(open(LEDGER, encoding='utf-8')) if os.path.exists(LEDGER) else {'说明': '批量接口花费账本（按 usage 与批量价格计算；以控制台账单为准）', 'runs': {}}


def spent(L):
    return round(sum(r.get('花费美元', 0) for r in L['runs'].values()), 4)


def cmd_count(a):
    reqs = load_requests(a.run)
    out, tot = {}, 0
    for r in reqs:
        p = r['params']
        n = call('POST', API + '/messages/count_tokens', {'model': p['model'], 'messages': p['messages']})['input_tokens']
        out[r['custom_id']] = n; tot += n
    kind = json.load(open(os.path.join(a.run, 'map.json'), encoding='utf-8'))['kind']
    est = tot * PRICE['input'] / 1e6 + len(reqs) * ASSUME_OUT[kind] * PRICE['output'] / 1e6
    json.dump({'input_tokens': out, '合计': tot, '估算花费美元（输出按每条 %d 估）' % ASSUME_OUT[kind]: round(est, 2)}, open(os.path.join(a.run, 'count.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'请求数': len(reqs), '输入token合计': tot, '每条均值': round(tot / len(reqs)), '估算花费美元': round(est, 2)}, ensure_ascii=False))


def cmd_submit(a):
    reqs = load_requests(a.run)
    mp = json.load(open(os.path.join(a.run, 'map.json'), encoding='utf-8'))
    assert not os.path.exists(os.path.join(a.run, 'batch.json')), '这一批已经提交过'
    cnt = json.load(open(os.path.join(a.run, 'count.json'), encoding='utf-8'))
    per = a.assume_output or ASSUME_OUT[mp['kind']]
    est = cnt['合计'] * PRICE['input'] / 1e6 + len(reqs) * per * PRICE['output'] / 1e6
    L = ledger()
    pending = sum(r.get('估算美元', 0) for r in L['runs'].values() if r.get('状态') == '已提交')
    if spent(L) + pending + est > a.cap:
        sys.exit(f'超过上限：已花 {spent(L)}，在途估算 {round(pending, 2)}，本批估算 {round(est, 2)}，上限 {a.cap}。不提交。')
    b = call('POST', API + '/messages/batches', {'requests': reqs})
    rec = {'batch_id': b['id'], 'submitted_at': datetime.datetime.now().astimezone().isoformat(), 'requests_sha256': sha(open(os.path.join(a.run, 'requests.jsonl'), 'rb').read()),
           '估算美元': round(est, 2)}
    open(os.path.join(a.run, 'batch.json'), 'x', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False, indent=1) + '\n')
    L['runs'][os.path.relpath(a.run, HERE)] = {'状态': '已提交', '估算美元': round(est, 2), 'batch_id': b['id']}
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(L, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'已提交': b['id'], '请求数': len(reqs), '本批估算美元': round(est, 2), '账本已花': spent(L)}, ensure_ascii=False))


def cmd_status(a):
    b = json.load(open(os.path.join(a.run, 'batch.json'), encoding='utf-8'))
    s = call('GET', f"{API}/messages/batches/{b['batch_id']}")
    print(json.dumps({'状态': s['processing_status'], '计数': s['request_counts']}, ensure_ascii=False))


def parse_json(text):
    t = text.strip()
    m = re.match(r'^```(?:json)?\s*\n(.*)\n```\s*$', t, re.S)
    if m:
        t = m.group(1)
    return json.loads(t)


NRM = lambda x: re.sub(r'[\s\W_]+', '', str(x or ''))
YN = ('是', '否')


def coder_row_ok(r):
    qa = str(r.get('问A', '')).strip()
    if qa == '定名':
        return str(r.get('问B', '')).strip() in ('象名', '义名') and str(r.get('问D', '')).strip() in YN
    if qa == '断事':
        return all(str(r.get(q, '')).strip() in YN for q in ('C1', 'C2', 'C3', 'C4', 'C5')) and str(r.get('问D', '')).strip() in YN
    return False


def seg_ok(lst, sent):
    return isinstance(lst, list) and all(isinstance(x, dict) and NRM(x.get('判断原文')) and NRM(x.get('判断原文')) in NRM(sent) for x in lst)


def check(kind, obj, folder):
    if kind in ('segmenter', 'seg_adjudicator'):
        sents = {u['编号']: u['句子'] for u in json.load(open(os.path.join(folder, 'sentences.json'), encoding='utf-8'))['句子']}
        key_ = '切分' if kind == 'segmenter' else '裁定'
        want = set(sents) if kind == 'segmenter' else set(json.load(open(os.path.join(folder, '待裁定.json'), encoding='utf-8'))['待裁定'])
        rows = obj.get(key_) if isinstance(obj.get(key_), list) else None
        if rows is None:
            return [f'没有「{key_}」']
        got = [x.get('编号') for x in rows]
        why = [] if set(got) == want and len(got) == len(want) else [f'编号不全或有多余（应 {len(want)}，交 {len(got)}）']
        bad = [x.get('编号') for x in rows if x.get('编号') in sents and not seg_ok(x.get('断语'), sents[x.get('编号')])]
        return why + ([f'判断原文不在句中：{len(bad)} 句'] if bad else [])
    if kind == 'judge':
        return [] if isinstance(obj.get('答案'), list) and obj['答案'] else ['没有「答案」']
    if kind == 'coder':
        want = {u['编号'] for u in json.load(open(os.path.join(folder, 'units.json'), encoding='utf-8'))['条目']}
        got = [x.get('编号') for x in obj.get('归类', [])] if isinstance(obj.get('归类'), list) else None
        if got is None:
            return ['没有「归类」']
        why = [] if set(got) == want and len(got) == len(want) else [f'归类编号不全或有多余（应 {len(want)}，交 {len(got)}）']
        bad = [x.get('编号') for x in obj['归类'] if not coder_row_ok(x)]
        return why + ([f'取值不合规：{len(bad)} 条'] if bad else [])
    want = {(x['编号'], x['项']) for x in json.load(open(os.path.join(folder, '待裁定.json'), encoding='utf-8'))['待裁定']}
    got = [(x.get('编号'), x.get('项')) for x in obj.get('裁定', [])] if isinstance(obj.get('裁定'), list) else None
    if got is None:
        return ['没有「裁定」']
    why = [] if set(got) == want and len(got) == len(want) else [f'裁定项不全或有多余（应 {len(want)}，交 {len(got)}）']
    bad = 0
    for x in obj['裁定']:
        it = x.get('项')
        if it == '整条':
            bad += 0 if coder_row_ok(x) else 1
        elif it == '问B':
            bad += 0 if str(x.get('裁定', '')).strip() in ('象名', '义名') else 1
        else:
            bad += 0 if str(x.get('裁定', '')).strip() in YN else 1
    return why + ([f'裁定取值不合规：{bad} 项'] if bad else [])


def cost(u):
    return (u.get('input_tokens', 0) * PRICE['input'] + u.get('output_tokens', 0) * PRICE['output']
            + u.get('cache_creation_input_tokens', 0) * PRICE['cache_write'] + u.get('cache_read_input_tokens', 0) * PRICE['cache_read']) / 1e6


def cmd_fetch(a):
    b = json.load(open(os.path.join(a.run, 'batch.json'), encoding='utf-8'))
    mp = json.load(open(os.path.join(a.run, 'map.json'), encoding='utf-8'))
    s = call('GET', f"{API}/messages/batches/{b['batch_id']}")
    if s['processing_status'] != 'ended':
        sys.exit(f"批次还没结束：{s['processing_status']} {json.dumps(s['request_counts'])}")
    raw = call('GET', s['results_url'], raw=True)
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
            total += cost(usage)
            if msg.get('stop_reason') != 'end_turn':
                why.append(f"stop_reason={msg.get('stop_reason')}")
            text = ''.join(c.get('text', '') for c in msg.get('content', []) if c.get('type') == 'text')
            try:
                obj = parse_json(text)
                why += check(mp['kind'], obj, os.path.join(HERE, t['dir']))
            except Exception:
                why.append('回复不是合法 JSON')
        open(os.path.join(a.out, name + '.api.json'), 'x', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=1) + '\n')
        if not why:
            open(os.path.join(a.out, name + '.json'), 'x', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1) + '\n')
        audit = {'name': name, 'id': t['id'], 'role': t.get('role'), 'rerun': t.get('rerun', 0), 'ok': not why, 'why_not_ok': why, 'custom_id': r['custom_id'],
                 'batch_id': b['batch_id'], 'model': msg.get('model'), 'message_id': msg.get('id'), 'stop_reason': msg.get('stop_reason'), 'usage': usage,
                 '花费美元': round(cost(usage), 4), 'prompt_sha256': t['prompt_sha256'], 'material_dir': t['dir']}
        open(os.path.join(a.out, name + '.audit.json'), 'x', encoding='utf-8').write(json.dumps(audit, ensure_ascii=False, indent=1) + '\n')
        (ok if not why else bad).append(name if not why else f"{name}（{'、'.join(why)}）")
    L = ledger()
    rk = os.path.relpath(a.run, HERE)
    L['runs'][rk] = {'状态': '已取回', '花费美元': round(total + L['runs'].get(rk, {}).get('花费美元', 0), 4), 'batch_id': b['batch_id']}
    json.dump(L, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'合格': len(ok), '不合格': bad, '本批花费美元': round(total, 2), '账本已花美元': spent(L)}, ensure_ascii=False))


def cmd_rerun(a):
    mp = json.load(open(os.path.join(a.run, 'map.json'), encoding='utf-8'))
    tasks = []
    for c, t in mp['tasks'].items():
        au = json.load(open(os.path.join(a.out, t['name'] + '.audit.json'), encoding='utf-8'))
        if au['ok']:
            continue
        base = re.sub(r'_重跑\d$', '', t['name'])
        n = t.get('rerun', 0) + 1
        if n > 2:
            continue
        tasks.append({'name': f'{base}_重跑{n}', 'id': t['id'], 'role': t.get('role'), 'rerun': n, 'dir': os.path.join(HERE, t['dir']),
                      **({'instructions': os.path.join(HERE, t['instructions'])} if t.get('instructions') else {})})
    if not tasks:
        print('没有要重跑的'); return
    tf = os.path.join(os.path.dirname(os.path.normpath(a.new)), os.path.basename(os.path.normpath(a.new)) + '_tasks.json')
    open(tf, 'x', encoding='utf-8').write(json.dumps({'kind': mp['kind'], 'tasks': tasks}, ensure_ascii=False, indent=1) + '\n')
    a.tasks = tf; a.run = a.new
    cmd_build(a)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('build', 'count', 'submit', 'status', 'fetch', 'rerun'))
    for k in ('tasks', 'run', 'out', 'new'):
        ap.add_argument('--' + k)
    ap.add_argument('--cap', type=float, default=185.0)
    ap.add_argument('--assume-output', type=int)
    a = ap.parse_args()
    {'build': cmd_build, 'count': cmd_count, 'submit': cmd_submit, 'status': cmd_status, 'fetch': cmd_fetch, 'rerun': cmd_rerun}[a.cmd](a)


if __name__ == '__main__':
    main()
