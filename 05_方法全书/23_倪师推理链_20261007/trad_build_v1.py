"""丁 传统框架归类：对象、切分、抽样与建包 v1（依据《00l_三项深化方案》v2 丁）。只打印编号与计数，不打印原文。
种子一律：SHA-256(种子字符串) 的十六进制前 16 位当整数，交给 random.Random。
对象：
  - 倪海厦全部 1685 步：知识库 chain_kb_v1.json 的定性步（起步）1314、推理步 371；名单按 (T 的数字, 步编号) 升序。
  - 《紫微斗数全书》400 句：全书分包 3025 个原文单元里 declared_layer 为 classical_text_in_corpus 的 2990 句，按冻结次序排好，
    用种子「METIS-V4-传统框架全书抽样-20261008」的 random.Random(整数).sample 抽 400 句；再经两人切分、一人裁定，切成断语，每条断语是一个归类条目。
子命令：
  units：写 <out>（trad_units_v1.json）：倪海厦条目、全书抽样句、原话全文（按 T）。
  seg --units … --out <切分目录>：全书 400 句按冻结次序排好，用种子「METIS-V4-传统框架全书切分分批-20261008」打乱，每 40 句一批（S01–S10），
        批内按冻结次序；每批一个切分包（instructions.txt = 切分说明、sentences.json、output_template.json）。写 <切分目录>/批名/ 与 batches.json。
  seg-adjudicate --batch-dir --a --b --adj-instr --out：两人切分不同的句子（判断原文去掉空白标点后的多重集合不同）建裁定包。
  seg-merge --units … --seg-dir … --returns … --adj-returns … --out <qs_units_v1.json>：定稿切分：两人相同的取切分甲的列表，不同的取裁定；
        每条断语一个条目，编号 = 句编号 + 「#」+ 序号（按判断原文在句中的位置）。有句子缺合格交卷或缺裁定的，停。
  pilot --round N --units … --qs-units … --codebook … --out …：试编第 N 轮：按种子「METIS-V4-传统框架试编N-20261008」依次抽
        起步 12、推理步 6、全书断语 12；另加富集层 10 条（原话摘录含 KEYWORDS 的起步 5、推理步 5，只用于停止规则）；去掉之前各轮抽过的。
  formal --units … --qs-units … --codebook … --out …：倪海厦 1685 步按出处 T 成团（起步与推理步同团），团按 T 的数字升序，
        用种子「METIS-V4-传统框架分批-20261008」打乱，满 45 步开下一批（N01……）；全书断语按句成团，句按冻结次序，
        用种子「METIS-V4-传统框架全书分批-20261008」打乱，满 40 条开下一批（Q01……）。写 <out>/批名/ 与 batches.json。
  adjudicate --batch-dir --a --b --adj-instr --out：两人问A 不同的整条交裁定；其余逐项列出问B、C1–C5、问D 的不同。
每个归类包：instructions.txt（= 归类说明）、units.json（「条目」与「原话」：本批条目引用的 T 的原话全文，每个 T 只放一份）、output_template.json。
倪海厦条目的材料：编号、来源、T、宫、适用、盘面条件（起步）或前提与附加条件（推理步）、结论（层、判断、原话说法）、连接（推理步）、原话摘录。
不给：命例特指、可操作、方向与强度、核查理由、结点号、旧的推理类型归类。
全书条目的材料：编号、来源、卷篇、条件原文、判断原文、所在句、所在整段。"""
import argparse, hashlib, json, os, random, re, shutil
from collections import Counter

QC = ['C1', 'C2', 'C3', 'C4', 'C5']
BATCH_MIN = 45
QS_BATCH = 40
SEG_BATCH = 40
N_QS = 400
KEYWORDS = re.compile(r'像|好比|就是|所谓|以此类推|同理|一样的道理')
PRIVATE = re.compile(r'/Users/|/home/|<用户名>|<用户名2>|file://')
norm = lambda s: re.sub(r'[\s\W_]+', '', str(s or ''))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def write(d, fn, obj):
    txt = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1) + '\n'
    assert not PRIVATE.search(txt), (d, fn)
    open(os.path.join(d, fn), 'x', encoding='utf-8').write(txt)


def tkey(u):
    return (int(u['T'][1:]), u['编号'])


def cmd_units(a):
    assert not os.path.exists(a.out)
    kb = json.load(open(a.kb, encoding='utf-8'))
    corpus = {}
    for ln in open(a.corpus, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜', 4)
        corpus[t[0]] = t[4]
    ni = []
    for s in kb['steps']:
        c = {'层': s['结论']['层'], '判断': s['结论']['判断'], '原话说法': s['结论'].get('原话说法', '')}
        if s['类型'] == '定性步':
            u = {'编号': s['step_id'], '来源': '倪海厦·起步', 'T': s['T'], '宫': s['宫'], '适用': s['适用'], '盘面条件': list(s.get('条件') or []),
                 '结论': c, '原话摘录': s['原话摘录']}
        else:
            u = {'编号': s['step_id'], '来源': '倪海厦·推理步', 'T': s['T'], '宫': s['宫'], '适用': s['适用'],
                 '前提': [{'层': p['层'], '判断': p['判断'], '原话说法': p.get('原话说法', '')} for p in s['前提']],
                 '附加条件': list(s.get('附加条件') or []), '结论': c, '连接': s.get('连接', ''), '原话摘录': s['原话摘录']}
        ni.append(u)
    ni.sort(key=tkey)
    assert len(ni) == 1685 and sum(u['来源'] == '倪海厦·起步' for u in ni) == 1314
    man = json.load(open(os.path.join(a.qs, 'manifest.json'), encoding='utf-8'))
    frozen = []
    for p in man['packets']:
        d = json.load(open(os.path.join(a.qs, p['path']), encoding='utf-8'))
        ctx = {c['context_id']: c['paragraph']['text'] for c in d['contexts']}
        for x in d['units']:
            u = x['unit']
            par = ctx.get(x['context_id'])
            assert par is not None and u['text'] in par, u['id']
            frozen.append({'编号': u['id'], '卷篇': u['chapter'], '句子': u['text'], '所在整段': par, 'layer': u['declared_layer']})
    assert len(frozen) == 3025 and len({u['编号'] for u in frozen}) == 3025
    classical = [u for u in frozen if u['layer'] == 'classical_text_in_corpus']
    assert len(classical) == 2990
    order = {u['编号']: k for k, u in enumerate(frozen)}
    pick = sorted(rng('METIS-V4-传统框架全书抽样-20261008').sample(classical, N_QS), key=lambda u: order[u['编号']])
    for u in pick:
        u.pop('layer')
    out = {'schema': 'trad-units-v1', 'inputs_sha256': {'kb': sha(a.kb), 'corpus': sha(a.corpus), 'qs_manifest': sha(os.path.join(a.qs, 'manifest.json'))},
           'qs_seed': 'METIS-V4-传统框架全书抽样-20261008', 'ni': ni, 'qs_sentences': pick, '原话': {T: corpus[T] for T in sorted({u['T'] for u in ni}, key=lambda t: int(t[1:]))}}
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'倪海厦': len(ni), '起步': sum(u['来源'] == '倪海厦·起步' for u in ni), '推理步': sum(u['来源'] == '倪海厦·推理步' for u in ni),
                      '全书抽样句': len(pick), '全书各卷': dict(Counter(u['卷篇'].split('·')[0] for u in pick))}, ensure_ascii=False))


# ---------- 全书切分 ----------
def cmd_seg(a):
    U = json.load(open(a.units, encoding='utf-8'))
    assert not os.path.exists(a.out)
    qs = U['qs_sentences']
    pos = {u['编号']: k for k, u in enumerate(qs)}
    qo = qs[:]
    rng('METIS-V4-传统框架全书切分分批-20261008').shuffle(qo)
    os.makedirs(a.out)
    man = {'seed': 'METIS-V4-传统框架全书切分分批-20261008', 'batches': []}
    instr = open(a.seg_instr, encoding='utf-8').read()
    for k in range(0, len(qo), SEG_BATCH):
        b = sorted(qo[k:k + SEG_BATCH], key=lambda u: pos[u['编号']])
        name = f'S{k // SEG_BATCH + 1:02d}'
        d = os.path.join(a.out, name)
        os.makedirs(d)
        write(d, 'instructions.txt', instr)
        write(d, 'sentences.json', {'批': name, '句子': b})
        write(d, 'output_template.json', {'批': name, '切分': [{'编号': u['编号'], '断语': [{'条件原文': '', '判断原文': ''}]} for u in b]})
        man['batches'].append({'batch': name, 'sentences': [u['编号'] for u in b], 'files_sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    write(a.out, 'batches.json', man)
    print(json.dumps({'切分批数': len(man['batches'])}, ensure_ascii=False))


def seg_key(lst):
    return sorted(norm(x.get('判断原文')) for x in (lst or []))


def cmd_seg_adjudicate(a):
    name = os.path.basename(os.path.normpath(a.batch_dir))
    d = os.path.join(a.out, name)
    assert not os.path.exists(d)
    A = {x['编号']: x['断语'] for x in json.load(open(a.a, encoding='utf-8'))['切分']}
    B = {x['编号']: x['断语'] for x in json.load(open(a.b, encoding='utf-8'))['切分']}
    assert set(A) == set(B)
    dis = [i for i in A if seg_key(A[i]) != seg_key(B[i])]
    os.makedirs(d)
    write(d, 'instructions.txt', open(a.adj_instr, encoding='utf-8').read())
    shutil.copyfile(os.path.join(a.batch_dir, 'instructions.txt'), os.path.join(d, 'codebook.txt'))
    shutil.copyfile(os.path.join(a.batch_dir, 'sentences.json'), os.path.join(d, 'sentences.json'))
    write(d, '切分甲.json', json.load(open(a.a, encoding='utf-8')))
    write(d, '切分乙.json', json.load(open(a.b, encoding='utf-8')))
    write(d, '待裁定.json', {'批': name, '待裁定': dis})
    write(d, 'output_template.json', {'批': name, '裁定': [{'编号': i, '断语': [{'条件原文': '', '判断原文': ''}], '理由': ''} for i in dis]})
    print(json.dumps({'batch': name, '待裁定句数': len(dis)}, ensure_ascii=False))


def accepted(rdir, name):
    for nm in (name, f'{name}_重跑1', f'{name}_重跑2'):
        au = os.path.join(rdir, nm + '.audit.json')
        if os.path.exists(au) and json.load(open(au, encoding='utf-8'))['ok']:
            return nm, json.load(open(os.path.join(rdir, nm + '.json'), encoding='utf-8'))
    return None, None


def cmd_seg_merge(a):
    U = json.load(open(a.units, encoding='utf-8'))
    sent = {u['编号']: u for u in U['qs_sentences']}
    man = json.load(open(os.path.join(a.seg_dir, 'batches.json'), encoding='utf-8'))
    assert not os.path.exists(a.out)
    units, stat, used = [], Counter(), {}
    for b in man['batches']:
        name = b['batch']
        na, A = accepted(a.returns, f'{name}_甲')
        nb, B = accepted(a.returns, f'{name}_乙')
        assert A and B, (name, '切分交卷不全')
        A = {x['编号']: x['断语'] for x in A['切分']}
        B = {x['编号']: x['断语'] for x in B['切分']}
        dis = [i for i in b['sentences'] if seg_key(A[i]) != seg_key(B[i])]
        D = {}
        nd = None
        if dis:
            nd, Dj = accepted(a.adj_returns, name)
            assert Dj, (name, '有分歧却没有合格裁定卷')
            D = {x['编号']: x['断语'] for x in Dj['裁定']}
            assert set(D) == set(dis), (name, '裁定句子不全')
        used[name] = [na, nb, nd]
        for i in b['sentences']:
            final = A[i] if i not in dis else D[i]
            stat['相同' if i not in dis else '裁定'] += 1
            s = sent[i]
            ns = norm(s['句子'])
            items = []
            for x in final:
                j = norm(x.get('判断原文'))
                assert j and j in ns, (i, '判断原文不在句中')
                items.append((ns.find(j), x))
            items.sort(key=lambda t: t[0])
            for k, (_, x) in enumerate(items, 1):
                units.append({'编号': f'{i}#{k}', '来源': '全书', '句编号': i, '卷篇': s['卷篇'], '条件原文': x.get('条件原文', ''), '判断原文': x['判断原文'],
                              '所在句': s['句子'], '所在整段': s['所在整段']})
            stat['断语'] += len(items)
            stat['无断语句'] += 0 if items else 1
    out = {'schema': 'trad-qs-units-v1', '采用的交卷': used, '统计': dict(stat), '条目': units}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(stat), ensure_ascii=False))


# ---------- 归类 ----------
def template(name, units):
    rows = []
    for u in units:
        r = {'编号': u['编号'], '问A': '', '问B': ''}
        for q in QC:
            r[q] = ''; r[q + '依据'] = ''
        r.update({'问D': '', '备注': ''})
        rows.append(r)
    return {'批': name, '归类': rows}


def make_pack(d, name, units, codebook, yuan):
    os.makedirs(d)
    write(d, 'instructions.txt', open(codebook, encoding='utf-8').read())
    Ts = sorted({u['T'] for u in units if 'T' in u}, key=lambda t: int(t[1:]))
    write(d, 'units.json', {'批': name, '条目': units, '原话': {T: yuan[T] for T in Ts}})
    write(d, 'output_template.json', template(name, units))
    return {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}


def load_all(a):
    U = json.load(open(a.units, encoding='utf-8'))
    Q = json.load(open(a.qs_units, encoding='utf-8'))['条目']
    return U['ni'], Q, U['原话']


def cmd_pilot(a):
    ni, qs, yuan = load_all(a)
    used = set()
    for k in range(1, a.round):
        used |= set(json.load(open(os.path.join(a.out, f'sample_P{k}.json'), encoding='utf-8'))['units'])
    r = rng(f'METIS-V4-传统框架试编{a.round}-20261008')
    q1 = [u for u in ni if u['来源'] == '倪海厦·起步' and u['编号'] not in used]
    q2 = [u for u in ni if u['来源'] == '倪海厦·推理步' and u['编号'] not in used]
    q3 = [u for u in qs if u['编号'] not in used]
    p1, p2 = r.sample(q1, 12), r.sample(q2, 6)
    p3 = {x['编号'] for x in r.sample(q3, 12)}
    taken = {u['编号'] for u in p1 + p2}
    e1 = r.sample([u for u in q1 if u['编号'] not in taken and KEYWORDS.search(u['原话摘录'])], 5)
    e2 = r.sample([u for u in q2 if u['编号'] not in taken and KEYWORDS.search(u['原话摘录'])], 5)
    pick = sorted(p1 + p2 + e1 + e2, key=tkey) + [u for u in qs if u['编号'] in p3]
    name = f'P{a.round}'
    d = os.path.join(a.out, name)
    assert not os.path.exists(d)
    os.makedirs(a.out, exist_ok=True)
    files = make_pack(d, name, pick, a.codebook, yuan)
    write(a.out, f'sample_P{a.round}.json', {'seed': f'METIS-V4-传统框架试编{a.round}-20261008', 'excluded': sorted(used), 'units': [u['编号'] for u in pick],
                                              '富集层': sorted(u['编号'] for u in e1 + e2), 'files_sha256': files})
    print(json.dumps({'round': a.round, 'units': len(pick), '富集层': len(e1 + e2)}, ensure_ascii=False))


def cmd_formal(a):
    ni, qs, yuan = load_all(a)
    assert not os.path.exists(a.out)
    clusters = {}
    for u in ni:
        clusters.setdefault(u['T'], []).append(u)
    order = sorted(clusters, key=lambda t: int(t[1:]))
    rng('METIS-V4-传统框架分批-20261008').shuffle(order)
    batches, cur = [], []
    for t in order:
        if len(cur) >= BATCH_MIN:
            batches.append(cur); cur = []
        cur += clusters[t]
    if cur:
        batches.append(cur)
    sc = {}
    for u in qs:
        sc.setdefault(u['句编号'], []).append(u)
    sorder = list(sc)
    rng('METIS-V4-传统框架全书分批-20261008').shuffle(sorder)
    qb, cur = [], []
    for s in sorder:
        if len(cur) >= QS_BATCH:
            qb.append(cur); cur = []
        cur += sc[s]
    if cur:
        qb.append(cur)
    qpos = {u['编号']: k for k, u in enumerate(qs)}
    os.makedirs(a.out)
    man = {'seeds': ['METIS-V4-传统框架分批-20261008', 'METIS-V4-传统框架全书分批-20261008'], 'batch_min': BATCH_MIN, 'qs_batch': QS_BATCH, 'batches': []}
    for k, b in enumerate(batches, 1):
        name = f'N{k:02d}'
        b = sorted(b, key=tkey)
        man['batches'].append({'batch': name, 'units': [u['编号'] for u in b], 'files_sha256': make_pack(os.path.join(a.out, name), name, b, a.codebook, yuan)})
    for k, b in enumerate(qb, 1):
        name = f'Q{k:02d}'
        b = sorted(b, key=lambda u: qpos[u['编号']])
        man['batches'].append({'batch': name, 'units': [u['编号'] for u in b], 'files_sha256': make_pack(os.path.join(a.out, name), name, b, a.codebook, yuan)})
    write(a.out, 'batches.json', man)
    print(json.dumps({'倪海厦批数': len(batches), '倪海厦批大小': [len(b) for b in batches], '全书批数': len(qb), '全书批大小': [len(b) for b in qb],
                      '合计条目': sum(len(b) for b in batches) + sum(len(b) for b in qb)}, ensure_ascii=False))


def val(x, allowed):
    x = str(x or '').strip()
    return x if x in allowed else None


def disagreements(A, B, ids):
    a = {x['编号']: x for x in A['归类']}
    b = {x['编号']: x for x in B['归类']}
    assert set(a) == set(b) == set(ids), '编号不同'
    out = []
    for i in ids:
        qa, qb = val(a[i].get('问A'), ('定名', '断事')), val(b[i].get('问A'), ('定名', '断事'))
        if qa != qb:
            out.append({'编号': i, '项': '整条'}); continue
        items = (['问B'] if qa == '定名' else QC) + ['问D']
        for q in items:
            allowed = ('象名', '义名') if q == '问B' else ('是', '否')
            if val(a[i].get(q), allowed) != val(b[i].get(q), allowed):
                out.append({'编号': i, '项': q, '甲': a[i].get(q, ''), '乙': b[i].get(q, '')})
    return out


def cmd_adjudicate(a):
    name = os.path.basename(os.path.normpath(a.batch_dir))
    d = os.path.join(a.out, name)
    assert not os.path.exists(d)
    A = json.load(open(a.a, encoding='utf-8'))
    B = json.load(open(a.b, encoding='utf-8'))
    ids = [u['编号'] for u in json.load(open(os.path.join(a.batch_dir, 'units.json'), encoding='utf-8'))['条目']]
    dis = disagreements(A, B, ids)
    os.makedirs(d)
    write(d, 'instructions.txt', open(a.adj_instr, encoding='utf-8').read())
    shutil.copyfile(os.path.join(a.batch_dir, 'instructions.txt'), os.path.join(d, 'codebook.txt'))
    shutil.copyfile(os.path.join(a.batch_dir, 'units.json'), os.path.join(d, 'units.json'))
    write(d, '归类甲.json', A)
    write(d, '归类乙.json', B)
    write(d, '待裁定.json', {'批': name, '待裁定': dis})
    rows = []
    for x in dis:
        if x['项'] == '整条':
            r = {'编号': x['编号'], '项': '整条', '问A': '', '问B': ''}
            for q in QC:
                r[q] = ''; r[q + '依据'] = ''
            r.update({'问D': '', '理由': ''})
            rows.append(r)
        else:
            rows.append({'编号': x['编号'], '项': x['项'], '裁定': '', '依据': '', '理由': ''})
    write(d, 'output_template.json', {'批': name, '裁定': rows})
    print(json.dumps({'batch': name, '待裁定项': len(dis), '整条': sum(x['项'] == '整条' for x in dis), '涉及条数': len({x['编号'] for x in dis})}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('units', 'seg', 'seg-adjudicate', 'seg-merge', 'pilot', 'formal', 'adjudicate'))
    ap.add_argument('--round', type=int)
    for k in ('kb', 'corpus', 'qs', 'units', 'qs-units', 'codebook', 'seg-instr', 'seg-dir', 'returns', 'adj-returns', 'out', 'batch-dir', 'a', 'b', 'adj-instr'):
        ap.add_argument('--' + k)
    a = ap.parse_args()
    {'units': cmd_units, 'seg': cmd_seg, 'seg-adjudicate': cmd_seg_adjudicate, 'seg-merge': cmd_seg_merge, 'pilot': cmd_pilot,
     'formal': cmd_formal, 'adjudicate': cmd_adjudicate}[a.cmd](a)


if __name__ == '__main__':
    main()
