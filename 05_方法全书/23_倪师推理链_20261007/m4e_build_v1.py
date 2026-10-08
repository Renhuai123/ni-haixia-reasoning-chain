"""M4e 认本人检验（推理链）：建题 v1（依据《00h_三项补充研究方案_v2.md》甲）。只打印编号与计数，不打印陈述或论断内容。
题目、陈述文件、陪衬人选、A–D 次序、输出模板从前作 M4（m4_v1）原样沿用：逐字节复制并核对 SHA-256。
三组论断（每组 28 题 × 4 份）：
- 链组 judge_packets_链：第四版引擎（ni_chain_engine_v1.infer_candidates）推理，m4e_render_v1.render_chain_m4e 成稿；
- 平铺组 judge_packets_平：同一份推理结果，m4e_render_v1.render_flat_m4e 成稿；
- 第三版先天组 judge_packets_三：第三版（ni_engine_v3，规则库与 M4d 相同）cite=False 成稿，m4e_render_v1.v3_natal 只取先天四节。
剔除（每题一套，四份论断、三组共用）：R = {T：T 的时段（起点到起点后 WIN 秒）与四位当事人任一讲述时段有重叠} ∪ 本题陈述的源 T 表。
第四版剔除出处在 R 里的步；第三版剔除出处在 R 里的规则，《取舍规则表》的步骤凡所引 T 全在 R 里的关掉（同 M4c、M4d，只把「落在时段内」换成 R）。
另核对：R 包含 M4d 的剔除（前作按起点判的时段内规则全在 R 里）。
候选盘：两版都只留各候选都推出的结论（第四版 infer_candidates、第三版 read_candidates 都按同一宫取交集）；各候选身宫不同的人，身宫不作标注（打印人数）。
泄露核对（违者停）：第四版每份论断的推理结果里，每个结点的每一种推法用到的步，出处都不在 R 里；
第三版每份论断用到的规则出处都不在 R 里，并用 cite=True 重出一次，先天四节引用的 T 除引擎写死的方法出处 ENGINE_T 之外都不在 R 里
（ENGINE_T：算子 T10、T294、T313、T317、T977，地支论病 T1052、T1053、T1058；它们是两版引擎共用的看盘方法，不是哪个人的论断）。
另写（只作描述，审者开跑之前算）：describe_m4e_v1.json——每份论断的行数、字数、判断条数、候选盘张数；每题四份论断两两的 Jaccard 重合度；
每份论断与本题陈述的 4 字相同片段：片段数、有相同片段的陈述条数。
写出 <out>/judge_packets_{链,平,三}/Mxx/、<out>/key_m4e_v1.json、<out>/manifest.json、<out>/describe_m4e_v1.json；目录已存在就停。
用法：python3 m4e_build_v1.py --m4 <m4_v1> --kb <chain_kb_v1.json> --v3kb <倪师层> --v3kb-qs <全书补层> --persons <m3_statements_merged_v1.json>
      --corpus <ni_corpus.txt> --sources <陈述源T表> --instr-dir <三份审者说明所在目录> --out <新目录>"""
import argparse, itertools, json, os, re, shutil, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE); sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E
import ni_engine_v3 as V3
import m4e_render_v1 as RD
from m4_build_v2 import run_charts, write, body_text, sha
from m4d_build_v1 import table_steps, GUARDED

WIN = 60
ARMS = ('链', '平', '三')
INSTR = {arm: f'm4e_judge_instructions_{arm}_v1.txt' for arm in ARMS}
TREF = re.compile(r'（(T\d+)')
ENGINE_T = {'T10', 'T294', 'T313', 'T317', 'T977', 'T1052', 'T1053', 'T1058'}
norm = lambda s: re.sub(r'[\s\W_]+', '', s)


def span_hit(P, tm, segs):
    m = re.match(r'P(\d+)', str(P))
    if not m or not tm:
        return False
    t = E.secs(tm)
    return any(int(g['分P']) == int(m.group(1)) and t <= g['end_s'] and t + WIN >= g['start_s'] for g in segs)


def judgment_lines(text):
    """论断里写判断的行（去掉节标题与总标题），用于计条数、找相同片段。"""
    out = []
    for ln in text.split('\n'):
        if ln.startswith('  '):
            body = ln.strip()
            body = body.split('：', 1)[1] if '：' in body else body
            out.append(body)
    return out


def count_judgments(arm, text):
    n = 0
    for b in judgment_lines(text):
        if arm == '链':
            n += 0 if b.startswith('盘面 →') else 1
        else:
            n += len([x for x in b.split('；') if x.strip()])
    return n


def grams4(s):
    s = norm(s)
    return {s[i:i + 4] for i in range(len(s) - 3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('m4', 'kb', 'v3kb', 'v3kb-qs', 'persons', 'corpus', 'sources', 'instr-dir', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    nodes, steps = C.load_kb(a.kb)
    by_id = {s['step_id']: s for s in steps}
    dead = set(RD.death_nodes(nodes))
    rules = E.load_rules([a.v3kb, a.v3kb_qs])
    persons = {p['person_id']: p for p in json.load(open(a.persons, encoding='utf-8'))['persons']}
    key = json.load(open(os.path.join(a.m4, 'key_v1.json'), encoding='utf-8'))
    man = json.load(open(os.path.join(a.m4, 'manifest.json'), encoding='utf-8'))
    src = json.load(open(a.sources, encoding='utf-8'))
    corpus = {}
    for ln in open(a.corpus, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜')
        corpus[t[0]] = (t[1], t[2])
    tab = table_steps()
    allT = sorted({t for v in tab.values() for t in v})
    need = sorted({c for v in key['items'].values() for c in v['letters'].values()})
    rows = run_charts({f"{pid}#{i}": b['form'] for pid in need for i, b in enumerate(persons[pid]['candidates'])})
    cand_rows = {pid: [rows[f'{pid}#{i}'] for i in range(len(persons[pid]['candidates']))] for pid in need}
    for pid, rs in cand_rows.items():
        assert all('error' not in r for r in rs), pid
    instr = {arm: open(os.path.join(a.instr_dir, INSTR[arm]), encoding='utf-8').read() for arm in ARMS}
    os.makedirs(a.out)
    newkey = {'seed_m4': key['seed'], 'derived_from': 'm4_v1/key_v1.json', 'items': {},
              'inputs_sha256': {'chain_kb': sha(a.kb), 'v3kb': sha(a.v3kb), 'v3kb_qs': sha(a.v3kb_qs), 'persons': sha(a.persons), 'corpus': sha(a.corpus),
                                'sources': sha(a.sources), 'render': sha(os.path.join(HERE, 'm4e_render_v1.py')), 'engine_v4': sha(os.path.join(HERE, 'ni_chain_engine_v1.py')),
                                'engine_v3': sha(os.path.join(E_DIR, 'ni_engine_v3.py')), 'build': sha(os.path.abspath(__file__)),
                                **{f'instructions_{arm}': sha(os.path.join(a.instr_dir, INSTR[arm])) for arm in ARMS}},
              'death_nodes': sorted(dead)}
    newman = {'schema': 'm4e-packets-v1', 'arms': {arm: [] for arm in ARMS}}
    desc = {'说明': '审者开跑之前算的描述量；不含任何审者结果', 'items': {}}
    shen_unsure = set()
    for pk in man['judge_packs']:
        (iid,) = pk['items']
        v = key['items'][iid]
        owners = [v['letters'][L] for L in 'ABCD']
        segs = [g for c in owners for g in persons[c]['segments']]
        R = {T for T, (P, tm) in corpus.items() if span_hit(P, tm, segs)}
        src_extra = set(src['items'][iid]['源T']) - R
        R |= set(src['items'][iid]['源T'])
        # 第三版：剔除出处在 R 里的规则；核对 R 包含 M4d 的剔除
        rs_m4d, _ = E.leave_out(rules, segs)
        rs = [r for r in rules if r['T'] not in R]
        assert {r['rule_id'] for r in rs} <= {r['rule_id'] for r in rs_m4d}, (iid, 'R 没有包含 M4d 的剔除')
        hitT = {t for t in allT if t in R}
        disabled = sorted(sid for sid, ts in tab.items() if ts and all(t in hitT for t in ts))
        assert set(disabled) <= GUARDED, (iid, '要关的步骤没有开关', sorted(set(disabled) - GUARDED))
        # 第四版：剔除出处在 R 里的步
        allowed = {s['step_id'] for s in steps if s['T'] not in R}
        dirs = {arm: os.path.join(a.out, f'judge_packets_{arm}', pk['pack']) for arm in ARMS}
        srcdir = os.path.join(a.m4, 'judge_packets', pk['pack'])
        for arm, d in dirs.items():
            os.makedirs(d)
            write(d, 'instructions.txt', instr[arm])
            for fn in ('output_template.json', f'{iid}_陈述.txt'):
                shutil.copyfile(os.path.join(srcdir, fn), os.path.join(d, fn))
                assert sha(os.path.join(d, fn)) == pk['files_sha256'][fn], (iid, fn)
        stmt = open(os.path.join(srcdir, f'{iid}_陈述.txt'), encoding='utf-8').read().split('\n')
        stmt = [re.sub(r'^\d+\. （[^）]*）', '', x) for x in stmt if x.strip()]
        sg = [grams4(x) for x in stmt]
        d_item = {'R_T数': len(R), '源T在时段之外另剔的T数': len(src_extra), '第四版剔除步数': len(steps) - len(allowed),
                  '第三版剔除规则数': len(rules) - len(rs), '关掉的取舍步骤': disabled, '各份': {}, 'Jaccard': {}}
        sets = {arm: {} for arm in ARMS}
        genders = {}
        for L, c in v['letters'].items():
            charts = [E.Chart(r) for r in cand_rows[c]]
            gs = {ch.gender for ch in charts}
            genders[L] = gs.pop() if len(gs) == 1 else None
            shens = {ch.shen for ch in charts}
            shen = shens.pop() if len(shens) == 1 else None
            if shen is None:
                shen_unsure.add(c)
            der = C.infer_candidates(cand_rows[c], nodes, steps, allowed=allowed)
            used = {x['step'] for dp in der.values() for xs in dp.values() for x in xs}
            assert not {by_id[s]['T'] for s in used} & R, (iid, L, '第四版论断用到了 R 里的步')
            texts = {'链': RD.render_chain_m4e(der, nodes, by_id, shen, dead), '平': RD.render_flat_m4e(der, nodes, shen, dead)}
            rd, rby = V3.read_candidates(cand_rows[c], rs)
            syn = V3.synthesize(rd, rby, charts, disabled)
            texts['三'] = RD.v3_natal(V3.render_text_v3(rd, rby, syn, cite=False))
            assert not {rby[h['rule']]['T'] for part in ('natal', 'daxian', 'liunian') for h in rd[part]} & R, (iid, L, '第三版论断用到了 R 里的规则')
            cited = set(TREF.findall(RD.v3_natal(V3.render_text_v3(rd, rby, syn, cite=True)))) - ENGINE_T
            assert not cited & R, (iid, L, '第三版先天四节引用了 R 里的 T')
            sets['链'][L] = sets['平'][L] = RD.judgment_set_v4(der, dead)
            sets['三'][L] = {(h['palace'], h['rule']) for h in rd['natal']}
            for arm in ARMS:
                write(dirs[arm], f'{iid}_论断{L}.txt', body_text(texts[arm]))
                rg = set().union(*(grams4(x) for x in judgment_lines(texts[arm]))) if judgment_lines(texts[arm]) else set()
                d_item['各份'][f'{arm}{L}'] = {'owner_is_true': c == v['person'], '候选盘': len(charts), '行数': texts[arm].count('\n'),
                                              '字数': len(norm(texts[arm])), '判断条数': count_judgments(arm, texts[arm]),
                                              '与陈述相同的4字片段数': len(rg & set().union(*sg)) if sg else 0,
                                              '有相同片段的陈述条数': sum(1 for g in sg if g & rg)}
        for arm in ARMS:
            js = [len(sets[arm][x] & sets[arm][y]) / len(sets[arm][x] | sets[arm][y]) if sets[arm][x] | sets[arm][y] else 1.0
                  for x, y in itertools.combinations('ABCD', 2)]
            d_item['Jaccard'][arm] = round(statistics.mean(js), 4)
        desc['items'][iid] = d_item
        newkey['items'][iid] = dict(v, R_T=sorted(R, key=lambda x: int(x[1:])), disabled_steps=disabled, genders=genders)
        for arm, d in dirs.items():
            newman['arms'][arm].append({'pack': pk['pack'], 'items': [iid], 'files_sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    desc['各候选身宫不一的人'] = sorted(shen_unsure)
    write(a.out, 'key_m4e_v1.json', newkey)
    write(a.out, 'manifest.json', newman)
    write(a.out, 'describe_m4e_v1.json', desc)
    tot = {arm: sum(x['字数'] for it in desc['items'].values() for k, x in it['各份'].items() if k.startswith(arm)) for arm in ARMS}
    print(json.dumps({'items': len(newkey['items']), '各组总字数': tot, '各候选身宫不一的人数': len(shen_unsure),
                      '源T另剔': {i: x['源T在时段之外另剔的T数'] for i, x in desc['items'].items() if x['源T在时段之外另剔的T数']},
                      '关掉的取舍步骤': {i: x['关掉的取舍步骤'] for i, x in desc['items'].items() if x['关掉的取舍步骤']}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
