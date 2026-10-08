"""M4 配对检验：建题 v2（机械执行《01》《03》《05_M4执行细则_v1》《11_M4判包分文件_v1》；只打印编号与计数，不打印陈述或论断内容）。
v2 与 v1 的选题、干扰、排序、留一、论断生成完全相同，只改判包的文件格式与每包题数：
- 陈述与每份论断各写成一个文本文件（真换行），不再把整份论断放进 JSON 的一行；
- 主检验每包 1 题（v1 为 3 题；《01》规定「至多 3 题」）。
输入：冻结的倪师层、全书补层知识库合并文件；m3_statements_merged_v1.json（人、命盘候选、陈述、讲述时段、标记）。
步骤：
1. 每个有命盘的人：各候选用 chart_runner_v1.cjs 排盘；性别、五行局取各候选一致者，不一致记为不确定。
2. 每个纳入的人出一题：
   - 按此人讲述时段做逐例留一，得到本题规则集；
   - 真论断与 3 份干扰论断都用本题规则集读（ni_engine_v1.read_candidates + render_text(cite=False)）；
   - 干扰：有命盘的其他人，剔除同八字者；分档（同性别同局 → 同性别 → 不限）、档内按 SHA-256(种子|目标|候选) 升序；
   - 四份按 SHA-256(种子|目标|论断所属人) 升序排成 A–D。
3. 判包：主检验每包 1 题（题NN_陈述.txt、题NN_论断A–D.txt），每包由两名互不相通的盲审各判一次；
   次要检验每人两组：本人论断、干扰中排第一的他盘论断，全部组按 SHA-256(种子|组) 打乱，每包至多 4 组（组NN_陈述.txt、组NN_论断.txt）。
4. 答案与对照表写进 key_v1.json（不进任何判包；格式与 v1 相同，m4_analyze_v1.py 照用）。
用法：python3 m4_build_v2.py --kb <倪师层合并> --kb-qs <全书补层合并> --persons <m3_statements_merged_v1.json> --out <新目录>"""
import argparse, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_engine_v1 as E

SEED = 'METIS-M4-配对-20261005'
NODE = '/opt/homebrew/Cellar/node/26.0.0/bin/node'
PER_ITEM_PACK, PER_PAIR_PACK = 1, 4
PRIVATE = re.compile(r'/Users/|/home/|<用户名>|<用户名2>|file://')
h = lambda *xs: hashlib.sha256('|'.join(xs).encode('utf-8')).hexdigest()
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def run_charts(forms):
    inputs = [{'id': k, 'form': f} for k, f in forms.items()]
    p = subprocess.run([NODE, os.path.join(HERE, 'chart_runner_v1.cjs')], input=json.dumps(inputs), capture_output=True, text=True,
                       env={'PATH': '/usr/bin:/bin', 'TZ': 'Asia/Taipei', 'LANG': 'en_US.UTF-8'}, timeout=3600)
    assert p.returncode == 0, p.stderr[-2000:]
    return {r['id']: r for r in json.loads(p.stdout)['rows']}


def write(d, fn, obj):
    txt = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1) + '\n'
    assert not PRIVATE.search(txt), (d, fn)
    open(os.path.join(d, fn), 'x', encoding='utf-8').write(txt)


def stmt_text(sts):
    """陈述：每行一条，序号、对象、年龄、内容。"""
    return ''.join(f"{s['序号']}. （对象：{s['对象'] or '未说'}；年龄：{s['年龄'] or '未说'}）{' '.join(str(s['内容']).split())}\n" for s in sts)


def body_text(t):
    return t if t.endswith('\n') else t + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'kb-qs', 'persons', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    rules = E.load_rules([a.kb, a.kb_qs])
    M = json.load(open(a.persons, encoding='utf-8'))
    persons = {p['person_id']: p for p in M['persons']}
    same = {tuple(x) for x in M['same_bazi_pairs']} | {tuple(reversed(x)) for x in M['same_bazi_pairs']}
    charted = [pid for pid, p in persons.items() if p['candidates']]
    rows = run_charts({f"{pid}#{i}": b['form'] for pid in charted for i, b in enumerate(persons[pid]['candidates'])})
    cand_rows = {pid: [rows[f'{pid}#{i}'] for i in range(len(persons[pid]['candidates']))] for pid in charted}
    for pid, rs in cand_rows.items():
        assert all('error' not in r for r in rs), pid
    gender = {pid: ({r['birth']['gender'] for r in rs}.pop() if len({r['birth']['gender'] for r in rs}) == 1 else None) for pid, rs in cand_rows.items()}
    ju = {pid: ({r['chart']['wuxingJu'] for r in rs}.pop() if len({r['chart']['wuxingJu'] for r in rs}) == 1 else None) for pid, rs in cand_rows.items()}
    targets = sorted(pid for pid in charted if persons[pid]['eligible'])
    os.makedirs(a.out)
    items, pairs, key = [], [], {'seed': SEED, 'items': {}, 'pairs': {}}
    for n, t in enumerate(targets, 1):
        rs_t, dropped = E.leave_out(rules, persons[t]['segments'])
        pool = [c for c in charted if c != t and (t, c) not in same]
        def tier(c):
            if gender[t] and gender[c] == gender[t] and ju[t] is not None and ju[c] == ju[t]:
                return 0
            if gender[t] and gender[c] == gender[t]:
                return 1
            return 2
        decoys = sorted(pool, key=lambda c: (tier(c), h(SEED, t, c)))[:3]
        owners = sorted([t] + decoys, key=lambda c: h(SEED, t, c + '#论断'))
        texts = {}
        for c in owners:
            rd, by_id = E.read_candidates(cand_rows[c], rs_t)
            texts[c] = E.render_text(rd, by_id, cite=False)
        letters = dict(zip('ABCD', owners))
        iid = f'题{n:02d}'
        sts = [{'序号': i, '内容': s['内容'], '对象': s.get('对象', ''), '年龄': s.get('年龄', '')} for i, s in enumerate(persons[t]['statements'], 1)]
        items.append({'题': iid, '陈述': sts, '论断': {L: texts[c] for L, c in letters.items()}})
        key['items'][iid] = {'person': t, 'true': next(L for L, c in letters.items() if c == t), 'letters': letters, 'decoys_in_tier_order': decoys,
                             'tiers': {c: tier(c) for c in decoys}, 'rules_used': len(rs_t), 'rules_left_out': dropped,
                             'identity_doubt': persons[t]['identity_doubt'], 'n_statements': len(sts),
                             'categories': [s.get('类别', '') for s in persons[t]['statements']]}
        for kind, owner in (('本盘', t), ('他盘', decoys[0])):
            pk = h(SEED, t, kind)
            pairs.append((pk, {'陈述': sts, '论断': texts[owner]}, {'person': t, 'kind': kind, 'owner': owner}))
    pairs.sort(key=lambda x: x[0])
    for i, (_, body, meta) in enumerate(pairs, 1):
        gid = f'组{i:02d}'
        body['组'] = gid
        key['pairs'][gid] = meta
    ji = open(os.path.join(HERE, 'm4_judge_instructions_v2.txt'), encoding='utf-8').read()
    si = open(os.path.join(HERE, 'm4_stmt_instructions_v2.txt'), encoding='utf-8').read()
    man = {'schema': 'm4-packets-v2', 'judge_packs': [], 'stmt_packs': []}
    for k in range(0, len(items), PER_ITEM_PACK):
        name = f'M{k // PER_ITEM_PACK + 1:02d}'
        d = os.path.join(a.out, 'judge_packets', name); os.makedirs(d)
        chunk = items[k:k + PER_ITEM_PACK]
        write(d, 'instructions.txt', ji)
        for it in chunk:
            write(d, f"{it['题']}_陈述.txt", stmt_text(it['陈述']))
            for L in 'ABCD':
                write(d, f"{it['题']}_论断{L}.txt", body_text(it['论断'][L]))
        write(d, 'output_template.json', {'包': name, '答案': [{'题': it['题'], '最符合': '', '排序': ['', '', '', ''], '理由': {L: '' for L in 'ABCD'}} for it in chunk]})
        man['judge_packs'].append({'pack': name, 'items': [it['题'] for it in chunk], 'files_sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    bodies = [b for _, b, _ in pairs]
    for k in range(0, len(bodies), PER_PAIR_PACK):
        name = f'S{k // PER_PAIR_PACK + 1:02d}'
        d = os.path.join(a.out, 'stmt_packets', name); os.makedirs(d)
        chunk = bodies[k:k + PER_PAIR_PACK]
        write(d, 'instructions.txt', si)
        for b in chunk:
            write(d, f"{b['组']}_陈述.txt", stmt_text(b['陈述']))
            write(d, f"{b['组']}_论断.txt", body_text(b['论断']))
        write(d, 'output_template.json', {'包': name, '判定': [{'组': b['组'], '逐条': [{'序号': s['序号'], '判定': '', '依据': ''} for s in b['陈述']]} for b in chunk]})
        man['stmt_packs'].append({'pack': name, 'pairs': [b['组'] for b in chunk], 'files_sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    key['build_script'] = 'm4_build_v2.py'
    key['inputs_sha256'] = {'kb': sha(a.kb), 'kb_qs': sha(a.kb_qs), 'persons': sha(a.persons), 'engine': sha(os.path.join(HERE, 'ni_engine_v1.py')),
                            'runner': sha(os.path.join(HERE, 'chart_runner_v1.cjs'))}
    write(a.out, 'key_v1.json', key)
    write(a.out, 'manifest.json', man)
    print(json.dumps({'items': len(items), 'pairs': len(pairs), 'judge_packs': len(man['judge_packs']), 'stmt_packs': len(man['stmt_packs']),
                      'decoy_tiers': {iid: sorted(v['tiers'].values()) for iid, v in key['items'].items()},
                      'rules_left_out': {iid: v['rules_left_out'] for iid, v in key['items'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
