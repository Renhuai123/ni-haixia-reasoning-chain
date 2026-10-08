"""丁 传统框架归类：统计 v1（依据《00l_三项深化方案》v2 丁）。只读存档、对象与旧归类结果，只输出统计量。
定类（主次序）：问A 为「定名」的，按问B 记「定名·象名」或「定名·义名」；为「断事」的，按 C1 象 → C3 位 → C4 时 → C2 义 → C5 情 取第一个「是」，
  五问都「否」记「直断」；该答的项缺失或不合规、而在它之前没有「是」的，记「缺失」（不进分布，计数报出）。
  第二次序（敏感性）：C1 象 → C2 义 → C3 位 → C4 时 → C5 情。
组：起步（倪海厦定性步 1314）、推理步（倪海厦推理步 371）、全书（抽样 400 句切分出的断语）。
子命令：
  pilot --returns <试编存档目录> --round N --units <trad_units_v1.json> --qs-units <qs_units_v1.json> --sample <sample_PN.json> --out …：
    两名试编者（P{N}_甲、P{N}_乙）。分起步、推理步、全书三组（富集层算进它所属的组）各看一次，下面每一项都要满足才算达标：
    问A、问B（两人都答定名的）、C1–C5（两人都答断事的）、问D、类型的原始一致率 ≥ 0.70；
    C1–C5、问D：任一试编者答「是」的条目合计 ≥ 4 条时，「是」的特定一致率 2a/(2a+b+c) ≥ 0.5；不足 4 条的记「信息不足」，不算不达标。
  final --units … --qs-units … --formal <正式材料目录> --returns <正式存档目录> --adj-returns <裁定存档目录> --old-types <types_final_v1.json>
        --pilot-samples … --out …：
    一致程度（裁定之前）：各组与倪海厦合计，问A、问B、C1–C5、问D、类型的原始一致率与 Krippendorff α（名义尺度），95% 区间按团重抽 2000 次
      （倪海厦按 T 成团，全书按句成团；种子「METIS-V4-传统框架区间-20261008」）；类型每类特定一致率；C1–C5、问D 的「是」特定一致率；
      另报剔除试编条目、00h 的 25 条审稿样例与设计者看过的 12 条起步之后的版本。
    缺失：某批缺合格的归类交卷，或有分歧却没有合格裁定卷，整批记缺失；裁定项缺失或不合规的，该条类型记「缺失」。
    结果：各组的问A 比例；定名里象名的比例；断事里各类比例（主次序与第二次序）、C1–C5 各自答「是」的比例；问D 的比例（全部、断事里）；
      倪海厦两组按适用（先天／运限）分开；起步按「结论层是否为定性」与问A 交叉；起步的盘面条件里含位置、时机要素的条数（程序判，
      只作描述）与 C3、C4 交叉；「以此类推」类说法（KEY_ANALOGY）在原话摘录或全书句中出现的条数。
    对照（只作描述）：起步对全书、起步对推理步——定名比例、定名里象名比例、断事里各类比例与问D 比例之差，95% 区间由两组各自按团重抽相减。
    与旧框架（推理步 371，只作再编码稳定性的描述，不作效度证据）：旧类型 × 新类型（主次序）交叉表；按对应（取象→象、术数机理→位或时、
      类属展开→义、性情因果→情、处境常理→情、其他→直断）的一致率；相容率（术数机理对到位、时、义都算相容）。
    解读规则（事先写定）：某组类型 α < 0.4，不报该组各类比例，对照里涉及该组的类比例差也不报；某项（问A、问B、C1–C5、问D）α < 0.4，不报它的比例；
      某类特定一致率 < 0.5，该类比例只报区间；推理步新类型 α < 0.4，或比旧五类 α（0.8662）低 0.2 以上，正文推理方式一节以旧五类为主。
用法：python3 trad_analyze_v1.py pilot …；python3 trad_analyze_v1.py final …"""
import argparse, collections, hashlib, json, os, random, re

QC = ['C1', 'C2', 'C3', 'C4', 'C5']
NAMES = {'C1': '象', 'C2': '义', 'C3': '位', 'C4': '时', 'C5': '情'}
ORDER1 = ['C1', 'C3', 'C4', 'C2', 'C5']
ORDER2 = ['C1', 'C2', 'C3', 'C4', 'C5']
TYPES = ['定名·象名', '定名·义名', '象', '位', '时', '义', '情', '直断']
GROUPS = ['起步', '推理步', '全书']
MAP_OLD = {'取象': {'象'}, '术数机理': {'位', '时'}, '类属展开': {'义'}, '性情因果': {'情'}, '处境常理': {'情'}, '其他': {'直断'}}
COMPAT = {'取象': {'象'}, '术数机理': {'位', '时', '义'}, '类属展开': {'义'}, '性情因果': {'情'}, '处境常理': {'情'}, '其他': {'直断'}}
OLD_ALPHA = 0.8662
REVIEW25 = ['T1520-c1', 'T191-c3', 'T149-c2', 'T96-c1', 'T14-c2', 'T133-c7', 'T302-c6', 'T844-c1', 'T1488-c3', 'T1097-c2', 'T505-c2', 'T92-c3', 'T848-c2',
            'T653-c2', 'T471-c3', 'T203-c2', 'T297-c1', 'T502-c3', 'T703-c2', 'T196-c3', 'T304-c2', 'T926-c1', 'T180-c2', 'T259-c2', 'T785-c6']
SEEN12 = ['T1428-c1', 'T367-c2', 'T572-c3', 'T933-c1', 'T62-c2', 'T806-c2', 'T357-c1', 'T90-c2', 'T228-c2', 'T181-c1', 'T594-c1', 'T811-c5']
KEY_ANALOGY = re.compile(r'以此类推|类推|同理|一样的道理|也是这样批|照这样推')
POS_COND = re.compile(r'亮度:|化:|对宫|三方四正|夹|格:|会照')
TIME_COND = re.compile(r'大限|流年|小限|岁')
N_BOOT = 2000
SEED = 'METIS-V4-传统框架区间-20261008'


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def v(x, allowed):
    x = str(x or '').strip()
    return x if x in allowed else None


def qa(ans):
    return v(ans.get('问A'), ('定名', '断事'))


def type_of(ans, order=ORDER1):
    a = qa(ans)
    if a is None:
        return '缺失'
    if a == '定名':
        b = v(ans.get('问B'), ('象名', '义名'))
        return f'定名·{b}' if b else '缺失'
    for q in order:
        x = v(ans.get(q), ('是', '否'))
        if x is None:
            return '缺失'
        if x == '是':
            return NAMES[q]
    return '直断'


def group(u):
    return {'倪海厦·起步': '起步', '倪海厦·推理步': '推理步', '全书': '全书'}[u['来源']]


def accepted(rdir, name):
    for nm in (name, f'{name}_重跑1', f'{name}_重跑2'):
        au = os.path.join(rdir, nm + '.audit.json')
        if os.path.exists(au) and json.load(open(au, encoding='utf-8'))['ok']:
            return nm, json.load(open(os.path.join(rdir, nm + '.json'), encoding='utf-8'))
    return None, None


def alpha(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    if not pairs:
        return None
    n = collections.Counter()
    for a, b in pairs:
        n[a] += 1; n[b] += 1
    N = 2 * len(pairs)
    Do = 2 * sum(1 for a, b in pairs if a != b)
    De = N * N - sum(x * x for x in n.values())
    if De == 0:
        return 1.0 if Do == 0 else None
    return 1 - (N - 1) * Do / De


def raw(pairs):
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    return round(sum(a == b for a, b in pairs) / len(pairs), 4) if pairs else None


def spec(pairs, cls):
    a2 = 2 * sum(1 for x, y in pairs if x == y == cls)
    bc = sum(1 for x, y in pairs if (x == cls) != (y == cls))
    return round(a2 / (a2 + bc), 4) if a2 + bc else None


def cluster_boot(units, stat, seed):
    cl = collections.OrderedDict()
    for c, x in units:
        cl.setdefault(c, []).append(x)
    keys = list(cl)
    if not keys:
        return None
    r = rng(seed)
    vals = []
    for _ in range(N_BOOT):
        s = [x for _ in keys for x in cl[keys[r.randrange(len(keys))]]]
        y = stat(s)
        if y is not None:
            vals.append(y)
    if not vals:
        return None
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 4), round(vals[int(0.975 * len(vals)) - 1], 4)]


def item_pair(A, B, key):
    if key == '问A':
        return (qa(A), qa(B))
    if key == '问B':
        return (v(A.get('问B'), ('象名', '义名')), v(B.get('问B'), ('象名', '义名'))) if qa(A) == qa(B) == '定名' else (None, None)
    if key in QC:
        return (v(A.get(key), ('是', '否')), v(B.get(key), ('是', '否'))) if qa(A) == qa(B) == '断事' else (None, None)
    if key == '问D':
        return (v(A.get('问D'), ('是', '否')), v(B.get('问D'), ('是', '否')))
    return (type_of(A), type_of(B))


def agreement_block(rows, seed):
    """rows：[(团号, 甲, 乙)]。"""
    out = {'n': len(rows)}
    for key in ['问A', '问B'] + QC + ['问D', '类型']:
        pr = [(c, item_pair(A, B, key)) for c, A, B in rows]
        ps = [p for _, p in pr if p != (None, None)]
        if not ps:
            continue
        a = alpha(ps)
        blk = {'条数': len(ps), '原始一致率': raw(ps), 'alpha': round(a, 4) if a is not None else None,
               'alpha_95%（按团重抽）': cluster_boot([(c, p) for c, p in pr if p != (None, None)], alpha, seed + '|' + key)}
        if key in QC or key == '问D':
            blk['是的特定一致率'] = spec(ps, '是')
            blk['任一人答是的条数'] = sum(1 for x, y in ps if '是' in (x, y))
        if key == '类型':
            blk['每类特定一致率'] = {t: spec(ps, t) for t in TYPES + ['缺失'] if any(t in p for p in ps)}
        out[key] = blk
    return out


def cmd_pilot(a):
    U = json.load(open(a.units, encoding='utf-8'))
    Q = json.load(open(a.qs_units, encoding='utf-8'))['条目']
    units = {u['编号']: u for u in U['ni'] + Q}
    _, A = accepted(a.returns, f'P{a.round}_甲')
    _, B = accepted(a.returns, f'P{a.round}_乙')
    assert A and B, '试编交卷不全'
    a_ = {x['编号']: x for x in A['归类']}
    b_ = {x['编号']: x for x in B['归类']}
    res, ok_all = {'round': a.round, 'n': len(a_)}, True
    for g in GROUPS:
        ids = [i for i in a_ if group(units[i]) == g]
        blk = {'n': len(ids)}
        for key in ['问A', '问B'] + QC + ['问D', '类型']:
            ps = [item_pair(a_[i], b_[i], key) for i in ids]
            ps = [p for p in ps if p != (None, None)]
            if not ps:
                blk[key] = '无可比条目'; continue
            r_ = raw(ps)
            it = {'原始一致率': r_, '达标': r_ >= 0.70}
            if key in QC or key == '问D':
                ny = sum(1 for x, y in ps if '是' in (x, y))
                it['任一人答是的条数'] = ny
                if ny >= 4:
                    sp = spec(ps, '是')
                    it['是的特定一致率'] = sp
                    it['达标'] = it['达标'] and sp is not None and sp >= 0.5
                else:
                    it['是的特定一致率'] = '信息不足'
            ok_all = ok_all and it['达标']
            blk[key] = it
        res[g] = blk
    res['达标'] = ok_all
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'round': a.round, '达标': ok_all, **{g: {k: (x['原始一致率'] if isinstance(x, dict) else x) for k, x in res[g].items() if k != 'n'} for g in GROUPS}}, ensure_ascii=False))


def dist_block(rows, seed, order_name='主次序'):
    """rows：[(团号, 最终答案, 类型)]，已去掉缺失。"""
    n = len(rows)
    out = {'n': n}
    if not n:
        return out
    prop = lambda s, f: (sum(1 for x in s if f(x)) / len(s)) if s else None
    out['问A·定名比例'] = {'条数': sum(1 for _, A, _ in rows if qa(A) == '定名'), '比例': round(prop(rows, lambda x: qa(x[1]) == '定名'), 4),
                        '95%': cluster_boot([(c, (A, t)) for c, A, t in rows], lambda s: prop(s, lambda x: qa(x[0]) == '定名'), seed + '|定名')}
    dm = [(c, A, t) for c, A, t in rows if qa(A) == '定名']
    if dm:
        out['定名里象名比例'] = {'条数': sum(1 for _, _, t in dm if t == '定名·象名'), 'n': len(dm), '比例': round(prop(dm, lambda x: x[2] == '定名·象名'), 4),
                           '95%': cluster_boot([(c, t) for c, _, t in dm], lambda s: prop(s, lambda x: x == '定名·象名'), seed + '|象名')}
    ds = [(c, A, t) for c, A, t in rows if qa(A) == '断事']
    out['断事条数'] = len(ds)
    if ds:
        out['断事里各类'] = {}
        for t in ['象', '位', '时', '义', '情', '直断']:
            out['断事里各类'][t] = {'条数': sum(1 for *_, x in ds if x == t), '比例': round(prop(ds, lambda x: x[2] == t), 4),
                                 '95%': cluster_boot([(c, x) for c, _, x in ds], lambda s, t=t: prop(s, lambda y: y == t), seed + '|' + t)}
        t2 = [type_of(A, ORDER2) for _, A, _ in ds]
        out['断事里各类·第二次序'] = {t: {'条数': t2.count(t), '比例': round(t2.count(t) / len(t2), 4)} for t in ['象', '义', '位', '时', '情', '直断']}
        out['断事里C1–C5答是'] = {}
        for q in QC:
            out['断事里C1–C5答是'][NAMES[q]] = {'是': sum(1 for _, A, _ in ds if v(A.get(q), ('是', '否')) == '是'), '比例': round(prop(ds, lambda x: v(x[1].get(q), ('是', '否')) == '是'), 4),
                                            '95%': cluster_boot([(c, A) for c, A, _ in ds], lambda s, q=q: prop(s, lambda y: v(y.get(q), ('是', '否')) == '是'), seed + '|' + q)}
        out['断事里问D明说道理'] = {'是': sum(1 for _, A, _ in ds if v(A.get('问D'), ('是', '否')) == '是'), '比例': round(prop(ds, lambda x: v(x[1].get('问D'), ('是', '否')) == '是'), 4),
                              '95%': cluster_boot([(c, A) for c, A, _ in ds], lambda s: prop(s, lambda y: v(y.get('问D'), ('是', '否')) == '是'), seed + '|D断事')}
    out['问D明说道理·全部'] = {'是': sum(1 for _, A, _ in rows if v(A.get('问D'), ('是', '否')) == '是'), '比例': round(prop(rows, lambda x: v(x[1].get('问D'), ('是', '否')) == '是'), 4)}
    return out


def diff_ci(r1, r2, f, seed):
    def draws(rows, sd):
        cl = collections.OrderedDict()
        for c, x in rows:
            cl.setdefault(c, []).append(x)
        keys = list(cl)
        r = rng(sd)
        out = []
        for _ in range(N_BOOT):
            s = [x for _ in keys for x in cl[keys[r.randrange(len(keys))]]]
            out.append(f(s))
        return out
    d1, d2 = draws(r1, seed + '|1'), draws(r2, seed + '|2')
    vv = sorted(x - y for x, y in zip(d1, d2) if x is not None and y is not None)
    return [round(vv[int(0.025 * len(vv))], 4), round(vv[int(0.975 * len(vv)) - 1], 4)] if vv else None


def cmd_final(a):
    U = json.load(open(a.units, encoding='utf-8'))
    Q = json.load(open(a.qs_units, encoding='utf-8'))['条目']
    units = {u['编号']: u for u in U['ni'] + Q}
    clus = {i: (u['T'] if u['来源'] != '全书' else u['句编号']) for i, u in units.items()}
    batches = json.load(open(os.path.join(a.formal, 'batches.json'), encoding='utf-8'))['batches']
    excl = set(REVIEW25) | set(SEEN12)
    for f in a.pilot_samples or []:
        excl |= set(json.load(open(f, encoding='utf-8'))['units'])
    used, missing = {}, []
    coder, final, adj = {}, {}, collections.Counter()
    for b in batches:
        name = b['batch']
        na, A = accepted(a.returns, f'{name}_甲')
        nb, B = accepted(a.returns, f'{name}_乙')
        if not (A and B):
            missing.append(name); continue
        a_ = {x['编号']: x for x in A['归类']}
        b_ = {x['编号']: x for x in B['归类']}
        need = any(item_pair(a_[i], b_[i], k)[0] != item_pair(a_[i], b_[i], k)[1] for i in b['units'] for k in ['问A', '问B'] + QC + ['问D'])
        nd, D = accepted(a.adj_returns, name)
        if need and not D:
            missing.append(name); continue
        used[name] = [na, nb, nd]
        rulings, whole = collections.defaultdict(dict), {}
        for x in (D or {}).get('裁定', []):
            if x.get('项') == '整条':
                whole[x['编号']] = x
            else:
                rulings[x['编号']][x['项']] = x
        for i in b['units']:
            coder[i] = (a_[i], b_[i])
            if qa(a_[i]) != qa(b_[i]):
                final[i] = whole.get(i, {}); adj['整条'] += 1; continue
            fa = dict(a_[i])
            keys = (['问B'] if qa(a_[i]) == '定名' else QC) + ['问D']
            for k in keys:
                x, y = item_pair(a_[i], b_[i], k)
                if x != y or x is None:
                    r = rulings.get(i, {}).get(k)
                    fa[k] = r.get('裁定') if r else None
                    adj['逐项'] += 1
            final[i] = fa
    res = {'schema': 'trad-final-v1', '缺失的批': missing, '采用的交卷': used, '裁定': dict(adj), '一致程度·全部': {}, '一致程度·剔除试编与看过的': {}, '分布': {}}
    rows_all = [(clus[i], group(units[i]), *coder[i], i) for i in coder]
    for gname, sel in [('倪海厦合计', ('起步', '推理步')), ('起步', ('起步',)), ('推理步', ('推理步',)), ('全书', ('全书',))]:
        rs = [(c, A, B) for c, g, A, B, i in rows_all if g in sel]
        res['一致程度·全部'][gname] = agreement_block(rs, SEED + '|一致|' + gname)
        rs2 = [(c, A, B) for c, g, A, B, i in rows_all if g in sel and i not in excl]
        res['一致程度·剔除试编与看过的'][gname] = agreement_block(rs2, SEED + '|一致剔|' + gname)
    ftype = {i: type_of(final[i]) for i in final}
    res['类型缺失的条目'] = sorted(i for i, t in ftype.items() if t == '缺失')
    for g in GROUPS:
        rows = [(clus[i], final[i], ftype[i]) for i in final if group(units[i]) == g and ftype[i] != '缺失']
        res['分布'][g] = dist_block(rows, SEED + '|分布|' + g)
        if g != '全书':
            for apn, ap in [('先天', ('先天',)), ('运限', ('大限', '流年', '小限'))]:
                rr = [(clus[i], final[i], ftype[i]) for i in final if group(units[i]) == g and units[i]['适用'] in ap and ftype[i] != '缺失']
                res['分布'][f'{g}·{apn}'] = dist_block(rr, SEED + f'|分布|{g}|{apn}')
    qi = [i for i in final if group(units[i]) == '起步' and ftype[i] != '缺失']
    res['起步·问A×结论层是否定性'] = {str(lay): dict(collections.Counter(qa(final[i]) for i in qi if (units[i]['结论']['层'] == '定性') == lay)) for lay in (True, False)}
    pos = lambda u: bool(POS_COND.search(' '.join(u.get('盘面条件', []))))
    tim = lambda u: u['适用'] != '先天' or bool(TIME_COND.search(' '.join(u.get('盘面条件', []))))
    ds = [i for i in qi if qa(final[i]) == '断事']
    res['起步断事·盘面条件含位置要素×C3'] = {str(p): dict(collections.Counter(v(final[i].get('C3'), ('是', '否')) for i in ds if pos(units[i]) == p)) for p in (True, False)}
    res['起步断事·含时机要素×C4'] = {str(p): dict(collections.Counter(v(final[i].get('C4'), ('是', '否')) for i in ds if tim(units[i]) == p)) for p in (True, False)}
    res['以此类推类说法'] = {g: sorted(i for i in final if group(units[i]) == g and KEY_ANALOGY.search(units[i].get('原话摘录') or units[i].get('所在句', ''))) for g in GROUPS}

    def rows_of(g):
        return [(clus[i], (final[i], ftype[i])) for i in final if group(units[i]) == g and ftype[i] != '缺失']
    res['对照'] = {}
    for g1, g2 in [('起步', '全书'), ('起步', '推理步')]:
        r1, r2 = rows_of(g1), rows_of(g2)
        fs = {'定名比例': lambda s: (sum(1 for A, t in s if qa(A) == '定名') / len(s)) if s else None,
              '定名里象名比例': lambda s: (lambda d: sum(1 for t in d if t == '定名·象名') / len(d) if d else None)([t for A, t in s if qa(A) == '定名']),
              '断事里问D比例': lambda s: (lambda d: sum(1 for A in d if v(A.get('问D'), ('是', '否')) == '是') / len(d) if d else None)([A for A, t in s if qa(A) == '断事'])}
        for t in ['象', '位', '时', '义', '情', '直断']:
            fs[f'断事里{t}比例'] = (lambda t: lambda s: (lambda d: sum(1 for x in d if x == t) / len(d) if d else None)([x for A, x in s if qa(A) == '断事']))(t)
        blk = {}
        for nm, f in fs.items():
            p1, p2 = f([x for _, x in r1]), f([x for _, x in r2])
            blk[nm] = {g1: round(p1, 4) if p1 is not None else None, g2: round(p2, 4) if p2 is not None else None,
                       '差': round(p1 - p2, 4) if None not in (p1, p2) else None, '差的95%': diff_ci(r1, r2, f, SEED + f'|对照|{g1}|{g2}|{nm}')}
        res['对照'][f'{g1}对{g2}'] = blk
    old = json.load(open(a.old_types, encoding='utf-8'))['最终类型']
    inf = [i for i in final if group(units[i]) == '推理步' and ftype[i] != '缺失']
    ct = collections.defaultdict(collections.Counter)
    for i in inf:
        ct[old[i]][ftype[i]] += 1
    res['与旧框架（再编码稳定性，不作效度证据）'] = {'n': len(inf), '交叉表（行=旧，列=新）': {k: dict(x) for k, x in ct.items()},
                                         '按对应的一致率': round(sum(ftype[i] in MAP_OLD[old[i]] for i in inf) / len(inf), 4) if inf else None,
                                         '相容率': round(sum(ftype[i] in COMPAT[old[i]] for i in inf) / len(inf), 4) if inf else None}
    res['各类前两例'] = {g: {t: sorted((i for i in final if group(units[i]) == g and ftype[i] == t),
                                     key=lambda i: (int(units[i]['T'][1:]) if 'T' in units[i] else 0, i))[:2] for t in TYPES} for g in GROUPS}
    rules = {}
    for g in GROUPS:
        blk = res['一致程度·全部'][g]
        rules[g] = {'类型alpha<0.4': (blk.get('类型', {}).get('alpha') or 0) < 0.4,
                    'alpha<0.4的项': [k for k in ['问A', '问B'] + QC + ['问D'] if k in blk and (blk[k]['alpha'] or 0) < 0.4],
                    '特定一致率<0.5的类': [t for t, x in blk.get('类型', {}).get('每类特定一致率', {}).items() if x is not None and x < 0.5]}
    na = res['一致程度·全部']['推理步'].get('类型', {}).get('alpha') or 0
    rules['推理步以旧五类为主'] = na < 0.4 or na < OLD_ALPHA - 0.2
    res['解读规则'] = rules
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'缺失的批': missing, '裁定': dict(adj), '类型缺失': len(res['类型缺失的条目']),
                      '类型alpha': {g: res['一致程度·全部'][g].get('类型', {}).get('alpha') for g in res['一致程度·全部']},
                      '与旧框架一致率': res['与旧框架（再编码稳定性，不作效度证据）']['按对应的一致率']}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=('pilot', 'final'))
    ap.add_argument('--round', type=int)
    ap.add_argument('--pilot-samples', nargs='*')
    for k in ('returns', 'units', 'qs-units', 'sample', 'out', 'formal', 'adj-returns', 'old-types'):
        ap.add_argument('--' + k)
    a = ap.parse_args()
    {'pilot': cmd_pilot, 'final': cmd_final}[a.cmd](a)


if __name__ == '__main__':
    main()
