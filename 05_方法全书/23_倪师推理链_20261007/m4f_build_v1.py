"""M4f 认本人检验（独立陪衬、统一陈述、两种对照）：建题 v1（依据《00l_三项深化方案》v2 戊）。只打印编号与计数，不打印陈述或论断内容。
题目：前作 M4 的 28 位本人（题号同 m4_v1）。每题有三组：
  正题    ：陈述 = 本人 i 的 K 条；论断 = 本人盘 + 陪衬盘 1–3；
  换陈述组：陈述 = 另一位本人 π(i) 的 K 条；论断与正题逐字相同；
  换论断组：陈述 = 本人 i 的 K 条（与正题相同）；论断 = 另一位本人 π′(i) 的盘（「他人真盘」）+ 陪衬盘 1–3（与正题相同）。
  每组的「焦点论断」：正题与换陈述组是本人盘那份，换论断组是他人真盘那份。
陈述：pick_statements——池 = 类别不是「其他」、性质不是「无法判断」的陈述；先取不带年龄的，再取带年龄的；
  每组里按固定的类别次序 CAT_ORDER 轮取，类内对象为「本人」的在前、再按 SHA-256(种子|人|原序号) 升序；取满 K 条为止；不足 K 条的用全部。
陪衬盘：与本人同一候选结构（同样张数；各候选的性别相同；农历日的相差相同）、同五行局；年份 1920–1995、月、时、起始日按种子随机；
  每份依次试第 0、1、2……次抽签，取第一张合规的：排盘无误、五行局相同、规范化后的（农历年、月、日、时辰）与任何真人候选盘都不同、
  与本题已取的陪衬盘也都不同。
π、π′：28 人上的两个错位排列（种子各一）：不配给自己；不配给同八字的人；两人性别都确定时须同性别；π′(i) ≠ π(i)。
  用按种子定次序的回溯求得（derange）。
剔除：R(X) = {T：T 的时段（起点到起点后 WIN 秒）与 X 或与 X 同八字者的任一讲述时段有重叠} ∪ X 与其同八字者那一题陈述的源 T 表；
  R_i = R(i) ∪ R(π(i)) ∪ R(π′(i))。本题全部五份论断（本人、陪衬 1–3、他人真盘）都用剔除 R_i 后的知识库推理，多候选盘按 cand_closure_v1 闭合取交集。
内容泄露核对（不依赖剔除集）：每份论断用到的每一步，其出处 T 的原话全文与本题出现的两份陈述（i 与 π(i)）的原话（去掉空白与标点）
  若有 NGRAM 字以上相同的连续片段，就把这个 T 并入 R_i、重推本题全部论断，直到没有为止；并入的 T 记进答案表。
  另核对（违者停）：最终每份论断用到的步，出处都不在 R_i 里。
成稿：m4e_render_v1.render_chain_m4e（字段白名单、涉生死改提醒，与 M4e 链组相同）。
审者：每题每组 J 名（--judges）；每名审者一个包，包号按种子打乱、不透露组别；每包四份论断的 A–D 次序各自按种子打乱。
另写（只作描述，审者开跑之前算）：describe_m4f_v1.json——每份论断的字数、判断条数；本人论断是否严格最长；每份陪衬盘与本人
  「命宫主星组合相同」「十四主星排布相同（紫微与命宫同在一地支）」；每题四份两两 Jaccard；每份论断与两份陈述的 4 字相同片段数。
写出 <out>/packets/Jxxx/、<out>/key_m4f_v1.json、<out>/manifest.json、<out>/describe_m4f_v1.json；目录已存在就停。
用法：python3 m4f_build_v1.py --m4 <m4_v1> --kb <chain_kb_v1.json> --persons <m3_statements_merged_v1.json> --corpus <ni_corpus.txt>
      --sources <statement_source_T_v1.json> --instr <m4f_judge_instructions_v1.txt> --judges 2 --out <新目录>"""
import argparse, hashlib, itertools, json, os, random, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE); sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E
import m4e_render_v1 as RD
import cand_closure_v1 as CC
from m4_build_v2 import run_charts, write, body_text, sha

WIN = 60
NGRAM = 8
K = 6
TRIES = 60
YEARS = (1920, 1995)
ARMS = ('正', '换陈述', '换论断')
CAT_ORDER = ['个性', '长相', '行为', '路线', '成就', '婚姻', '财', '健康', '意外', '官非', '迁移', '父母', '兄弟', '子女', '朋友']
SEED_STMT = 'METIS-M4f-陈述-20261008'
SEED_DECOY = 'METIS-M4f-陪衬-20261008'
SEED_PI = 'METIS-M4f-负对照-20261008'
SEED_PI2 = 'METIS-M4f-换论断-20261008'
SEED_LETTER = 'METIS-M4f-字母-20261008'
SEED_PACK = 'METIS-M4f-包号-20261008'
norm = lambda s: re.sub(r'[\s\W_]+', '', str(s))
h16 = lambda s: int(hashlib.sha256(s.encode('utf-8')).hexdigest()[:16], 16)


def rng(seed):
    return random.Random(h16(seed))


def span_hit(P, tm, segs):
    m = re.match(r'P(\d+)', str(P))
    if not m or not tm:
        return False
    t = E.secs(tm)
    return any(int(g['分P']) == int(m.group(1)) and t <= g['end_s'] and t + WIN >= g['start_s'] for g in segs)


def pick_statements(pid, sts):
    pool = [(k, s) for k, s in enumerate(sts, 1) if s['类别'] != '其他' and s['性质'] != '无法判断']
    assert all(s['类别'] in CAT_ORDER for _, s in pool), sorted({s['类别'] for _, s in pool} - set(CAT_ORDER))
    chosen = []
    for grp in ([x for x in pool if not (x[1]['年龄'] or '').strip()], [x for x in pool if (x[1]['年龄'] or '').strip()]):
        cats = {}
        for k, s in grp:
            cats.setdefault(s['类别'], []).append((k, s))
        for c in cats:
            cats[c].sort(key=lambda x: (x[1]['对象'] != '本人', h16(f'{SEED_STMT}|{pid}|{x[0]}')))
        order = [c for c in CAT_ORDER if c in cats]
        while len(chosen) < K and any(cats.values()):
            for c in order:
                if cats[c] and len(chosen) < K:
                    chosen.append(cats[c].pop(0)[0])
    return sorted(chosen), len(pool)


def stmt_text(sts, picked):
    return ''.join(f"{n}. （对象：{sts[k - 1]['对象'] or '未说'}；年龄：{sts[k - 1]['年龄'] or '未说'}）{' '.join(str(sts[k - 1]['内容']).split())}\n"
                   for n, k in enumerate(picked, 1))


def structure(person):
    fs = [c['form'] for c in person['candidates']]
    assert len({(f['year'], f['month'], f['clockHour'], f['calendarType'], f['isLeapMonth']) for f in fs}) == 1, person['person_id']
    assert fs[0]['calendarType'] == 'lunar' and not fs[0]['isLeapMonth']
    d0 = min(int(f['day']) for f in fs)
    return [(int(f['day']) - d0, f['gender']) for f in fs]


def ymdh(f):
    """规范化：（农历年、月、日、时辰序号）。"""
    return (int(f['year']), int(f['month']), int(f['day']), (int(f['clockHour']) + 1) % 24 // 2)


def decoy_forms(iid, j, t, struct):
    r = rng(f'{SEED_DECOY}|{iid}|{j}|{t}')
    year = r.randint(*YEARS)
    month = r.randint(1, 12)
    hour = r.randrange(12)
    maxd = max(dd for dd, _ in struct)
    base = r.randint(1, 29 - maxd)
    return [{'calendarType': 'lunar', 'isLeapMonth': False, 'longitude': 120, 'unknownTime': False, 'city': '', 'province': '', 'name': '',
             'year': str(year), 'month': str(month), 'day': str(base + dd), 'clockHour': str(2 * hour), 'clockMinute': '0', 'gender': g}
            for dd, g in struct]


def derange(targets, gender, same, seed, avoid=None):
    """按种子定次序的回溯：本人按题号次序，各人的候选名单按 SHA-256(种子|本人|候选) 升序；取第一个合规的完整排列。"""
    ok = lambda p, q: p != q and (p, q) not in same and not (gender[p] and gender[q] and gender[p] != gender[q]) and not (avoid and avoid[p] == q)
    cands = {p: sorted((q for q in targets if ok(p, q)), key=lambda q: h16(f'{seed}|{p}|{q}')) for p in targets}
    out, used = {}, set()

    def go(k):
        if k == len(targets):
            return True
        p = targets[k]
        for q in cands[p]:
            if q not in used:
                out[p] = q; used.add(q)
                if go(k + 1):
                    return True
                used.discard(q); del out[p]
        return False
    if not go(0):
        raise SystemExit('找不到合规的错位排列')
    return dict(out)


def judgment_lines(text):
    out = []
    for ln in text.split('\n'):
        if ln.startswith('  '):
            body = ln.strip()
            out.append(body.split('：', 1)[1] if '：' in body else body)
    return out


def grams(s, k):
    s = norm(s)
    return {s[i:i + k] for i in range(len(s) - k + 1)}


def chart_shape(rows):
    ch = E.Chart(rows[0])
    b = ch.by_name['命宫']['branch']
    return tuple(sorted(ch.majors_in(b))), ch.star_at.get('紫微'), b


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('m4', 'kb', 'persons', 'corpus', 'sources', 'instr', 'out'):
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--judges', type=int, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    nodes, steps = C.load_kb(a.kb)
    by_id = {s['step_id']: s for s in steps}
    dead = set(RD.death_nodes(nodes))
    M = json.load(open(a.persons, encoding='utf-8'))
    persons = {p['person_id']: p for p in M['persons']}
    same = {tuple(x) for x in M['same_bazi_pairs']} | {tuple(reversed(x)) for x in M['same_bazi_pairs']}
    partners = {}
    for x, y in same:
        partners.setdefault(x, set()).add(y)
    key = json.load(open(os.path.join(a.m4, 'key_v1.json'), encoding='utf-8'))
    src = json.load(open(a.sources, encoding='utf-8'))
    corpus, ctext = {}, {}
    for ln in open(a.corpus, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜', 4)
        corpus[t[0]] = (t[1], t[2]); ctext[t[0]] = t[4]
    instr = open(a.instr, encoding='utf-8').read()
    items = sorted(key['items'])
    tgt = {iid: key['items'][iid]['person'] for iid in items}
    iid_of = {p: i for i, p in tgt.items()}
    targets = [tgt[i] for i in items]
    rows = run_charts({f'{p}#{k}': c['form'] for p in targets for k, c in enumerate(persons[p]['candidates'])})
    cand = {p: [rows[f'{p}#{k}'] for k in range(len(persons[p]['candidates']))] for p in targets}
    assert all('error' not in r for rs in cand.values() for r in rs)
    gender = {p: ({r['birth']['gender'] for r in rs}.pop() if len({r['birth']['gender'] for r in rs}) == 1 else None) for p, rs in cand.items()}
    ju = {}
    for p, rs in cand.items():
        js = {r['chart']['wuxingJu'] for r in rs}
        assert len(js) == 1, p
        ju[p] = js.pop()
    real = {ymdh(c['form']) for p in persons.values() for c in p['candidates']}
    struct = {p: structure(persons[p]) for p in targets}
    forms = {}
    for iid in items:
        for j in (1, 2, 3):
            for t in range(TRIES):
                for k, f in enumerate(decoy_forms(iid, j, t, struct[tgt[iid]])):
                    forms[f'{iid}|{j}|{t}|{k}'] = f
    drows = run_charts(forms)
    decoys, tries_used = {}, {}
    for iid in items:
        p = tgt[iid]
        taken = set()
        for j in (1, 2, 3):
            for t in range(TRIES):
                rs = [drows[f'{iid}|{j}|{t}|{k}'] for k in range(len(struct[p]))]
                fs = [forms[f'{iid}|{j}|{t}|{k}'] for k in range(len(struct[p]))]
                if any('error' in r for r in rs) or {r['chart']['wuxingJu'] for r in rs} != {ju[p]}:
                    continue
                keys = {ymdh(f) for f in fs}
                if keys & real or keys & taken:
                    continue
                decoys[(iid, j)] = (rs, fs); tries_used[f'{iid}|{j}'] = t; taken |= keys
                break
            assert (iid, j) in decoys, (iid, j, '抽签用完仍无合规陪衬盘')
    picks = {p: pick_statements(p, persons[p]['statements']) for p in targets}
    stext = {p: stmt_text(persons[p]['statements'], picks[p][0]) for p in targets}
    pi = derange(targets, gender, same, SEED_PI)
    pi2 = derange(targets, gender, same, SEED_PI2, avoid=pi)

    def R_of(p):
        group = {p} | partners.get(p, set())
        segs = [g for q in group for g in persons[q]['segments']]
        out = {T for T, (P, tm) in corpus.items() if span_hit(P, tm, segs)}
        for q in group:
            if q in iid_of:
                out |= set(src['items'][iid_of[q]]['源T'])
        return out
    Rx = {p: R_of(p) for p in targets}
    os.makedirs(os.path.join(a.out, 'packets'))
    newkey = {'schema': 'm4f-key-v1', 'K': K, 'judges_per_arm': a.judges, 'arms': list(ARMS), 'NGRAM': NGRAM,
              'seeds': {'陈述': SEED_STMT, '陪衬': SEED_DECOY, '换陈述': SEED_PI, '换论断': SEED_PI2, '字母': SEED_LETTER, '包号': SEED_PACK},
              'inputs_sha256': {'m4_key': sha(os.path.join(a.m4, 'key_v1.json')), 'chain_kb': sha(a.kb), 'persons': sha(a.persons), 'corpus': sha(a.corpus),
                                'sources': sha(a.sources), 'instructions': sha(a.instr), 'render': sha(os.path.join(HERE, 'm4e_render_v1.py')),
                                'engine_v4': sha(os.path.join(HERE, 'ni_chain_engine_v1.py')), 'closure': sha(os.path.join(HERE, 'cand_closure_v1.py')),
                                'build': sha(os.path.abspath(__file__))},
              'death_nodes': sorted(dead), 'pi': {iid_of[p]: iid_of[q] for p, q in pi.items()}, 'pi2': {iid_of[p]: iid_of[q] for p, q in pi2.items()},
              'items': {}, 'packets': {}}
    desc = {'说明': '审者开跑之前算的描述量；不含任何审者结果', 'items': {}}
    texts_all = {}
    for iid in items:
        p, q, q2 = tgt[iid], pi[tgt[iid]], pi2[tgt[iid]]
        R = Rx[p] | Rx[q] | Rx[q2]
        sg = grams(stext[p] + stext[q], NGRAM)
        sg_full = set()
        for s_ in (persons[p]['statements'], persons[q]['statements']):
            for st in s_:
                sg_full |= grams(st.get('原话', ''), NGRAM)
        added = []
        owners = {'本人': cand[p], '陪衬1': decoys[(iid, 1)][0], '陪衬2': decoys[(iid, 2)][0], '陪衬3': decoys[(iid, 3)][0], '他人真盘': cand[q2]}
        for _round in range(50):
            allowed = {s['step_id'] for s in steps if s['T'] not in R}
            ders, hitT = {}, set()
            for o, rs in owners.items():
                der = CC.infer_candidates_closed(rs, nodes, steps, allowed=allowed)
                ders[o] = der
                used = {x['step'] for dp in der.values() for xs in dp.values() for x in xs}
                Ts = {by_id[s]['T'] for s in used}
                assert not Ts & R, (iid, o, '论断用到了 R 里的步')
                hitT |= {T for T in Ts if grams(ctext[T], NGRAM) & (sg | sg_full)}
            if not hitT:
                break
            added += sorted(hitT - R); R |= hitT
        else:
            raise SystemExit(f'{iid} 内容泄露核对 50 轮仍不收敛')
        texts, sets, info = {}, {}, {}
        for o, rs in owners.items():
            charts = [E.Chart(r) for r in rs]
            shens = {ch.shen for ch in charts}
            assert len(shens) == 1, (iid, o, '各候选身宫不一')
            texts[o] = body_text(RD.render_chain_m4e(ders[o], nodes, by_id, shens.pop(), dead))
            sets[o] = RD.judgment_set_v4(ders[o], dead)
        texts_all[iid] = texts
        g_own = [grams(x, 4) for x in stext[p].split('\n') if x.strip()]
        g_neg = [grams(x, 4) for x in stext[q].split('\n') if x.strip()]
        shp = chart_shape(cand[p])
        for o, tx in texts.items():
            jl = judgment_lines(tx)
            rg = set().union(*(grams(x, 4) for x in jl)) if jl else set()
            info[o] = {'字数': len(norm(tx)), '判断条数': sum(0 if b.startswith('盘面 →') else 1 for b in jl),
                       '与本人陈述相同4字片段': len(rg & set().union(*g_own)) if g_own else 0, '与换陈述组陈述相同4字片段': len(rg & set().union(*g_neg)) if g_neg else 0}
            if o.startswith('陪衬'):
                ds = chart_shape(owners[o])
                info[o]['命宫主星组合与本人相同'] = ds[0] == shp[0]
                info[o]['十四主星排布与本人相同'] = ds[1] == shp[1] and ds[2] == shp[2]
        quad = ['本人', '陪衬1', '陪衬2', '陪衬3']
        js = [len(sets[x] & sets[y]) / len(sets[x] | sets[y]) if sets[x] | sets[y] else 1.0 for x, y in itertools.combinations(quad, 2)]
        longest = [o for o in quad if info[o]['字数'] == max(info[x]['字数'] for x in quad)]
        desc['items'][iid] = {'本人': p, '换陈述组陈述来自': iid_of[q], '换论断组论断来自': iid_of[q2], 'R_T数': len(R), '内容核对并入的T': added,
                              '剔除步数': len(steps) - len({s['step_id'] for s in steps if s['T'] not in R}), '候选盘张数': len(cand[p]),
                              '陈述池条数': picks[p][1], '陈述条数': len(picks[p][0]),
                              '陈述带年龄条数': sum(1 for k in picks[p][0] if (persons[p]['statements'][k - 1]['年龄'] or '').strip()),
                              '各份': info, 'Jaccard均值（正题四份）': round(statistics.mean(js), 4), '本人论断严格最长': longest == ['本人'],
                              '陪衬抽签次数': [tries_used[f'{iid}|{j}'] for j in (1, 2, 3)]}
        newkey['items'][iid] = {'person': p, 'gender': gender[p], 'ju': ju[p], 'structure': struct[p], 'statements_picked': picks[p][0],
                                '换陈述_person': q, '换论断_person': q2, 'R_T': sorted(R, key=lambda x: int(x[1:])), '内容核对并入的T': added,
                                'decoy_forms': {f'陪衬{j}': decoys[(iid, j)][1] for j in (1, 2, 3)}}
    jobs = [(arm, iid, r) for arm in ARMS for iid in items for r in range(1, a.judges + 1)]
    order = jobs[:]
    rng(SEED_PACK).shuffle(order)
    man = {'schema': 'm4f-packets-v1', 'packets': []}
    for n, (arm, iid, r) in enumerate(order, 1):
        pk = f'J{n:03d}'
        focal = '他人真盘' if arm == '换论断' else '本人'
        own = [focal, '陪衬1', '陪衬2', '陪衬3']
        rng(f'{SEED_LETTER}|{arm}|{iid}|{r}').shuffle(own)
        letters = dict(zip('ABCD', own))
        d = os.path.join(a.out, 'packets', pk)
        os.makedirs(d)
        write(d, 'instructions.txt', instr)
        p = tgt[iid]
        write(d, '题01_陈述.txt', stext[pi[p]] if arm == '换陈述' else stext[p])
        for L, o in letters.items():
            write(d, f'题01_论断{L}.txt', texts_all[iid][o])
        write(d, 'output_template.json', {'包': pk, '答案': [{'题': '题01', '最符合': '', '排序': ['', '', '', ''], '理由': {L: '' for L in 'ABCD'}}]})
        newkey['packets'][pk] = {'arm': arm, 'item': iid, 'judge': r, 'letters': letters, 'focal': focal, 'focal_letter': next(L for L, o in letters.items() if o == focal)}
        man['packets'].append({'pack': pk, 'files_sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    write(a.out, 'key_m4f_v1.json', newkey)
    write(a.out, 'manifest.json', man)
    write(a.out, 'describe_m4f_v1.json', desc)
    D = desc['items'].values()
    print(json.dumps({'items': len(items), 'packets': len(order), '陈述不足K的题': {i: x['陈述条数'] for i, x in desc['items'].items() if x['陈述条数'] < K},
                      '陈述总条数': sum(x['陈述条数'] for x in D), '带年龄的陈述': {i: x['陈述带年龄条数'] for i, x in desc['items'].items() if x['陈述带年龄条数']},
                      '本人论断严格最长的题数': sum(x['本人论断严格最长'] for x in D),
                      '字数中位': {o: statistics.median(x['各份'][o]['字数'] for x in D) for o in ('本人', '陪衬1', '陪衬2', '陪衬3', '他人真盘')},
                      '含十四主星排布相同陪衬的题': [i for i, x in desc['items'].items() if any(x['各份'][f'陪衬{j}']['十四主星排布与本人相同'] for j in (1, 2, 3))],
                      '含命宫主星组合相同陪衬的题数': sum(any(x['各份'][f'陪衬{j}']['命宫主星组合与本人相同'] for j in (1, 2, 3)) for x in D),
                      '内容核对并入T的题': {i: len(x['内容核对并入的T']) for i, x in desc['items'].items() if x['内容核对并入的T']},
                      '陪衬抽签次数最大': max(tries_used.values()), 'π': newkey['pi'], 'π′': newkey['pi2']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
