"""引擎第二版·综合取舍 A 组：路线、成就（本人）。照《取舍规则表》A 组裁定结果实现（v2_principles_v1/returns/A_裁定.json，已登记）。
步骤编号「A路6」「A成5」＝A 组·属性·第几步，与裁定表 R1（路线）、R2（成就）的「步」一一对应；通则 G1–G12 已体现在各步里。
实现中不得不做的技术选择，逐条记在《16》技术选择记录里（代码里标「技术选择」）。"""
import collections

from v2_synth_common import Contest, soft, all_charts, cond_has_ji, cond_has_sha, cond_named_stars, conds, SIX_SHA, E

ROUTES = ['当官', '武职', '经商', '受雇', '专业']
PAIRS_R = [(v, '非' + v) for v in ROUTES] + [('当官', '经商'), ('武职', '经商'), ('受雇', '经商'), ('武职', '非当官')]
DOUBT_R = [('武职', '受雇'), ('武职', '专业')]           # 倪师没讲能不能并存，写两说（A路1）
HYPO = {'T136-r2', 'T180-r2'}                              # A路2(a) 假设语气
NOLU = {'T191-r2': '本宫', 'T638-r1': '本宫', 'T471-r1': '命宫三方四正', 'T951-r2': '命宫三方四正'}   # A路2(b)
WU_STARS = ('七杀', '破军', '贪狼', '廉贞', '武曲')        # A路2(c)
SUN_GUAN = {'T51-r1', 'T52-r3', 'T61-r1'}                  # A路2(d)
EITHER = {'T432-r1', 'T571-r1'}                            # A路3：只证明受雇、经商二者之一
OUTSIDE = {'T593-r1', 'T596-r1'}                           # 只讲外地，写成「到外地：X」
GUANLU_NONE = {'T639-r1', 'T641-r1'}                       # A路4
GE_R = {'T790-r1': ('武职',), 'T785-r1': ('当官',), 'T715-r3': ('当官',), 'T259-r1': ('武职',), 'T260-r1': ('武职',), 'T838-r1': ('武职',),
        'T794-r1': ('经商',), 'T800-r1': ('经商',), 'T817-r1': None, 'T715-r2': ('经商',), 'T936-r1': ('经商',), 'T942-r1': ('经商',),
        'T943-r1': ('经商',), 'T951-r1': ('经商',), 'T572-r2': ('经商',), 'T782-r1': ('经商', '专业')}
QUANLU = {'T715-r2', 'T936-r1', 'T942-r1', 'T943-r1', 'T951-r1', 'T572-r2', 'T782-r1'}   # 权禄、禄马
EXTRA_TYPES = {'化', '位化', '亮度', '宫支', '身宫', '性别'}   # A路5「具体的说法优先」认的多出条件

PREMISE = {'当官': {'T327-r1', 'T623-r1', 'T628-r3', 'T630-r1', 'T949-r1'}, '武职': {'T136-r2', 'T153-r1', 'T231-r1', 'T232-r1', 'T233-r1', 'T238-r2'},
           '经商': {'T180-r2'}}                            # A成2
GE_A = {'T785-r1', 'T791-r2', 'T715-r3', 'T785-r2', 'T790-r2', 'T791-r1', 'T259-r3', 'T794-r1', 'T802-r2', 'T936-r2', 'T231-r1', 'T232-r1', 'T233-r1'}
ZUOCAI = {'T213-r1', 'T214-r2', 'T214-r3', 'T215-r2', 'T216-r1', 'T284-r1', 'T924-r1', 'T925-r1'}   # A成7


# ---------------- 命盘上的判断（并列候选都要成立） ----------------
def pal_b(ch, name):
    return ch.by_name[name]['branch']


def sfsz(b):
    return {b % 12, (b + 4) % 12, (b + 8) % 12, (b + 6) % 12}


def has_lu(ch, b):
    """这一宫有禄：禄存或化禄（G8：禄存与化禄同论）。"""
    return '禄存' in ch.stars_in(b) or any(ch.hua(s) == '禄' for s in ch.stars_in(b))


def lucun_in(ctx, s, where):
    def f(ch):
        b = pal_b(ch, s['宫']) if where == '本宫' else None
        bs = {b} if where == '本宫' else sfsz(pal_b(ch, '命宫'))
        return any('禄存' in ch.stars_in(x) for x in bs)
    return all_charts(ctx.charts, f)


def stars_fallen(ctx, stars):
    """技术选择：点名的几颗星全部落陷才算「落陷」（与 B 组同一口径）。"""
    return bool(stars) and all_charts(ctx.charts, lambda ch: all(ch.level(x) == '陷' for x in stars))


def any_star_ji(ctx, stars):
    return bool(stars) and all_charts(ctx.charts, lambda ch: any(ch.hua(x) == '忌' for x in stars))


def level_of(ctx, s):
    """A路7、A成6：格级、四化级、星级。T690-r1（本宫有财星）只有命中宫确有化禄或禄存才算四化级。"""
    r = ctx.rule(s)
    if s['规则'] == 'T690-r1':
        return '四化' if all_charts(ctx.charts, lambda ch: has_lu(ch, pal_b(ch, s['宫']))) else '星'
    if any(c['t'] in ('化', '位化') for c in conds(r)) or any(c['t'] == '有无' and c['has'] and '禄存' in c['stars'] for c in conds(r)):
        return '四化'
    return '星'


def quan_kind(ctx, s):
    """A路8：化权写明是哪颗星（化:X=权，或本宫有某星且本宫化权）→ 'star'；只写位置化权 → 'pos'；不涉化权 → None。"""
    r = ctx.rule(s)
    if any(c['t'] == '化' and c['hua'] == '权' for c in conds(r)):
        return 'star'
    pos = [c for c in conds(r) if c['t'] == '位化' and '权' in c['hua'] and c.get('has', True)]
    if not pos:
        return None
    if any(c['where'] == '本宫' for c in pos) and cond_named_stars(r):
        return 'star'
    return 'pos'


def more_specific(ctx, sa, sb):
    """A路5：同一宫，sa 的条件包含 sb 的全部条件，多出来的全是四化、亮度、宫支、身宫、性别条件 → sa 更具体。
    技术选择：多出来的条件必须全是这几类才算（较严，少取舍）。"""
    if sa['宫'] != sb['宫']:
        return False
    A, B = E.atoms(ctx.rule(sa)), E.atoms(ctx.rule(sb))
    if not B < A:
        return False
    import json as _j
    return all(_j.loads(x)['t'] in EXTRA_TYPES for x in A - B)


def specific_step(c, ctx, sid):
    lose = set()
    for a, b in c.conflicts():
        for sa in c.support[a]:
            for sb in c.support[b]:
                if more_specific(ctx, sa, sb):
                    lose.add((b, id(sb)))
                elif more_specific(ctx, sb, sa):
                    lose.add((a, id(sa)))
    if lose:
        c.remove_statements(sid, lambda v, x: (v, id(x)) in lose, note='具体的说法优先')


EXC_R = {frozenset(p) for p in PAIRS_R}     # 规则表「互斥」表里的对子（写两说的 DOUBT_R 不算）


def is_ge_route(ctx, x):
    """A路6 的格清单（含各条的成立条件）。"""
    rid = x['规则']
    if rid not in GE_R:
        return False
    if rid == 'T715-r3' and x['宫'] not in ('命宫', '官禄', '迁移'):
        return False
    if rid == 'T800-r1' and 'T794-r1' not in {y['规则'] for y in ctx.ev if y['时间层'] == '先天'}:
        return False
    if rid == 'T572-r2':   # 财星是禄存或化禄时才算权禄
        return all_charts(ctx.charts, lambda ch: has_lu(ch, pal_b(ch, x['宫'])))
    return True


def tier(ctx, x, ge_pred):
    """G4 三级：格级 3、四化级 2、星级 1。"""
    if ge_pred(x):
        return 3
    return 2 if level_of(ctx, x) == '四化' else 1


def tiered_step(c, ctx, ge_pred, sid7, sid8, exc):
    """A路7、A路8（G4）：先在四化级内部按「化权看是哪颗星」剔除位置化权的说法，定出四化级的结果（已定的、两说的）；
    再处理只有星级说法的取值：与已定的四化级取值互斥（且不是已冻结的两说）→ 淘汰；与四化级两说的双方都互斥 → 淘汰。
    有格级说法的取值不被下级淘汰（格级已在 A路6 处理）。技术选择：第8步排在第7步的淘汰之前，以便先定四化级内部。"""
    top = lambda v: max((tier(ctx, x, ge_pred) for x in c.support[v]), default=0)
    # 四化级内部：化权看是哪颗星
    lose = set()
    for a, b in c.conflicts():
        if top(a) == 2 and top(b) == 2:
            ka = {quan_kind(ctx, x) for x in c.support[a]}
            kb = {quan_kind(ctx, x) for x in c.support[b]}
            if 'star' in ka:
                lose |= {(b, id(x)) for x in c.support[b] if quan_kind(ctx, x) == 'pos'}
            if 'star' in kb:
                lose |= {(a, id(x)) for x in c.support[a] if quan_kind(ctx, x) == 'pos'}
    if lose:
        c.remove_statements(sid8, lambda v, x: (v, id(x)) in lose, note='化权看是哪颗星')
    al = c.alive()
    V4 = [v for v in al if top(v) == 2]
    S = [v for v in al if top(v) == 1]
    tied4 = [(a, b) for i, a in enumerate(V4) for b in V4[i + 1:] if frozenset((a, b)) in c.pairs]
    fixed4 = [v for v in V4 if not any(v in p for p in tied4)]
    out = {}
    for v in S:
        by = next((f for f in fixed4 if frozenset((v, f)) in exc and frozenset((v, f)) not in c.frozen), None)
        if by is None:
            by = next((p for p in tied4 if frozenset((v, p[0])) in exc and frozenset((v, p[1])) in exc), None)
        if by is not None:
            out[v] = by
    for v, by in out.items():
        c.out[v] = (sid7, by if isinstance(by, str) else '／'.join(by), '四化优先')
    if out:
        c.log.append((sid7, sorted((k, str(v)) for k, v in out.items())))


def borrowed_freeze(c, sid):
    """两说③：借对宫求得的命中和本宫实有之星的命中互斥，写两说（倪师没讲借对宫的分量）。"""
    for a, b in c.conflicts():
        ba = {x['借对宫'] for x in c.support[a]}
        bb = {x['借对宫'] for x in c.support[b]}
        if (ba == {True} and bb == {False}) or (ba == {False} and bb == {True}):
            c.freeze(sid, a, b, '借对宫的命中对本宫实有之星的命中，写两说')


# ---------------- 路线（裁定表 R1） ----------------
def route_items(ctx, layer):
    out = []
    for s in ctx.ev:
        vals = [v for a, v in s['claims'] if a == '路线']
        if not vals or s['时间层'] != layer:
            continue
        if layer == '先天':
            pal, rg, via = s['宫'], s['规则宫'], s['推导']
            ok = (via.startswith('身宫规则') or pal in ('命宫', '官禄') or (pal == '财帛' and rg == '财帛')
                  or (pal == '迁移' and rg in ('迁移', '任一宫')))
        else:
            ok = True
        if ok:
            out.append((s, vals))
    return out


def route_contest(ctx, items, layer):
    notes, outside, either, drop = [], [], [], []
    sup = collections.defaultdict(list)
    for s, vals in items:
        rid = s['规则']
        if rid in HYPO:
            notes.append(('A路2', f"假设语气，不当路线证据：{s['内容']}", [s['T']])); drop.append(('A路2', s)); continue
        if rid in NOLU and lucun_in(ctx, s, '本宫' if NOLU[rid] == '本宫' else '三方四正'):
            notes.append(('A路2', f"条件要靠无化禄，而范围里有禄存，不当证据：{s['内容']}", ['T333'])); drop.append(('A路2', s)); continue
        if rid in SUN_GUAN and stars_fallen(ctx, ['太阳']):
            notes.append(('A路2', f"太阳落陷，不当官、武职证据：{s['内容']}", ['T68'])); drop.append(('A路2', s)); continue
        r = ctx.rule(s)
        if s['原方向'] == '吉' and any_star_ji(ctx, cond_named_stars(r)):
            notes.append(('A路2', f"所依的星本身化忌，不当证据：{s['内容']}", ['T965'])); drop.append(('A路2', s)); continue
        if soft(s):
            continue          # G2：修正后不再为凶的凶断，不当否定的证据
        if rid in OUTSIDE:    # 第2步各款与修正检查之后再分流（只讲外地，写成「到外地：X」）
            outside += [(v, s) for v in vals]; continue
        if rid in EITHER:     # A路3：只证明受雇、经商二者之一
            either.append(s); continue
        if rid == 'T817-r1':  # A路3：命宫、财帛都有禄取经商，否则武职
            both = all_charts(ctx.charts, lambda ch: has_lu(ch, pal_b(ch, '命宫')) and has_lu(ch, pal_b(ch, '财帛')))
            vals = ['经商'] if both else ['武职']
        elif rid == 'T715-r2':
            vals = ['经商']
        for v in vals:
            if v == '武职':
                rel = [x for x in cond_named_stars(r) if x in WU_STARS]
                if rel and stars_fallen(ctx, rel):
                    notes.append(('A路2', f"所依的武官星落陷，不当武职证据：{s['内容']}", ['T90', 'T196', 'T314'])); drop.append(('A路2', s)); continue
            sup[v].append(s)
    c = Contest(sup, PAIRS_R + DOUBT_R)
    for a, b in DOUBT_R:
        c.freeze('A路1', a, b, '倪师没讲能不能并存，写两说')
    # A路4：官禄空宫，借对宫的当官让位给 T639-r1、T641-r1 的不会当官
    if layer == '先天' and any(x['规则'] in GUANLU_NONE for x in c.support.get('非当官', [])) and \
            all_charts(ctx.charts, lambda ch: not ch.majors_in(pal_b(ch, '官禄'))):
        c.remove_statements('A路4', lambda v, x: v == '当官' and x['宫'] == '官禄' and x['借对宫'], note='官带不进来')
    borrowed_freeze(c, 'A路4')
    specific_step(c, ctx, 'A路5')
    ge_step_route(c, ctx, layer)
    tiered_step(c, ctx, lambda x: is_ge_route(ctx, x), 'A路7', 'A路8', EXC_R)
    res = c.result()
    if either and not ({'受雇', '经商'} & set(res['主断'])) and not any({'受雇', '经商'} & set(p) for p in res['两说']):
        res.setdefault('两说另列', []).append(('受雇', '经商', 'A路3', ['T432', 'T571', 'T561'], either, either))
    res.setdefault('两说另列', [])
    for v in res['主断']:
        if ctx.on('A路9') and c.support[v] and all(x['宫'] == '迁移' for x in c.support[v]):
            notes.append(('A路9', f'{v}之说都出自迁移宫，指外地', ['T589']))
    res.update({'附注': notes, '外地': outside, 'contest': c, '不取': drop, '二者之一': either})
    return res


def ge_step_route(c, ctx, layer):
    """A路6：格先定。格和格互斥时，权禄、禄马（经商）对当官、武职取经商，其余写两说；
    格定下的取值，和它互斥（只认规则表的互斥表）的非格取值整条让位；格这一级是两说的，只剔除和两说双方都互斥的。已冻结的两说不越过。"""
    gv = {v: [x for x in ss if is_ge_route(ctx, x)] for v, ss in c.support.items() if v not in c.out}
    gv = {v: ss for v, ss in gv.items() if ss}
    if not gv:
        return
    lost, two, held = set(), [], []
    vs = sorted(gv)
    for i, a in enumerate(vs):
        for b in vs[i + 1:]:
            k = frozenset((a, b))
            if k in c.frozen:          # 已冻结的两说（借对宫、倪师未讲）：不取舍，但算作格级两说（实现复核 A 新问题1）
                held.append((a, b)); continue
            if k not in EXC_R:
                continue
            qa = a == '经商' and any(x['规则'] in QUANLU for x in gv[a])
            qb = b == '经商' and any(x['规则'] in QUANLU for x in gv[b])
            if qa and b in ('当官', '武职'):
                lost.add(b)
            elif qb and a in ('当官', '武职'):
                lost.add(a)
            else:
                two.append((a, b))
    for v in lost:
        c.out[v] = ('A路6', '经商', '权禄、禄马之格对当官、武职，取经商')
    tied = [p for p in two if p[0] not in lost and p[1] not in lost]
    for a, b in tied:
        c.freeze('A路6', a, b, '格与格互斥，写两说')
    tied += [p for p in held if p[0] not in lost and p[1] not in lost]
    fixed = [v for v in gv if v not in lost and not any(v in p for p in tied)]
    for v in c.alive():
        if v in gv:
            continue
        hit = any(frozenset((v, f)) in EXC_R and frozenset((v, f)) not in c.frozen for f in fixed) or \
            any(frozenset((v, p[0])) in EXC_R and frozenset((v, p[1])) in EXC_R and
                frozenset((v, p[0])) not in c.frozen and frozenset((v, p[1])) not in c.frozen for p in tied)
        if hit:
            c.out[v] = ('A路6', None, '格先定，互斥的非格命中让位')
    c.log.append(('A路6', sorted(gv)))


# ---------------- 成就（裁定表 R2） ----------------
def ach_items(ctx, layer):
    out = []
    for s in ctx.ev:
        vals = [v for a, v in s['claims'] if a == '成就']
        if not vals or s['时间层'] != layer:
            continue
        if layer == '先天':
            pal, rg, via = s['宫'], s['规则宫'], s['推导']
            ok = (via.startswith('身宫规则') or pal in ('命宫', '官禄') or (pal == '财帛' and rg == '财帛') or (pal == '迁移' and rg == '迁移'))
        else:
            ok = True
        if ok:
            out.append((s, vals))
    return out


def weak_low(s, r):
    """A成1：修正后已经不是凶的低命中不算低的证据——同宫紫微可解（T10）、杀星入庙凶处藏吉（T313）、同宫有吉星杀力减弱（T294），
    裁定表 R2 第1步原文三者并列。化忌引出的低，算子若以入庙为由减轻，不采用这一修正（A成3）。"""
    notes = ' '.join(s['算子'])
    if cond_has_ji(r) and 'T313' in notes and 'T10' not in notes and 'T294' not in notes:
        return False
    return soft(s) or 'T294' in notes


def ge_a(ctx, x):
    rid = x['规则']
    if rid not in GE_A or (rid == 'T715-r3' and x['宫'] not in ('命宫', '官禄')):
        return False
    if rid == 'T802-r2' and 'T794-r1' not in {y['规则'] for y in ctx.ev if y['时间层'] == '先天'}:
        return False
    return True


def zang(ctx, x):
    """所在宫另有落陷的六杀或化忌（吉处藏凶）。"""
    def f(ch):
        b = pal_b(ch, x['宫'])
        return any(ch.level(y) == '陷' for y in set(ch.stars_in(b)) & set(SIX_SHA)) or any(ch.hua(y) == '忌' for y in ch.stars_in(b))
    return all_charts(ctx.charts, f)


def ach_contest(ctx, items, layer, route_main, route_two, span=None):
    """route_main：该层可用的路线主断；route_two：该层路线两说里出现的取值。"""
    notes, cond_two, drop = [], [], []
    sup = collections.defaultdict(list)
    natal_rules = {x['规则'] for x in ctx.ev if x['时间层'] == '先天'}
    for s, vals in items:
        rid, r = s['规则'], ctx.rule(s)
        if '低' in vals and weak_low(s, r):
            vals = [v for v in vals if v != '低']
            if not vals:
                continue
        # A成3：所依的星落陷或化忌，不算高（放在前提分流之前，若走的高同样要过这一关）
        if '高' in vals:
            st = cond_named_stars(r)
            if (st and (stars_fallen(ctx, st) or any_star_ji(ctx, st))) or (rid == 'T802-r2' and 'T794-r1' not in natal_rules):
                if st and (stars_fallen(ctx, st) or any_star_ji(ctx, st)):
                    notes.append(('A成3', f"所依的星落陷或化忌，不算高：{s['内容']}", ['T199', 'T965'])); drop.append(('A成3', s))
                vals = [v for v in vals if v != '高']
                if not vals:
                    continue
        # A成2：以路线为前提的
        prem = [k for k, ids in PREMISE.items() if rid in ids]
        if prem:
            k = prem[0]
            if k in route_main:
                pass
            elif k in route_two:
                cond_two += [(k, v, s) for v in vals]; continue
            else:
                notes.append(('A成2', f"以{k}为前提，路线不含{k}，不算：{s['内容']}", [s['T']])); drop.append(('A成2', s)); continue
        # 取值关系·可并存：T1317-r2 不论哪一限都不算冲突，只记「早年好运不延续」；T1317-r1 记为求学期的高
        if rid == 'T1317-r2':
            notes.append(('A成·可并存', '早年好运不延续（毕业以后当不上主管），不当后面各限的低', ['T1317'])); continue
        if rid == 'T1317-r1':
            notes.append(('A成·可并存', '这一段的高只在求学期（读书时当班长、主管）', ['T1317']))
        for v in vals:
            sup[v].append(s)
    c = Contest(sup, [('高', '低')])
    borrowed_freeze(c, 'A成·两说②')
    specific_step(c, ctx, 'A成4')
    # A成5：格先定。格宫另坐落陷的六杀或化忌（吉处藏凶）→ 两说⑤，后面各步也定不了；大限走到格宫而地空、地劫也会到 → 本步不定
    def dx_kongjie():
        return layer == '大限' and span and not all_charts(ctx.charts, lambda ch: not ({'地空', '地劫'} & {y for b in sfsz(span[2]) for y in ch.stars_in(b)}))
    if '高' in c.alive() and '低' in c.alive() and frozenset(('高', '低')) not in c.frozen:
        ges = [x for x in c.support['高'] if ge_a(ctx, x)]
        good = [x for x in ges if not zang(ctx, x)]
        if good and not dx_kongjie():
            for x in c.support['低']:
                if (cond_has_ji(ctx.rule(x)) or cond_has_sha(ctx.rule(x))) and x['方向'] == '凶':
                    notes.append(('A成5', f"格高带灾星：{x['内容']}", ['T821']))
            c.out['低'] = ('A成5', '高', '格先定')
            c.log.append(('A成5', [('低', '高')]))
        elif ges and not good:
            c.freeze('A成5', '高', '低', '格宫有落陷的杀星或化忌，吉处藏凶，写两说')
    # A成6：四化优先。有格级说法的一方不被下级淘汰；一方有四化级说法、另一方只有星级说法，剔除星级一方
    if '高' in c.alive() and '低' in c.alive() and frozenset(('高', '低')) not in c.frozen:
        lv = {v: {('格' if ge_a(ctx, x) else level_of(ctx, x)) for x in c.support[v]} for v in ('高', '低')}
        for a, b in (('高', '低'), ('低', '高')):
            if '格' not in lv[a] and '格' not in lv[b] and '四化' in lv[a] and lv[b] == {'星'}:
                c.out[b] = ('A成6', a, '四化优先'); c.log.append(('A成6', [(b, a)])); break
    # A成7：看有没有权
    if '高' in c.alive() and '低' in c.alive() and frozenset(('高', '低')) not in c.frozen and \
            all(x['规则'] in ZUOCAI for x in c.support['低']) and not route_two and ({'当官', '武职'} & set(route_main)):
        sihua_quan = ctx.sihua_star('权')
        base = (lambda ch: sfsz(span[2])) if (layer == '大限' and span) else (lambda ch: sfsz(pal_b(ch, '命宫')))
        if sihua_quan and all_charts(ctx.charts, lambda ch: ch.star_at.get(sihua_quan) in base(ch)):
            c.out['低'] = ('A成7', '高', '三方四正有化权')
        else:
            c.out['高'] = ('A成7', '低', '三方四正没有化权')
        c.log.append(('A成7', []))
    res = c.result()
    # A成3、G7：照算的高（主断或两说里的），所在宫另有落陷的杀星或化忌，附注吉处藏凶
    shown = set(res['主断']) | {v for p in res['两说'] for v in p}
    zs = sorted({x['规则'] for k, v, x in cond_two if v == '高' and zang(ctx, x)})
    if '高' in shown:
        zs = sorted(set(zs) | {x['规则'] for x in c.support['高'] if zang(ctx, x)})
    if zs:
        notes.append(('A成3', f"吉处藏凶：高的命中（{'、'.join(zs)}）所在宫另有落陷的杀星或化忌", ['T1516', 'T1519']))
    res.update({'附注': notes, '两说另列': [], '若走': cond_two, 'contest': c, '不取': drop})
    return res


def route_and_achievement(ctx):
    rn = route_contest(ctx, route_items(ctx, '先天'), '先天')
    r_main, r_two = set(rn['主断']), {v for p in rn['两说'] for v in p} | {v for t in rn['两说另列'] for v in t[:2]}
    an = ach_contest(ctx, ach_items(ctx, '先天'), '先天', r_main, r_two - r_main)
    R = {'属性': '路线', '对象': '本人', '先天': rn, '大限': []}
    A = {'属性': '成就', '对象': '本人', '先天': an, '大限': []}
    for s, e, pb in ctx.daxian_spans():
        ri = route_items(ctx, '大限'); ri = [(x, v) for x, v in ri if x['岁段'] == (s, e)]
        ai_all = [(x, v) for x, v in ach_items(ctx, '大限') if x['岁段'] == (s, e)]
        ai = [(x, v) for x, v in ai_all if x['规则'] != 'T407-r3']     # 时间层③：讲限后的，记在止岁之后，不算本限的高
        dr = route_contest(ctx, ri, '大限') if ri else None
        notes_r, notes_a = [], []
        if dr:
            same = set(dr['主断']) & r_main
            other = [v for v in dr['主断'] if any(frozenset((v, m)) in EXC_R for m in r_main)]
            if same:
                notes_r.append(('A路·时间层②', '本限加强：' + '、'.join(sorted(same)), ['T772']))
            if other:
                notes_r.append(('A路·时间层②', '一生主断' + '、'.join(sorted(r_main)) + '；本限另说' + '、'.join(other), ['T772', 'T836']))
            if e <= 23:
                notes_r.append(('A路·时间层③', '止岁在 23 岁以内，只算求学期，不当就业路线', ['T1316', 'T1317', 'T837']))
            if s >= 72 and '武职' in dr['主断']:
                notes_r.append(('A路·时间层④', '72 岁以后才到，不必劝他当武官', ['T1336']))
        avail_main = r_main | (set(dr['主断']) if dr else set())
        avail_two = (r_two | ({v for p in dr['两说'] for v in p} if dr else set())) - avail_main
        da = ach_contest(ctx, ai, '大限', avail_main, avail_two, span=(s, e, pb)) if ai else None
        if not da and any(x['规则'] == 'T407-r3' for x, _ in ai_all):
            notes_a.append(('A成·时间层③', f'这段时间做满十年之后（{e} 岁以后）会非常好', ['T407']))
        if da:
            if '高' in an['主断'] and '低' in da['主断']:
                notes_a.append(('A成·时间层②', '命好限不好，这十年会半空折翅', ['T844', 'T1315']))
            if e <= 23 and '高' in da['主断']:
                notes_a.append(('A成·时间层③', '止岁在 23 岁以内，高只算求学期的好（考试好、当班长）', ['T1316', 'T837', 'T1197']))
            if any(x['规则'] == 'T407-r3' for x, _ in ai_all):
                notes_a.append(('A成·时间层③', f'这段时间做满十年之后（{e} 岁以后）会非常好', ['T407']))
            if s >= 72 and '高' in da['主断'] and '武职' in avail_main:
                notes_a.append(('A成·时间层③', '72 岁以后才到，不必劝他当武官', ['T1336']))
            yq = [a for a in range(s, e + 1) if ctx.year_branch_of_age(a) == pb]
            if da['主断'] and yq:
                notes_a.append(('A成·时间层⑤', f"应期：虚岁 {yq[0]}（大小二限相逢）", ['T524', 'T1112']))
        yr_r, yr_a = liunian_notes(ctx, s, e, r_main, r_two, dr, da)
        if dr or notes_r or yr_r:
            R['大限'].append({'岁段': (s, e), '大限': dr, '流年': yr_r, '附注': notes_r, '婚变应期': []})
        if da or notes_a or yr_a:
            A['大限'].append({'岁段': (s, e), '大限': da, '流年': yr_a, '附注': notes_a, '婚变应期': []})
    return [R, A]


def liunian_notes(ctx, s, e, r_main, r_two, dr, da):
    """时间层（R1⑤、R2④、G10）：流年只作当年附注，不改大限，也不改一生主断；综合论断不逐年列出（技术选择第22条），这里照算以备查。
    路线：只有 T1416-r1，记「这一年有X之事」，与所在大限（没有大限路线时用一生主断）互斥的记为当年例外。
    成就：流年命宫本宫、对宫的成就命中（引擎的流年求值本来只看本宫、对宫），与本限主断相同写「该年加强」，相反写「本限主X，该年Y」。
    以路线为前提的，照第2步；T238-r2「批武官的命」只看一生主断（R2 第2步末句）。"""
    yr_r, yr_a = [], []
    base_r = set(dr['主断']) if dr and dr['主断'] else set(r_main)
    base_a = set(da['主断']) if da and da['主断'] else set()
    for a in range(s, e + 1):
        nr, na = [], []
        for x in ctx.ev:
            if x['时间层'] != '流年' or a not in (x['虚岁'] or ()):
                continue
            for attr, v in x['claims']:
                if attr == '路线' and x['规则'] == 'T1416-r1':
                    ex = any(frozenset((v, m)) in EXC_R for m in base_r)
                    nr.append(('A路·时间层⑤', f"这一年有{v}之事" + ('（当年例外）' if ex else ''), [x['T']]))
                elif attr == '成就':
                    rid = x['规则']
                    if rid == 'T238-r2':
                        if '武职' in r_main:
                            pass
                        elif '武职' in r_two:
                            na.append(('A成2', f"若走武职，这一年{v}", [x['T']])); continue
                        else:
                            continue
                    elif any(rid in ids for ids in PREMISE.values()):
                        k = next(kk for kk, ids in PREMISE.items() if rid in ids)
                        if k not in r_main and k not in (set(dr['主断']) if dr else set()):
                            continue
                    if v == '低' and weak_low(x, ctx.rule(x)):
                        continue
                    if base_a and v in base_a:
                        na.append(('A成·时间层④', f"该年加强（{v}）", [x['T']]))
                    elif base_a:
                        na.append(('A成·时间层④', f"本限主{'、'.join(sorted(base_a))}，该年{v}", [x['T']]))
                    else:
                        na.append(('A成·时间层④', f"这一年成就{v}", [x['T']]))
        if nr:
            yr_r.append({'虚岁': a, '主断': [], '两说': [], '附注': nr, '两说另列': []})
        if na:
            yr_a.append({'虚岁': a, '主断': [], '两说': [], '附注': na, '两说另列': []})
    return yr_r, yr_a


def synthesize(ctx):
    return route_and_achievement(ctx)
