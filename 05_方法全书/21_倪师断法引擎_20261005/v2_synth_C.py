"""引擎第二版·综合取舍 C 组：父母、兄弟、祖业田宅。照《取舍规则表》C 组裁定结果实现（v2_principles_v1/returns/C_裁定.json，已登记）。
步骤编号「C父7」「C兄3」「C祖6」＝C 组·属性·第几步，与裁定表 R1（父母）、R2（兄弟）、R3（祖业田宅）的「步」一一对应；通则 G1–G9 已体现在各步里。
G3（T294 减弱若只靠天府或天机就不认）：第一版算子认的吉星只有左辅、右弼、文昌、文曲、天魁、天钺，T294 从不由天府、天机引出，这一条在引擎里不会起作用（技术选择记录）。
实现中不得不做的技术选择，逐条记在《16》技术选择记录里（代码里标「技术选择」）。"""
import collections, re

from v2_synth_common import Contest, soft, all_charts, cond_has_ji, cond_has_sha, cond_named_stars, conds, E

T294 = lambda s: any('T294' in n for n in s['算子'])
T317 = lambda s: any('T317' in n for n in s['算子'])


def op_ts(s):
    """G2：附注照抄算子所引的 T 编号。"""
    return sorted({t for n in s['算子'] for t in re.findall(r'T\d+', n)})


def benben_sha(ctx, s):
    """C父8②：本宫的杀星（六杀或化忌）——条件里本宫有六杀或「杀星」；或本宫化忌、或点名在本宫的星化忌，而且化忌的星确实坐在该宫
    （这条凶说若是借对宫求得的，化忌星其实在对宫，不算本宫杀星；实现复核 C 第2条）。并列候选都要成立。"""
    r = ctx.rule(s)
    named = set(cond_named_stars(r))
    here_ji = lambda ch: any(ch.hua(y) == '忌' for y in ch.stars_in(ch.by_name[s['宫']]['branch']))
    for c in conds(r):
        if c['t'] == '有无' and c['has'] and c['where'] == '本宫' and (set(c['stars']) & {'擎羊', '陀罗', '火星', '铃星', '地空', '地劫'} or '杀星' in c['stars']):
            return True
        if c['t'] == '位化' and c['where'] == '本宫' and '忌' in c['hua'] and c.get('has', True) and all_charts(ctx.charts, here_ji):
            return True
        if c['t'] == '化' and c['hua'] == '忌' and c['star'] in named and \
                all_charts(ctx.charts, lambda ch, st=c['star']: st in ch.stars_in(ch.by_name[s['宫']]['branch'])):
            return True
    return False


def stars_of(r):
    """规则「依据」的星：条件里点名的（任何位置）、某星化某、某星亮度。"""
    out = set()
    for c in conds(r):
        if c['t'] == '有无' and c['has']:
            out |= {x for x in c['stars'] if x not in E.CLASSES}
        elif c['t'] in ('化', '亮度'):
            out.add(c['star'])
    return out


def bright_of(r):
    return {c['star'] for c in conds(r) if c['t'] == '亮度'}


def has_sihua(r):
    return any(c['t'] in ('化', '位化') for c in conds(r))


# ---------------- 父母（裁定表 R1） ----------------
FATHER = {'T77-r1', 'T998-r1'}
MOTHER = {'T932-r1', 'T962-r1', 'T989-r1', 'T989-r2'}
LEAVE = {'T212-r1', 'T212-r4'}
DX_PARENT = {'T77-r1', 'T78-r1', 'T78-r2'}
SHI_GONG = ('父母', '财帛', '疾厄', '迁移', '官禄', '田宅', '福德')


def ref(s):
    return '父' if s['规则'] in FATHER else '母' if s['规则'] in MOTHER else '父母'


def overlap(a, b):
    return a == b or '父母' in (a, b)


def parent_pairs():
    refs = ('父', '母', '父母')
    return [(f'{x}·凶', f'{y}·吉') for x in refs for y in refs if overlap(x, y)]


def p_contest(ctx, items, layer):
    notes, drop, two_extra = [], [], []
    sup = collections.defaultdict(list)
    for s, vals in items:
        for v in vals:
            if soft(s) and v == '凶':
                notes.append(('C父4', f"修正后不再是凶，只作附注：{s['内容']}", op_ts(s))); continue
            sup[f'{ref(s)}·{v}'].append(s)
    c = Contest(sup, parent_pairs())

    def dirn(v):
        return v.split('·')[1]

    def same(a, b):
        return overlap(a.split('·')[0], b.split('·')[0])
    # C父5：亮度在先（同一宫、所指重叠、依据同一颗星、方向相反）
    lose = set()
    for a, b in c.conflicts():
        for sa in c.support[a]:
            for sb in c.support[b]:
                if sa['宫'] != sb['宫']:
                    continue
                ra, rb = ctx.rule(sa), ctx.rule(sb)
                common = stars_of(ra) & stars_of(rb)
                ab = any(x in bright_of(ra) and x not in bright_of(rb) for x in common)
                ba = any(x in bright_of(rb) and x not in bright_of(ra) for x in common)
                if ab and not ba:
                    lose.add((b, id(sb)))
                elif ba and not ab:
                    lose.add((a, id(sa)))
    if lose:
        c.remove_statements('C父5', lambda v, x: (v, id(x)) in lose, note='亮度在先')
    # C父6：化忌破庙旺：只凭某星庙旺得出、又不含这颗星化忌的吉，这颗星生年化忌时降为另说
    def broken(x):
        r = ctx.rule(x)
        miao = {cc['star'] for cc in conds(r) if cc['t'] == '亮度' and cc['level'] == '庙旺'}
        has_ji = {cc['star'] for cc in conds(r) if cc['t'] == '化' and cc['hua'] == '忌'}
        return any(all_charts(ctx.charts, lambda ch, st=st: ch.hua(st) == '忌') for st in miao - has_ji)
    c.remove_statements('C父6', lambda v, x: dirn(v) == '吉' and broken(x), note='化忌破庙旺')
    # C父7：化忌之凶压过不含四化之吉（同一宫、所指重叠）
    lose = set()
    for a, b in c.conflicts():
        bad, good = (a, b) if dirn(a) == '凶' else (b, a)
        for sb in c.support[bad]:
            if sb['方向'] == '凶' and cond_has_ji(ctx.rule(sb)) and not T294(sb):
                lose |= {(good, id(g)) for g in c.support[good] if g['宫'] == sb['宫'] and not has_sihua(ctx.rule(g))}
    if lose:
        c.remove_statements('C父7', lambda v, x: (v, id(x)) in lose, note='化忌之凶压过不含四化之吉')
    # C父8：①落陷杀星之凶（带 T317）压过父母宫之吉；②借对宫之吉让位给本宫杀星（六杀或化忌）之凶
    lose = set()
    for a, b in c.conflicts():
        bad, good = (a, b) if dirn(a) == '凶' else (b, a)
        for sb in c.support[bad]:
            if sb['方向'] != '凶':
                continue
            if T317(sb):
                lose |= {(good, id(g)) for g in c.support[good] if g['宫'] == sb['宫']}
            if benben_sha(ctx, sb) and not T294(sb):
                lose |= {(good, id(g)) for g in c.support[good] if g['宫'] == sb['宫'] and g['借对宫']}
    if lose:
        c.remove_statements('C父8', lambda v, x: (v, id(x)) in lose, note='吉处藏凶')
    res = c.result()
    if any(x['规则'] == 'T989-r2' for v in res['主断'] for x in c.support[v]):
        notes.append(('C父6', '妈妈不会早走，跟命主感情特别好，会为命主担心烦恼（不是庙旺大吉）', ['T989', 'T1432', 'T1434']))
    if any(x['规则'] == 'T998-r1' and not soft(x) for x, _ in items):
        notes.append(('C父·时间层', '父亲之凶限于小时候（女命太阳小时候指爸爸）', ['T74', 'T82']))
    if res['主断'] or res['两说']:
        notes.append(('C父9', '六亲推断准度较差，主断最高只作倾向', ['T383', 'T384']))
    res.update({'附注': notes, '两说另列': two_extra, 'contest': c, '不取': drop})
    return res


def parents(ctx):
    natal, leave, dx = [], [], collections.defaultdict(list)
    for s in ctx.ev:
        vals = [v for a, v in s['claims'] if a == '父母']
        if not vals:
            continue
        if s['时间层'] == '先天' and s['规则'] in LEAVE and s['宫'] == '命宫':
            leave.append(s)
        elif s['时间层'] == '先天' and s['宫'] == '父母':
            natal.append((s, vals))
        elif s['时间层'] == '大限' and s['规则'] in DX_PARENT:
            dx[s['岁段']].append((s, vals))
    if natal:
        n = p_contest(ctx, natal, '先天')
    else:   # C父3：父母宫没有先天命中，父母不下吉凶主断
        n = {'主断': [], '两说': [], '淘汰': {}, '两说出处': {}, '附注': [], '两说另列': [], 'contest': None, '不取': []}
    if leave:
        n['附注'].append(('C父3', '本人离开父母（如读书考到外地）', ['T212', 'T408']))
        n['不取'] = n.get('不取', []) + [('C父3', x) for x in leave]
    out = {'属性': '父母', '对象': '父母', '先天': n, '大限': []}
    for (s, e, pb) in ctx.daxian_spans():
        its = dx.get((s, e))
        if not its:
            continue
        dnotes = [('C父4', f"修正后不再是凶，只作附注：{x['内容']}", op_ts(x)) for x, v in its if soft(x)]
        its = [(x, v) for x, v in its if x['方向'] == '凶' and '凶' in v]
        mine = [(x, v) for x, v in its if x['宫'] in SHI_GONG]
        other = [x for x, v in its if x['宫'] not in SHI_GONG]
        res = {'主断': sorted({f'{ref(x)}·凶' for x, v in mine}), '两说': [], '淘汰': {}, '两说出处': {}, '附注': dnotes, '两说另列': [], 'contest': None, '不取': [],
               '依据': {f'{ref(x)}·凶': [y for y, _ in mine if ref(y) == ref(x)] for x, _ in mine}}
        if other and not mine:
            pals = sorted({x['宫'] for x in other})
            res['两说另列'].append(('父母有问题', f"应在{'、'.join(pals)}之人", 'C父·时间层', ['T473', 'T1111'], other, []))
        if res['主断'] or res['两说另列']:
            res['附注'].append(('C父9', '六亲推断准度较差，主断最高只作倾向', ['T383', 'T384']))
        out['大限'].append({'岁段': (s, e), '大限': res, '流年': [], '附注': [], '婚变应期': []})
    return out


# ---------------- 兄弟（裁定表 R2） ----------------
JI_BRO = {'T439-r1', 'T439-r2', 'T453-r1', 'T985-r1', 'T985-r2', 'T985-r3', 'T451-r1'}
SHA_BRO = {'T439-r4', 'T439-r5'}


def brothers(ctx):
    items = [(s, [v for a, v in s['claims'] if a == '兄弟']) for s in ctx.ev if s['时间层'] == '先天' and s['宫'] == '兄弟']
    items = [(s, v) for s, v in items if v]
    notes, drop, has_bro = [], [], []
    sup = collections.defaultdict(list)
    for s, vals in items:
        if s['规则'] == 'T542-r2':      # C兄2：只跟 T444-r1 相对；其余只作「有兄弟」附注
            has_bro.append(s); continue
        for v in vals:
            if soft(s) and v == '凶':
                notes.append(('C兄1', f"修正后不再是凶，只作附注：{s['内容']}", op_ts(s))); continue
            sup[v].append(s)
    t444 = [x for x in sup.get('凶', []) if x['规则'] == 'T444-r1']
    two_extra = []
    if has_bro and t444:   # 取值关系·互斥：T542-r2「有兄弟」与 T444-r1「没有兄弟」，第3、4步管不到，写两说（C兄5）
        sup['凶'] = [x for x in sup['凶'] if x['规则'] != 'T444-r1']
        two_extra.append(('有兄弟', '没有兄弟', 'C兄5', ['T542', 'T444'], has_bro, t444))
    elif has_bro:
        notes.append(('C兄2', '有兄弟', ['T444', 'T542']))
    c = Contest(sup, [('凶', '吉')])
    if '凶' in c.alive() and '吉' in c.alive():
        bad = c.support['凶']
        if any(x['规则'] in JI_BRO and x['方向'] == '凶' and not T294(x) for x in bad):
            c.out['吉'] = ('C兄3', '凶', '兄弟宫有忌（化忌之凶）'); c.log.append(('C兄3', [('吉', '凶')]))
        elif all(x['规则'] in SHA_BRO for x in bad):
            if any(T317(x) for x in bad) or (all(g['借对宫'] for g in c.support['吉']) and any(not T294(x) for x in bad)):
                c.out['吉'] = ('C兄4', '凶', '落陷杀星或借对宫之吉'); c.log.append(('C兄4', [('吉', '凶')]))
    res = c.result()
    if {'T444-r1', 'T444-r2'} <= ({x['规则'] for x in c.support.get('凶', [])} | {x['规则'] for x in t444}):
        notes.append(('C兄·两说②', '一说没有兄弟，一说有兄弟而且夭折', ['T444']))
    if res['主断'] or res['两说'] or two_extra:
        notes.append(('C兄5', '六亲推断准度较差，主断最高只作倾向', ['T383', 'T384']))
    res.update({'附注': notes, '两说另列': two_extra, 'contest': c, '不取': drop, '前提': has_bro if two_extra else []})
    return {'属性': '兄弟', '对象': '兄弟', '先天': res, '大限': []}


# ---------------- 祖业田宅（裁定表 R3） ----------------
ZHICHAN = {'T654-r1', 'T104-r1'}
FIRE = {'T645-r1', 'T650-r1'}
NOT_RELY = 'T414-r3'
BORROW_NOLU = {'T205-r2', 'T415-r2', 'T712-r1', 'T716-r2', 'T775-r2'}
WITH_LU = {'T712-r2', 'T947-r2'}


def z_contest(ctx, items, layer):
    notes, drop, zhichan = [], [], []
    sup = collections.defaultdict(list)
    for s, vals in items:
        rid = s['规则']
        if rid == NOT_RELY:
            notes.append(('C祖4', '即使祖业再大，也不靠祖业起家', ['T414'])); continue
        if rid in ZHICHAN or rid in FIRE:
            if rid in FIRE and soft(s):
                if any('T313' in n for n in s['算子']):
                    notes.append(('C祖3', '凶处藏吉：火险看得见，可以预防', ['T313', 'T1518']))
                else:
                    notes.append(('C祖3', f"修正后不再是凶，只作附注：{s['内容']}", op_ts(s)))
                continue
            zhichan.append(s); continue
        for v in vals:
            if soft(s) and v in ('无祖业', '破祖业'):
                notes.append(('C祖3', f"修正后不再是凶，只作附注：{s['内容']}", op_ts(s))); continue
            sup[v].append(s)
    c = Contest(sup, [('有祖业', '无祖业'), ('无祖业', '破祖业')])
    # C祖6：父母宫内，T716-r1（无祖业）对父母宫的有祖业
    t716 = [x for x in c.support.get('无祖业', []) if x['规则'] == 'T716-r1' and x['方向'] == '凶']
    if t716 and '有祖业' in c.alive():
        x = t716[0]
        pm = [g for g in c.support['有祖业'] if g['宫'] == '父母']
        if T317(x):
            c.remove_statements('C祖6', lambda v, g: v == '有祖业' and g['宫'] == '父母', note='落陷杀星，父母宫的有祖业让位')
        elif not T294(x):
            c.remove_statements('C祖6', lambda v, g: v == '有祖业' and g['宫'] == '父母' and g['借对宫'] and g['规则'] in BORROW_NOLU,
                                note='父母宫空宫有地劫，借对宫又不带化禄的有祖业让位')
    res = c.result()
    premise = []
    # C祖5：有祖业与破祖业同时成立，主断写「有祖业而破」，取值记为破祖业，有祖业各条作为前提照列
    if ctx.on('C祖5') and '破祖业' in res['主断'] and '有祖业' in res['主断']:
        res['主断'].remove('有祖业')
        premise = list(c.support['有祖业'])
        res['合写'] = {'破祖业': '有祖业而破（先有后破，会把父母亲的财产耗掉）'}
    elif ctx.on('C祖5') and sorted(['有祖业', '无祖业']) in res['两说'] and sorted(['破祖业', '无祖业']) in res['两说']:
        # 有祖业、破祖业同在两说的同一方（都只与无祖业相对）：这一说写作「有祖业而破」，有祖业作前提照列（实现复核 C 新问题3）
        res['两说'] = [p for p in res['两说'] if p != sorted(['有祖业', '无祖业'])]
        premise = list(c.support['有祖业'])
        res['合写'] = {'破祖业': '有祖业而破（先有后破，会把父母亲的财产耗掉）'}
    # C祖2、C祖8：置产义单独出主断，置产旺与火灾照原话并列，不取舍
    res['置产'] = zhichan
    if layer == '大限' and any(x['规则'] == 'T205-r1' for v in res['主断'] for x in c.support[v]):
        notes.append(('C祖·时间层', '这十年祖业分得到', ['T205']))
    res.update({'附注': notes, '两说另列': [], 'contest': c, '不取': drop, '前提': premise})
    return res


def ancestry(ctx):
    items = collections.defaultdict(list)
    for s in ctx.ev:
        vals = [v for a, v in s['claims'] if a == '祖业田宅']
        if not vals:
            continue
        if s['时间层'] == '先天' and s['宫'] in ('田宅', '父母', '命宫'):
            items['先天'].append((s, vals))
        elif s['时间层'] == '大限':
            items[s['岁段']].append((s, vals))
    out = {'属性': '祖业田宅', '对象': '本人', '先天': z_contest(ctx, items['先天'], '先天'), '大限': []}
    for (s, e, pb) in ctx.daxian_spans():
        if items.get((s, e)):
            out['大限'].append({'岁段': (s, e), '大限': z_contest(ctx, items[(s, e)], '大限'), '流年': [], '附注': [], '婚变应期': []})
    return out


def synthesize(ctx):
    return [parents(ctx), brothers(ctx), ancestry(ctx)]
