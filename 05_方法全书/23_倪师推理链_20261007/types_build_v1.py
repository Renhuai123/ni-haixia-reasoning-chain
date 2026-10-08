"""乙 推理类型：抽样与建包 v1（依据《00h_三项补充研究方案_v2.md》三、一）。只打印编号与计数，不打印原话。
种子一律：SHA-256(种子字符串) 的十六进制前 16 位当整数，交给 random.Random。名单一律按 (T 的数字, 步编号) 升序。
子命令：
  pilot --round N：试编第 N 轮（N 为 1 或 2）。名单 = 知识库 371 条推理步，去掉 25 条审稿样例与之前各轮试编抽过的步；
        种子「METIS-V4-推理类型试编N-20261007」，random.Random(整数).sample(名单, 30)。写 <out>/P{N}/ 与 <out>/sample_P{N}.json。
  formal：371 步按出处 T 成团；团按 T 的数字升序排好，用种子「METIS-V4-推理类型分批-20261007」的 random.Random(整数).shuffle 打乱；
        依次装批，当前批已有 47 步以上就开下一批。写 <out>/Bxx/ 与 <out>/batches.json。
  adjudicate --batch-dir <批目录> --a <归类甲.json> --b <归类乙.json>：列出两人答案不同的项，建裁定包 <out>/<批名>/。
每个归类包：instructions.txt（= 归类说明）、steps.json、output_template.json。裁定包另有 codebook.txt、归类甲.json、归类乙.json、待裁定.json。
步的材料：编号、T、宫、适用、前提（层、判断、原话说法）、附加条件、结论（层、判断、原话说法）、连接、原话摘录、原话全文（原话库）。
不给：命例特指、可操作、方向与强度、核查理由、结点号。
用法：python3 types_build_v1.py pilot --round 1 --kb chain_kb_v1.json --corpus <ni_corpus.txt> --codebook types_codebook_v1.txt --out types_v1/pilot
      python3 types_build_v1.py formal --kb … --corpus … --codebook … --out types_v1/formal
      python3 types_build_v1.py adjudicate --batch-dir types_v1/formal/B01 --a <甲交卷> --b <乙交卷> --adj-instr types_adjudicate_instructions_v1.txt --out types_v1/adjudicate"""
import argparse, hashlib, json, os, random, re, shutil

REVIEW25 = ['T1520-c1', 'T191-c3', 'T149-c2', 'T96-c1', 'T14-c2', 'T133-c7', 'T302-c6', 'T844-c1', 'T1488-c3', 'T1097-c2', 'T505-c2', 'T92-c3', 'T848-c2',
            'T653-c2', 'T471-c3', 'T203-c2', 'T297-c1', 'T502-c3', 'T703-c2', 'T196-c3', 'T304-c2', 'T926-c1', 'T180-c2', 'T259-c2', 'T785-c6']
QS = ['问1', '问2', '问3', '问4', '问5']
FLAGS = {'标A': ('无附加条件', '主要靠附加条件', '不主要靠附加条件'), '标B': ('原话不是在讲具体的人', '仍成立', '不成立'), '标C': ('是', '否')}
BATCH_MIN = 47
PRIVATE = re.compile(r'/Users/|/home/|<用户名>|<用户名2>|file://')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def order_key(s):
    return (int(s['T'][1:]), s['step_id'])


def write(d, fn, obj):
    txt = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1) + '\n'
    assert not PRIVATE.search(txt), (d, fn)
    open(os.path.join(d, fn), 'x', encoding='utf-8').write(txt)


def load(a):
    kb = json.load(open(a.kb, encoding='utf-8'))
    inf = sorted((s for s in kb['steps'] if s['类型'] == '推理步'), key=order_key)
    assert len(inf) == 371 and set(REVIEW25) <= {s['step_id'] for s in inf}
    corpus = {}
    for ln in open(a.corpus, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜', 4)
        corpus[t[0]] = t[4]
    return inf, corpus


def material(s, corpus):
    return {'编号': s['step_id'], 'T': s['T'], '宫': s['宫'], '适用': s['适用'],
            '前提': [{'层': p['层'], '判断': p['判断'], '原话说法': p.get('原话说法', '')} for p in s['前提']],
            '附加条件': list(s.get('附加条件') or []),
            '结论': {'层': s['结论']['层'], '判断': s['结论']['判断'], '原话说法': s['结论'].get('原话说法', '')},
            '连接': s.get('连接', ''), '原话摘录': s['原话摘录'], '原话全文': corpus[s['T']]}


def template(name, steps):
    row = lambda i: dict({'编号': i}, **{k: v for q in QS for k, v in ((q, ''), (q + '依据', ''))}, 标A='', 标B='', 标C='', 备注='')
    return {'批': name, '归类': [row(s['step_id']) for s in steps]}


def make_pack(d, name, steps, corpus, codebook):
    os.makedirs(d)
    write(d, 'instructions.txt', open(codebook, encoding='utf-8').read())
    write(d, 'steps.json', {'批': name, '推理步': [material(s, corpus) for s in steps]})
    write(d, 'output_template.json', template(name, steps))
    return {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}


def cmd_pilot(a):
    inf, corpus = load(a)
    used = set(REVIEW25)
    for k in range(1, a.round):
        used |= set(json.load(open(os.path.join(a.out, f'sample_P{k}.json'), encoding='utf-8'))['steps'])
    pool = [s for s in inf if s['step_id'] not in used]
    seed = f'METIS-V4-推理类型试编{a.round}-20261007'
    pick = sorted(rng(seed).sample(pool, 30), key=order_key)
    name = f'P{a.round}'
    d = os.path.join(a.out, name)
    assert not os.path.exists(d)
    os.makedirs(a.out, exist_ok=True)
    files = make_pack(d, name, pick, corpus, a.codebook)
    write(a.out, f'sample_P{a.round}.json', {'seed': seed, 'pool_size': len(pool), 'excluded': sorted(used, key=lambda x: (int(x.split('-')[0][1:]), x)),
                                              'steps': [s['step_id'] for s in pick], 'files_sha256': files})
    print(json.dumps({'round': a.round, 'pool': len(pool), 'steps': len(pick)}, ensure_ascii=False))


def cmd_formal(a):
    inf, corpus = load(a)
    assert not os.path.exists(a.out)
    clusters = {}
    for s in inf:
        clusters.setdefault(s['T'], []).append(s)
    order = sorted(clusters, key=lambda t: int(t[1:]))
    rng('METIS-V4-推理类型分批-20261007').shuffle(order)
    batches, cur = [], []
    for t in order:
        if len(cur) >= BATCH_MIN:
            batches.append(cur); cur = []
        cur += clusters[t]
    if cur:
        batches.append(cur)
    os.makedirs(a.out)
    man = {'seed': 'METIS-V4-推理类型分批-20261007', 'batch_min': BATCH_MIN, 'batches': []}
    for k, b in enumerate(batches, 1):
        name = f'B{k:02d}'
        b = sorted(b, key=order_key)
        files = make_pack(os.path.join(a.out, name), name, b, corpus, a.codebook)
        man['batches'].append({'batch': name, 'steps': [s['step_id'] for s in b], 'files_sha256': files})
    write(a.out, 'batches.json', man)
    print(json.dumps({'batches': len(batches), 'sizes': [len(b) for b in batches], 'total': sum(len(b) for b in batches)}, ensure_ascii=False))


def norm_q(x):
    x = str(x or '').strip()
    return x if x in ('是', '否') else None


def disagreements(A, B):
    a = {x['编号']: x for x in A['归类']}
    b = {x['编号']: x for x in B['归类']}
    assert set(a) == set(b), '两人编号不同'
    out = []
    for i in a:
        for q in QS:
            if norm_q(a[i].get(q)) != norm_q(b[i].get(q)):
                out.append({'编号': i, '项': q, '甲': a[i].get(q, ''), '乙': b[i].get(q, '')})
        for f in FLAGS:
            if str(a[i].get(f, '')).strip() != str(b[i].get(f, '')).strip():
                out.append({'编号': i, '项': f, '甲': a[i].get(f, ''), '乙': b[i].get(f, '')})
    return out


def cmd_adjudicate(a):
    name = os.path.basename(os.path.normpath(a.batch_dir))
    d = os.path.join(a.out, name)
    assert not os.path.exists(d)
    A = json.load(open(a.a, encoding='utf-8'))
    B = json.load(open(a.b, encoding='utf-8'))
    dis = disagreements(A, B)
    os.makedirs(d)
    write(d, 'instructions.txt', open(a.adj_instr, encoding='utf-8').read())
    shutil.copyfile(os.path.join(a.batch_dir, 'instructions.txt'), os.path.join(d, 'codebook.txt'))
    shutil.copyfile(os.path.join(a.batch_dir, 'steps.json'), os.path.join(d, 'steps.json'))
    write(d, '归类甲.json', A)
    write(d, '归类乙.json', B)
    write(d, '待裁定.json', {'批': name, '待裁定': dis})
    write(d, 'output_template.json', {'批': name, '裁定': [{'编号': x['编号'], '项': x['项'], '裁定': '', '依据': '', '理由': ''} for x in dis]})
    print(json.dumps({'batch': name, '待裁定项': len(dis), '涉及步数': len({x['编号'] for x in dis})}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('pilot', 'formal', 'adjudicate'))
    ap.add_argument('--round', type=int)
    for k in ('kb', 'corpus', 'codebook', 'out', 'batch-dir', 'a', 'b', 'adj-instr'):
        ap.add_argument('--' + k)
    a = ap.parse_args()
    {'pilot': cmd_pilot, 'formal': cmd_formal, 'adjudicate': cmd_adjudicate}[a.cmd](a)


if __name__ == '__main__':
    main()
