"""丙 召回率：抽样与建包 v1（依据《00h_三项补充研究方案_v2.md》四、一）。只打印编号与计数，不打印原话。
总体：正式抽取 35 批（chain_packets_v2/K01–K35/batch.json）的 1374 条倪师原话。
分层（按知识库 chain_kb_v1.json 收下的步）：S1 含推理步；S2 只有定性步（起步）；S3 一步都没有。
种子：SHA-256(种子字符串) 的十六进制前 16 位当整数，交给 random.Random；名单一律按 T 的数字升序。
子命令：
  sample：用种子「METIS-V4-召回率抽样-20261007」的同一个 random.Random，依次从 S1、S2、S3 里 .sample 104、124、72 条；
          300 条按 T 的数字升序排好后，用种子「METIS-V4-召回率分包-20261007」.shuffle，依次每 25 条一包（R01–R12），包内按 T 的数字升序。
          写 <out>/sample_v1.json（不含原话）。
  finder-packs：按 sample_v1.json 建找漏包 <out>/finder/Rxx/：instructions.txt（找漏说明）、抽取规矩.txt（正式抽取实际用的说明，核对 SHA-256）、
          pack.json（原话的 T、分P、时间、整理主题、原话、全面比对分类，取自抽取时的 batch.json；另附「已列步」＝知识库收下的步，照抽取格式）、
          context.txt（每条原话在原话库里前后各 5 条）、output_template.json。
  adj-pack --pack Rxx --a <找漏甲交卷> --b <找漏乙交卷>：建裁定包 <out>/adjudicate/Rxx/：找漏包的 pack.json、context.txt、抽取规矩.txt，
          另加 核查规矩.txt（正式核查用的说明，核对 SHA-256）、找漏甲.json、找漏乙.json、instructions.txt（裁定说明）、output_template.json（列出每一条漏步）。
用法：python3 recall_build_v1.py sample --kb chain_kb_v1.json --packets chain_packets_v2 --out recall_v1
      python3 recall_build_v1.py finder-packs --kb … --packets … --corpus <ni_corpus.txt> --finder-instr recall_finder_instructions_v1.txt --out recall_v1
      python3 recall_build_v1.py adj-pack --pack R01 --a … --b … --check-instr chain_check_instructions_v1.txt --adj-instr recall_adjudicate_instructions_v1.txt --out recall_v1"""
import argparse, collections, glob, hashlib, json, os, random, re, shutil

N_PER = {'S1': 104, 'S2': 124, 'S3': 72}
PACK = 25
CTX = 5
EXTRACT_SHA = 'b4ec921643aab1c100de1f904d9df9e600ed74fa5a1cb616afde58de7f292531'
CHECK_SHA_PREFIX = '27e227314436d7a6'
PRIVATE = re.compile(r'/Users/|/home/|<用户名>|<用户名2>|file://')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
tnum = lambda t: int(t[1:])


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def write(d, fn, obj):
    txt = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1) + '\n'
    assert not PRIVATE.search(txt), (d, fn)
    open(os.path.join(d, fn), 'x', encoding='utf-8').write(txt)


def population(packets):
    items = {}
    for f in sorted(glob.glob(os.path.join(packets, 'K*', 'batch.json'))):
        for x in json.load(open(f, encoding='utf-8'))['倪师条目']:
            items[x['T']] = x
    assert len(items) == 1374
    return items


def strata(kb, items):
    by = collections.defaultdict(set)
    for s in kb['steps']:
        by[s['T']].add(s['类型'])
    S = {'S1': [], 'S2': [], 'S3': []}
    for t in sorted(items, key=tnum):
        S['S1' if '推理步' in by.get(t, ()) else 'S2' if by.get(t) else 'S3'].append(t)
    return S


def listed(s):
    out = {'编号': s['step_id'], '类型': s['类型'], '宫': s['宫'], '适用': s['适用']}
    if s['类型'] == '定性步':
        out['条件'] = list(s.get('条件') or [])
    else:
        out['前提'] = [{'层': p['层'], '判断': p['判断'], '原话说法': p.get('原话说法', '')} for p in s['前提']]
        out['附加条件'] = list(s.get('附加条件') or [])
    out['结论'] = {k: s['结论'].get(k, '') for k in ('层', '判断', '原话说法', '方向', '强度')}
    if s['类型'] == '推理步':
        out['连接'] = s.get('连接', '')
    out.update({'原话摘录': s['原话摘录'], '命例特指': s['命例特指'], '可操作': s['可操作']})
    return out


def cmd_sample(a):
    kb = json.load(open(a.kb, encoding='utf-8'))
    items = population(a.packets)
    S = strata(kb, items)
    r = rng('METIS-V4-召回率抽样-20261007')
    pick = {h: r.sample(S[h], N_PER[h]) for h in ('S1', 'S2', 'S3')}
    allp = sorted((t for v in pick.values() for t in v), key=tnum)
    rng('METIS-V4-召回率分包-20261007').shuffle(allp)
    packs = {f'R{k // PACK + 1:02d}': sorted(allp[k:k + PACK], key=tnum) for k in range(0, len(allp), PACK)}
    os.makedirs(a.out, exist_ok=True)
    out = {'seeds': {'抽样': 'METIS-V4-召回率抽样-20261007', '分包': 'METIS-V4-召回率分包-20261007'}, 'strata_sizes': {h: len(v) for h, v in S.items()},
           'n_per_stratum': N_PER, 'stratum_of': {t: h for h, v in pick.items() for t in v}, 'packs': packs,
           'inputs_sha256': {'kb': sha(a.kb)}}
    write(a.out, 'sample_v1.json', out)
    print(json.dumps({'strata': out['strata_sizes'], 'packs': {k: len(v) for k, v in packs.items()},
                      'per_pack_strata': {k: dict(collections.Counter(out['stratum_of'][t] for t in v)) for k, v in packs.items()}}, ensure_ascii=False))


def cmd_finder_packs(a):
    kb = json.load(open(a.kb, encoding='utf-8'))
    items = population(a.packets)
    smp = json.load(open(os.path.join(a.out, 'sample_v1.json'), encoding='utf-8'))
    extract = os.path.join(a.packets, 'K01', 'instructions.txt')
    assert sha(extract) == EXTRACT_SHA, '抽取说明与正式抽取用的不同'
    lines = open(a.corpus, encoding='utf-8').read().splitlines()
    pos = {ln.split('｜', 1)[0]: i for i, ln in enumerate(lines)}
    by = collections.defaultdict(list)
    for s in kb['steps']:
        by[s['T']].append(s)
    root = os.path.join(a.out, 'finder')
    assert not os.path.exists(root)
    man = {'packs': {}}
    for name, ts in smp['packs'].items():
        d = os.path.join(root, name)
        os.makedirs(d)
        write(d, 'instructions.txt', open(a.finder_instr, encoding='utf-8').read())
        shutil.copyfile(extract, os.path.join(d, '抽取规矩.txt'))
        body = []
        for t in ts:
            x = dict(items[t])
            x['已列步'] = [listed(s) for s in sorted(by.get(t, []), key=lambda s: s['step_id'])]
            body.append(x)
        write(d, 'pack.json', {'包': name, '倪师条目': body})
        ctx = []
        for t in ts:
            i = pos[t]
            ctx.append(f'== {t} 前后各 {CTX} 条 ==')
            ctx += [lines[j] for j in range(max(0, i - CTX), min(len(lines), i + CTX + 1)) if j != i]
        write(d, 'context.txt', '\n'.join(ctx) + '\n')
        tpl = json.load(open(os.path.join(a.packets, 'K01', 'output_template.json'), encoding='utf-8'))
        ex = {k: dict(tpl[k], 为什么不算已列步='') for k in ('定性步示例', '推理步示例')}
        write(d, 'output_template.json', {'包': name, 'items': [{'T': t, '漏步': [], '备注': ''} for t in ts], **ex})
        man['packs'][name] = {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}
    write(root, 'manifest.json', man)
    print(json.dumps({'packs': len(man['packs']), 'listed_steps': sum(len(by.get(t, [])) for ts in smp['packs'].values() for t in ts)}, ensure_ascii=False))


def cmd_adj_pack(a):
    src = os.path.join(a.out, 'finder', a.pack)
    d = os.path.join(a.out, 'adjudicate', a.pack)
    assert not os.path.exists(d)
    assert sha(a.check_instr).startswith(CHECK_SHA_PREFIX), '核查说明与正式核查用的不同'
    A = json.load(open(a.a, encoding='utf-8'))
    B = json.load(open(a.b, encoding='utf-8'))
    os.makedirs(d)
    write(d, 'instructions.txt', open(a.adj_instr, encoding='utf-8').read())
    for fn in ('pack.json', 'context.txt', '抽取规矩.txt'):
        shutil.copyfile(os.path.join(src, fn), os.path.join(d, fn))
    shutil.copyfile(a.check_instr, os.path.join(d, '核查规矩.txt'))
    write(d, '找漏甲.json', A)
    write(d, '找漏乙.json', B)
    rows = []
    for who, X in (('甲', A), ('乙', B)):
        for it in X.get('items', []):
            for k, _ in enumerate(it.get('漏步') or [], 1):
                rows.append({'来源': who, 'T': it['T'], '序号': k, '判定': '', '类型': '', '漏步号': '', '对应已列步': '', '理由': ''})
    write(d, 'output_template.json', {'包': a.pack, '裁定': rows})
    print(json.dumps({'pack': a.pack, '甲报': sum(1 for r in rows if r['来源'] == '甲'), '乙报': sum(1 for r in rows if r['来源'] == '乙')}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('sample', 'finder-packs', 'adj-pack'))
    for k in ('kb', 'packets', 'corpus', 'finder-instr', 'out', 'pack', 'a', 'b', 'check-instr', 'adj-instr'):
        ap.add_argument('--' + k)
    a = ap.parse_args()
    {'sample': cmd_sample, 'finder-packs': cmd_finder_packs, 'adj-pack': cmd_adj_pack}[a.cmd](a)


if __name__ == '__main__':
    main()
