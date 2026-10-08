"""引擎第二版·综合取舍 B 组：婚姻、子女。照《取舍规则表》B 组裁定结果实现（v2_principles_v1/returns/B_裁定.json，已登记）。
步骤编号「B婚4」「B子3」＝B 组·属性·第几步，与裁定表 R1（婚姻）、R2（子女）的「步」一一对应；通则 G1–G9 已体现在各步里。
实现中不得不做的技术选择，逐条记在《16》技术选择记录里（代码里标「技术选择」）。"""
import collections

from v2_synth_common import Contest, prefer, soft, all_charts, cond_has_ji, cond_named_stars, cond_bright_stars, conds, SIX_SHA

BR = '子丑寅卯辰巳午未申酉戌亥'
OTHER_PERSON = ('兄弟', '子女', '父母', '仆役')

# ---------------- 婚姻（裁定表 R1） ----------------
SOLAR_DIV = {'T75-r1', 'T75-r2', 'T77-r3', 'T78-r3', 'T1008-r2', 'T991-r1', 'T994-r1', 'T992-r2'}   # B婚2
GE_JURI = {'T794-r2', 'T802-r1', 'T803-r1', 'T806-r1', 'T807-r1', 'T810-r1'}                     # B婚6 巨日会命
FUDE_BAD = {'T257-r2', 'T668-r1', 'T668-r2', 'T668-r3', 'T673-r1'}                                # B婚8
WANGFU = 'T1437-r2'                                                                               # B婚5
HONGLUAN_LN = {'T351-r1', 'T371-r1', 'T359-r1'}                                                   # 时间层③b
NOT_MARRY_LN = {'T764-r2', 'T764-r3'}                                                             # ③d
DROP_BY_764 = {'T351-r1', 'T764-r1', 'T359-r1'}                                                   # ③d
NO_HUSBAND_DX = {'T75-r1', 'T75-r2', 'T77-r3', 'T78-r3', 'T1008-r2'}                              # ④
NOT_MARRY_DX = 'T181-r1'                                                                          # ③a
OBJ_COND = {'T86-r1', 'T86-r2'}                                                                    # 倪师未讲⑩：要看对象条件，只作附注
PAIRS_M = [('好', '不好'), ('会结婚', '不成'), ('早婚', '晚婚'), ('早婚', '不成'), ('晚婚', '不成'), ('多婚', '不成')]
DOUBT_NATAL = [('不成', '婚变'), ('不成', '偏房')]       # 存疑不取舍（倪师未讲），先天层
DOUBT_ALL = [('偏房', '好'), ('偏房', '会结婚')]
JI_PAIRS = {frozenset(p) for p in [('好', '不好'), ('会结婚', '不成'), ('早婚', '不成'), ('多婚', '不成')]}   # B婚7、B婚9 适用的对子
BAD = {'不好', '不成'}


def m_items(ctx):
    """B婚1：收集婚姻证据，按裁定表的证据宫。返回 [(说法, [取值...])]。"""
    out = []
    for s in ctx.ev:
        vals = [v for a, v in s['claims'] if a == '婚姻']
        if not vals:
            continue
        rid, pal, L, rg = s['规则'], s['宫'], s['时间层'], s['规则宫']
        if L == '先天':
            ok = (pal in ('夫妻', '福德', '命宫') or (pal == '父母' and rid in ('T338-r1', 'T707-r1'))
                  or (pal == '子女' and rid == 'T339-r1') or (pal == '仆役' and rid in ('T339-r2', 'T618-r2')))
            if rid == 'T1228-r1' and pal not in ('命宫', '夫妻', '福德'):
                ok = False
        elif rg == '夫妻':
            ok = L == '流年' and rid in ('T302-r4', 'T302-r9')
        else:
            ok = rg == '命宫'
        if ok:
            out.append((s, vals))
    return out


def relies_only_outside(ctx, g):
    """吉方说法只靠对宫、三方、三方四正的条件或借对宫成立（B婚9、B子6）。技术选择：位置条件（有无、位化）全是对宫、三方、三方四正，
    且没有空宫、夹的条件，才算「只靠」；性别、亮度、某星化某这类不带位置的条件不影响。"""
    if g['借对宫']:
        return True
    pos = [x for x in conds(ctx.rule(g)) if x['t'] in ('有无', '位化', '空宫', '夹')]
    return bool(pos) and all(x['t'] in ('有无', '位化') and x['where'] in ('对宫', '三方', '三方四正') for x in pos)


def sha_relied(ctx, s, chart):
    """凶方说法所依的杀星（B婚9：六杀；七杀、破军、贪狼；廉贞破军；廉贞贪狼；T764-r3 的太阴）。条件写「杀星」类的，取该宫实有的六杀。"""
    r = ctx.rule(s)
    b = chart.by_name[s['宫']]['branch']
    here = set(chart.stars_in(b))
    named = set(cond_named_stars(r))
    stars = named & (set(SIX_SHA) | {'七杀', '破军', '贪狼'})
    if '廉贞' in named and named & {'破军', '贪狼'}:
        stars.add('廉贞')
    for x in conds(r):
        if x['t'] == '有无' and x['has'] and x['where'] == '本宫':
            if '杀星' in x['stars']:
                stars |= here & set(SIX_SHA)
            if '杀破狼' in x['stars']:
                stars |= here & {'七杀', '破军', '贪狼'}
    if s['规则'] == 'T764-r3':
        stars.add('太阴')
    return stars & here     # 只认确实坐在该宫的星：借对宫得来的说法，所依的星在对宫，不算「该宫落陷」


def fallen_sha(ctx, s):
    """技术选择：所依的杀星全部落陷才算（并列候选都要成立）。"""
    def f(c):
        st = sha_relied(ctx, s, c)
        return bool(st) and all(c.level(x) == '陷' for x in st)
    return all_charts(ctx.charts, f)


def bright_beats(ctx, sa, sb):
    """B婚10、亮度先看：同一宫、同一颗星引出的两条，sa 写明该星亮度、sb 没写 → sa 胜。"""
    if sa['宫'] != sb['宫'] or soft(sa):
        return False
    ra, rb = ctx.rule(sa), ctx.rule(sb)
    ba, bb = cond_bright_stars(ra), cond_bright_stars(rb)
    nb = set(cond_named_stars(rb))
    return any(x in nb and x not in bb for x in ba)


def bright_step(c, ctx, sid):
    lose = set()
    for a, b in c.conflicts():
        for sa in c.support[a]:
            for sb in c.support[b]:
                ab, ba = bright_beats(ctx, sa, sb), bright_beats(ctx, sb, sa)
                if ab and not ba:
                    lose.add((b, id(sb)))
                elif ba and not ab:
                    lose.add((a, id(sa)))
    if lose:
        c.remove_statements(sid, lambda v, x: (v, id(x)) in lose, note='亮度先看')


def soft_step(c, sid):
    """修正后不再为凶的凶断，不算凶方证据，不能压过对方；与对方互斥时写两说（B婚4、B子2）。"""
    for a, b in c.conflicts():
        if all(soft(x) for x in c.support[a]) or all(soft(x) for x in c.support[b]):
            c.freeze(sid, a, b, '修正后不再为凶的凶断，与对方互斥，写两说')


def m_contest(ctx, items, layer):
    """一个时间段内的婚姻取舍（B婚2、B婚4–11）。"""
    sup, notes, two_extra = collections.defaultdict(list), [], []
    restricted = []
    for s, vals in items:
        if s['规则'] in OBJ_COND:
            notes.append(('B婚·倪师未讲⑩', f"要看对象条件，引擎拿不到，只作附注：{s['内容']}", [s['T']])); continue
        for v in vals:
            if layer != '先天' and s['规则'] in SOLAR_DIV and s['宫'] in OTHER_PERSON and v == '婚变':
                restricted.append(s)       # B婚2：太阳凶兆落在别的人宫，不作本人婚变主断
            else:
                sup[v].append(s)
    doubt = DOUBT_ALL + (DOUBT_NATAL if layer == '先天' else [])
    c = Contest(sup, PAIRS_M + doubt)
    for a, b in doubt:
        c.freeze('B婚1', a, b, '倪师未讲，写两说')
    soft_step(c, 'B婚4')
    # B婚5：旺夫命讲她本人，与同段的「不好」互斥时，从「好」一方拿掉
    if not ctx.on('B婚5'):
        pass
    elif '不好' in c.alive() and any(x['规则'] == WANGFU for x in c.support.get('好', [])):
        c.remove_statements('B婚5', lambda v, x: v == '好' and x['规则'] == WANGFU, note='旺夫命讲的是本人，不当配偶好')
    elif any(x['规则'] == WANGFU for x in c.support.get('好', [])):
        notes.append(('B婚5', '旺夫命讲的是她本人，不等于先生好、白头偕老', ['T1440', 'T1441']))
    c.step('B婚6', prefer(lambda x: x['规则'] in GE_JURI and not soft(x)), '格成立优先（巨日会命）')
    # B婚7：化忌优先（只限凶方）
    lose = {}
    for a, b in c.conflicts():
        if frozenset((a, b)) not in JI_PAIRS:
            continue
        bad, good = (a, b) if a in BAD else (b, a)
        sb, sg = c.support[bad], c.support[good]
        q = any(cond_has_ji(ctx.rule(x)) and x['方向'] == '凶' for x in sb)
        good_ji = any(cond_has_ji(ctx.rule(x)) for x in sg)
        if q and not good_ji:
            lose[good] = bad
        elif good_ji:
            c.freeze('B婚7', a, b, '化忌命中在吉方一侧或两方都有，写两说')
    for v, by in lose.items():
        c.out[v] = ('B婚7', by, '化忌优先（凶方）')
    if lose:
        c.log.append(('B婚7', sorted(lose.items())))
    # B婚8：女命福德为先（先天）
    if layer == '先天' and ctx.gender == '女' and any(x['宫'] == '福德' and x['规则'] in FUDE_BAD and x['方向'] == '凶' for x, _ in items):
        c.remove_statements('B婚8', lambda v, x: v == '好' and x['宫'] in ('命宫', '夫妻'), note='女命福德宫凶，命宫、夫妻宫的好不取')
    # B婚9：落陷杀星的凶不被他处的吉抵消
    def d9(a, sa, b, sb):
        if frozenset((a, b)) not in JI_PAIRS:
            return None
        bad, sbad, sgood = (a, sa, sb) if a in BAD else (b, sb, sa)
        for s in sbad:
            if s['方向'] == '凶' and fallen_sha(ctx, s) and all(g['宫'] != s['宫'] or relies_only_outside(ctx, g) for g in sgood):
                return 'a' if bad == a else 'b'
        return None
    c.step('B婚9', d9, '落陷杀星的凶不被他处的吉抵消')
    bright_step(c, ctx, 'B婚10')
    res = c.result()
    # 技术选择：只靠修正后不再为凶的说法支持、又没有对手的取值，不作主断，记为附注
    for v in list(res['主断']):
        if all(soft(x) for x in c.support[v]):
            res['主断'].remove(v)
            notes.append(('B婚4', f'{v}之说经算子减弱（凶处藏吉或紫微可解），不作主断', []))
    if restricted and '婚变' not in res['主断'] and not any('婚变' in p for p in res['两说']):
        pals = sorted({x['宫'] for x in restricted})
        two_extra.append(('婚变（本人）', f"应在{'、'.join(pals)}之人", 'B婚2', ['T473', 'T82', 'T992'], restricted, []))
    res.update({'附注': notes, '两说另列': two_extra, 'contest': c, 'restricted': restricted, '不取': []})
    return res


def marriage(ctx):
    items = m_items(ctx)
    natal = [(s, v) for s, v in items if s['时间层'] == '先天']
    out = {'属性': '婚姻', '对象': '本人', '先天': m_contest(ctx, natal, '先天'), '大限': []}
    ji_star = ctx.sihua_star('忌')
    for s, e, pb in ctx.daxian_spans():
        dx = [(x, v) for x, v in items if x['时间层'] == '大限' and x['岁段'] == (s, e)]
        dres = m_contest(ctx, dx, '大限') if dx else None
        years = []
        dx_not_marry = any(x['规则'] == NOT_MARRY_DX and x['方向'] == '凶' for x, _ in dx)
        for a in range(s, e + 1):
            ln = [(x, v) for x, v in items if x['时间层'] == '流年' and a in (x['虚岁'] or ())]
            if not ln:
                continue
            yb = ctx.year_branch_of_age(a)
            notes = []
            # ③b：红鸾引出的流年结婚，要所在大限的大限宫三方四正有红鸾
            def hl_ok(c):
                p = c.star_at.get('红鸾')
                return p is not None and p in ((pb) % 12, (pb + 4) % 12, (pb + 8) % 12, (pb + 6) % 12)
            drop = []
            if any(x['规则'] in HONGLUAN_LN for x, _ in ln) and not all_charts(ctx.charts, hl_ok):
                drop += [('B婚③b', x) for x, _ in ln if x['规则'] in HONGLUAN_LN]
                ln = [(x, v) for x, v in ln if x['规则'] not in HONGLUAN_LN]
                notes.append(('B婚③b', '红鸾未动：所在大限的三方四正没有红鸾，红鸾引出的结婚不取', ['T488', 'T1369']))
            # ③d：同一流年 T764-r2/r3 修正后仍为凶 → 当年不成，红鸾、吉星引出的结婚与再婚不取；修正后不为凶的，不当不成的证据
            # ③d：T764-r2/r3 修正后仍为凶 → 当年取「不成」：当年的会结婚、多婚一概不取（规则表点名的 T351-r1、T764-r1、T359-r1 之外，
            # 名单外的结婚说法也不取，以符合「当年取不成」）；修正后不为凶的 T764-r2/r3 不触发这一条，照第4步进取舍
            if any(x['规则'] in NOT_MARRY_LN and x['方向'] == '凶' for x, _ in ln):
                # 按取值剔除：一条说法只去掉会结婚、多婚，其余取值照留（取值关系·可并存）
                drop += [('B婚③d', x) for x, v in ln if {'会结婚', '多婚'} & set(v) and not (set(v) - {'会结婚', '多婚'})]
                ln = [(x, [y for y in v if y not in ('会结婚', '多婚')]) for x, v in ln]
                ln = [(x, v) for x, v in ln if v]
            if not ln:
                if notes:
                    years.append({'虚岁': a, '主断': [], '两说': [], '附注': notes, '两说另列': [], '不取': drop})
                continue
            yr = m_contest(ctx, ln, '流年')
            yr['附注'] = notes + yr['附注']
            yr['不取'] = drop
            # ③a：大限有修正后仍为凶的「不成」，这十年里流年的会结婚、多婚写两说
            if dx_not_marry:
                for v in ('会结婚', '多婚'):
                    if v in yr['主断']:
                        yr['主断'].remove(v)
                        yr['两说另列'].append((v, '不成（本大限）', 'B婚③a', ['T1383', 'T1012', 'T1375'], yr['contest'].support[v],
                                             [x for x, _ in dx if x['规则'] == NOT_MARRY_DX]))
            # ③c：流年宫本宫坐生年化忌，会结婚不作主断
            if ji_star and '会结婚' in yr['主断'] and yb is not None and all_charts(ctx.charts, lambda c: c.star_at.get(ji_star) == yb):
                yr['主断'].remove('会结婚'); yr['附注'].append(('B婚③c', '流年宫坐生年化忌，要走过化忌才结婚，这一年的结婚不作主断', ['T1012']))
            yr['虚岁'] = a
            years.append(yr)
        # ④：女命行运走到太阳陷地的婚变，与这十年的结婚并存
        dnotes = []
        mine = lambda x: not (x['规则'] in SOLAR_DIV and x['宫'] in OTHER_PERSON)   # 落在别的人宫的太阳凶兆按 B婚2 写两说，不算本人的
        if any(x['规则'] in NO_HUSBAND_DX and mine(x) for x, _ in dx) and ((dres and '会结婚' in dres['主断']) or any('会结婚' in y['主断'] for y in years)):
            dnotes.append(('B婚④', '这十年里结的婚，主生离或死别', ['T521']))
        # ⑤：婚变应期：大限宫与流年宫同宫的那一岁，该宫在大限层或流年层有婚变命中
        yingqi = []
        natal_div = '婚变' in out['先天']['主断']
        for a in range(s, e + 1):
            if not (natal_div or (dres and '婚变' in dres['主断'])) or ctx.year_branch_of_age(a) != pb:
                continue
            has_dx = any('婚变' in v and mine(x) for x, v in dx)
            has_ln = any('婚变' in v and mine(x) for x, v in items if x['时间层'] == '流年' and a in (x['虚岁'] or ()))
            if has_dx or has_ln:
                kind = ''
                if ji_star:
                    if all_charts(ctx.charts, lambda c: c.star_at.get(ji_star) == (pb + 6) % 12):
                        kind = '化忌对冲'
                    elif all_charts(ctx.charts, lambda c: c.star_at.get(ji_star) == pb):
                        kind = '化忌坐守'
                yingqi.append((a, kind))
        if dres or years or dnotes or yingqi:
            out['大限'].append({'岁段': (s, e), '大限': dres, '流年': years, '附注': dnotes, '婚变应期': yingqi})
    return out


# ---------------- 子女（裁定表 R2） ----------------
SON_OTHER = {'T77-r2', 'T1008-r1'}                                       # B子1：大限，女命行运走到太阳陷地
SHAPO = ('七杀', '破军', '贪狼')
SHAPO_RULES = {'T540-r1', 'T543-r2', 'T543-r5', 'T543-r6', 'T552-r1', 'T552-r2'}
SHA_NOSON = {'T465-r2', 'T551-r1'}


def c_items(ctx):
    out = []
    for s in ctx.ev:
        vals = [v for a, v in s['claims'] if a == '子女']
        if not vals:
            continue
        if s['时间层'] == '先天' and s['宫'] == '子女':
            out.append((s, vals))
        elif s['时间层'] == '大限' and s['规则'] in SON_OTHER:
            out.append((s, vals))
    return out


def c_contest(ctx, items, layer):
    sup, notes, two_extra, restricted = collections.defaultdict(list), [], [], []
    for s, vals in items:
        for v in vals:
            if layer == '大限' and s['规则'] in SON_OTHER and s['宫'] in ('兄弟', '夫妻', '父母', '仆役'):
                restricted.append(s)       # B子1：落在别的人宫，写两说
            else:
                sup[v].append(s)
    c = Contest(sup, [('有子', '无子')])
    soft_step(c, 'B子2')
    hard = lambda ids: any(x['规则'] in ids and x['方向'] == '凶' for vs in c.support.values() for x in vs)
    decided = False
    # B子3：本宫化忌
    if layer == '先天' and hard({'T995-r1'}):
        if any(x['规则'] == 'T1006-r1' for x in c.support.get('有子', [])):
            c.freeze('B子3', '有子', '无子', 'T1006 与 T995 谁先倪师未讲，有子无子写两说，凶照取')
        else:
            c.drop('B子3', '有子', '子女宫本宫化忌，阳星再多也没有')
        decided = True
    # B子4：空宫、对宫化忌
    if layer == '先天' and not decided and hard({'T532-r1', 'T548-r1'}):
        c.drop('B子4', '有子', '空宫被对宫化忌冲，借来的有子不取')
        decided = True
    # B子5：子女宫本宫（不借对宫）有七杀、破军、贪狼 → 只看这三颗星的规则
    if layer == '先天' and not decided:
        def has_shapo(ch):
            return bool(set(ch.stars_in(ch.by_name['子女']['branch'])) & set(SHAPO))
        if all_charts(ctx.charts, has_shapo):
            c.remove_statements('B子5', lambda v, x: v in ('有子', '无子', '凶') and x['规则'] not in SHAPO_RULES | SHA_NOSON,
                                note='子女宫有杀破狼，不管宫里其他星')
            if hard(SHA_NOSON):
                c.freeze('B子5', '有子', '无子', '本宫杀星的无子对杀破狼的有子，写两说')
            decided = True
    # B子6：落陷杀星不被三方、对宫的吉抵消
    if layer == '先天' and not decided:
        for s in c.support.get('无子', []):
            if s['规则'] in SHA_NOSON and s['方向'] == '凶':
                def fallen(ch):   # 技术选择：与 B婚9 同一口径，本宫的六杀全部落陷才算
                    st = set(ch.stars_in(ch.by_name['子女']['branch'])) & set(SIX_SHA)
                    return bool(st) and all(ch.level(x) == '陷' for x in st)
                if all_charts(ctx.charts, fallen) and all(relies_only_outside(ctx, g) for g in c.support.get('有子', [])):
                    c.drop('B子6', '有子', '本宫落陷杀星，有子只靠对宫、三方或借对宫')
                    break
    bright_step(c, ctx, 'B子·G8')      # G8 亮度先看（G9 执行次序：专门步骤 → G7 → G8）
    res = c.result()
    for v in list(res['主断']):
        if all(soft(x) for x in c.support[v]):
            res['主断'].remove(v)
            notes.append(('B子2', f'{v}之说经算子减弱，不作主断', []))
    if restricted and '无子' not in res['主断']:
        pals = sorted({x['宫'] for x in restricted})
        two_extra.append(('这十年不生儿子', f"应在{'、'.join(pals)}之人", 'B子1', ['T473', 'T74', 'T82'], restricted, []))
    shown = set(res['主断']) | {v for p in res['两说'] for v in p}
    if ({'有子', '无子'} & shown) or two_extra:
        notes.append(('B子8', '只论儿子，是本人命盘的说法（无子不等于没有女儿），实际有几个要与配偶命盘合看；子女将来如何，以子女本人的命盘为准' +
                      ('；命上没有儿子的人，有了儿子有夭折之象' if layer == '先天' and '无子' in res['主断'] else ''),
                      ['T526', 'T539', 'T527', 'T533', 'T528'] + (['T536'] if layer == '先天' and '无子' in res['主断'] else [])))
    if layer == '大限' and ('无子' in res['主断'] or two_extra):
        notes.append(('B子·时间层②', '这十年不生儿子，只管该岁数区间，不改先天主断', ['T836', 'T1375']))
    if res['主断'] or res['两说'] or two_extra:
        notes.append(('B子7', '六亲推断准度较差，子女主断最高只作倾向', ['T383', 'T384', 'T528']))
    res.update({'附注': notes, '两说另列': two_extra, 'contest': c, 'restricted': restricted, '不取': []})
    return res


def children(ctx):
    items = c_items(ctx)
    out = {'属性': '子女', '对象': '只论儿子', '先天': c_contest(ctx, [(s, v) for s, v in items if s['时间层'] == '先天'], '先天'), '大限': []}
    for s, e, pb in ctx.daxian_spans():
        dx = [(x, v) for x, v in items if x['时间层'] == '大限' and x['岁段'] == (s, e)]
        if dx:
            out['大限'].append({'岁段': (s, e), '大限': c_contest(ctx, dx, '大限'), '流年': [], '附注': [], '婚变应期': []})
    return out


def synthesize(ctx):
    return [marriage(ctx), children(ctx)]
