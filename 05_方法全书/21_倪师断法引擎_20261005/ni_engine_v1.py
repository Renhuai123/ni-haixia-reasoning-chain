"""倪师断法引擎 v1（M2）：按倪师看盘顺序，对一张命盘逐层推论，每句结论带出处。
输入：chart_runner_v1.cjs 输出的命盘（正式站快照 a908，默认十项设置）；知识库合并文件（倪师层 kb_validate_v2.py 输出，可再加全书补层 kb_qs_validate_v1.py 输出）。
输出：结构化论断 JSON；render_text() 生成中文成稿（cite=False 时不带出处编号，供盲审）。
原则：
- 只用知识库里 valid 且可操作的规则；规则条件逐条按核验脚本 check_cond 的解析结果求值，不另加条件。
- 宫位关系：对宫＝相隔六宫；三方＝相隔四宫与八宫（命宫的三方即官禄、财帛）；三方四正＝本宫＋三方＋对宫；夹＝左右两邻宫。
- 亮度：快照引擎 XD2 原始值 庙/旺→庙旺，平/闲→平闲，陷→陷。
- 「任一宫」规则（星的通义）按宫性分两种用法：
  · 人宫（命宫 兄弟 夫妻 子女 仆役 父母）：结论整条归到该宫所主之人（T393「兄弟是紫微天相，那就是兄弟当官的……就是这样推的」，T406「以此类推」）；
  · 事宫（财帛 官禄 田宅 疾厄 迁移 福德）：只取与该宫宫性相符的领域（T386 宫性，T390「流年刚好落在财帛宫里面，代表今年你的主力在财帛上面」）。
- 空宫（无十四主星）时，借对宫主星代入「本宫有」条件求值，并注明借对宫（倪师读空宫命盘先看对面，如 T423）。
- 地支论病：任一宫、领域健康、条件带宫支的规则，在宫支所在那一宫求值，结论归本人身体（疾厄），不论那一宫是十二宫里的哪一宫（T1052、T1053、T1058）。
- 算子（倪师方法）在规则命中之后作修正，只修正由本宫杀星引出的凶断，每个算子写明所据原话（T10、T294、T313、T317、T977）。
- 两层：倪师层优先；全书补层只用在倪师层在同一宫（大限、流年同理）、同一领域没有任何命中的地方，成稿标「全书补」（研究方案 M1、M2）。
- 流年求值只看本宫、对宫，不看三方与夹（T1389）。
- 层次：先天十二宫 → 十年大限（大限宫当这十年的命宫，T1422、T1113；只列起运不晚于 96 岁的）→ 流年（流年命宫＝太岁所在宫，按年支每十二年一轮归纳，虚岁 1–96；倪师「十年为主，流年为辅」T1373）。
- 同组取舍（resolve）：空宫明示优先、细化优先（吉凶相反或只差亮度时，条件被包含的一般规则让位给更具体的规则）、断优先于倾向、仍分不出记「两说」、同句只留一句。
- 并列候选：对每个候选各读一次，只保留各候选完全一致的结论（M3/M4 方案一）。
- 涉及生死的结论：按研究方案只作健康与安全提醒，成稿不直接断死（结构化结果保留原结论与出处）。
- 逐例留一：leave_out() 剔除出处全部落在指定讲述时段内的规则（M3/M4 方案三）。
用法：python3 ni_engine_v1.py --kb <倪师层合并文件> [--kb-qs <全书补层合并文件>] --charts <runner 输出> --out <新文件>"""
import argparse, collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BR = '子丑寅卯辰巳午未申酉戌亥'
STEMS = '甲乙丙丁戊己庚辛壬癸'
PALACES = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄', '迁移', '仆役', '官禄', '田宅', '福德', '父母']
WHO = {'命宫': '本人', '兄弟': '兄弟', '夫妻': '配偶', '子女': '子女', '财帛': '钱财', '疾厄': '身体', '迁移': '外出与外地',
       '仆役': '朋友与合伙', '官禄': '事业', '田宅': '家宅与祖业', '福德': '福德与精神', '父母': '父母'}
MAJOR = ['紫微', '天机', '太阳', '武曲', '天同', '廉贞', '天府', '太阴', '贪狼', '巨门', '天相', '天梁', '七杀', '破军']
CLASSES = {'吉星': ['左辅', '右弼', '文昌', '文曲', '天魁', '天钺'], '杀星': ['擎羊', '陀罗', '火星', '铃星', '地空', '地劫'],
           '杀破狼': ['七杀', '破军', '贪狼'], '主星': MAJOR, '财星': ['禄存', '武曲', '贪狼'], '贵星': ['紫微', '太阳', '武曲', '天同']}
# 财星另含「带化禄的星」（T332「禄存化禄啊武曲贪狼，这都是属于大的财星」）
LEVEL = {'庙': '庙旺', '旺': '庙旺', '平': '平闲', '闲': '平闲', '陷': '陷'}
PERSON = {'命宫', '兄弟', '夫妻', '子女', '仆役', '父母'}
THEME = {'财帛': {'财'}, '官禄': {'路线', '成就'}, '田宅': {'祖业田宅'}, '疾厄': {'健康'}, '迁移': {'路线', '意外'}, '福德': {'福德'}}
SHA = CLASSES['杀星']
JI = CLASSES['吉星']
DAY = {3, 4, 5, 6, 7, 8}   # 卯至申时为昼


class Chart:
    def __init__(self, row):
        c = row['chart']
        self.id = row['id']
        self.gender = '男' if row['birth'].get('gender') == 'male' else '女'
        self.by_branch = {p['branch']: p for p in c['palaces']}
        self.by_name = {p['name']: p for p in c['palaces']}
        self.star_at, self.star = {}, {}
        for p in c['palaces']:
            for s in p['stars']:
                self.star_at[s['name']] = p['branch']; self.star[s['name']] = s
        self.shen = next(p['name'] for p in c['palaces'] if p.get('isShenGong'))
        self.daxian = c['daXians']
        li = c.get('lunarInfo') or {}
        self.year_stem = STEMS[li['yearStem']] if isinstance(li.get('yearStem'), int) else None
        self.year_branch = li.get('yearBranch') if isinstance(li.get('yearBranch'), int) else None
        h = (c.get('birthInfo') or {}).get('hour')
        self.hour_branch = (h % 12) if isinstance(h, int) else None
        self.raw = c

    def stars_in(self, b):
        return [s['name'] for s in self.by_branch[b % 12]['stars']]

    def majors_in(self, b):
        return [s for s in self.stars_in(b) if s in MAJOR]

    def level(self, star):
        s = self.star.get(star)
        return LEVEL.get((s or {}).get('brightnessRaw'))

    def hua(self, star):
        return ((self.star.get(star) or {}).get('siHua') or '') or None


def positions(where, b, scope=None):
    """流年只看本宫和对宫（倪师「批一年的小流年……只需要看本宫和对宫」T1389）：流年求值时三方四正只取本宫、对宫，三方不取。"""
    if scope == '流年':
        return {'本宫': [b], '对宫': [(b + 6) % 12], '三方': [], '三方四正': [b, (b + 6) % 12]}[where]
    return {'本宫': [b], '对宫': [(b + 6) % 12], '三方': [(b + 4) % 12, (b + 8) % 12],
            '三方四正': [b, (b + 4) % 12, (b + 8) % 12, (b + 6) % 12]}[where]


def present(chart, names, bs):
    there = set(x for b in bs for x in chart.stars_in(b))
    return [n for n in names if n in there]


def eval_atom(chart, x, b, borrowed, scope=None):
    """b＝求值所在宫的地支；borrowed＝空宫借对宫时用来代替本宫主星的对宫主星；scope＝流年时按 T1389 只看本宫、对宫，不看夹。
    返回 True/False/None（None＝无法求值）。"""
    t = x['t']
    if t == '有无':
        bs = positions(x['where'], b, scope)
        res = []
        for s in x['stars']:
            if s in CLASSES:
                hit = present(chart, CLASSES[s], bs)
                if s == '财星':
                    hit = hit or [n for bb in bs for n in chart.stars_in(bb) if chart.hua(n) == '禄']
                if borrowed and x['where'] == '本宫':
                    hit = hit or [n for n in borrowed if n in CLASSES[s]]
                res.append(bool(hit))
            else:
                hit = bool(present(chart, [s], bs)) or (borrowed is not None and x['where'] == '本宫' and s in borrowed)
                res.append(hit)
        return all(res) if x['has'] else not any(res)
    if t == '夹':
        if scope == '流年':
            return None
        L, R = set(chart.stars_in(b - 1)), set(chart.stars_in(b + 1))
        ss = [CLASSES.get(s, [s]) for s in x['stars']]
        if len(ss) == 2:
            return (bool(L & set(ss[0])) and bool(R & set(ss[1]))) or (bool(L & set(ss[1])) and bool(R & set(ss[0])))
        return bool((L | R) & set(ss[0]))
    if t == '亮度':
        lv = chart.level(x['star'])
        return None if lv is None else lv == x['level']
    if t == '化':
        return chart.hua(x['star']) == x['hua']
    if t == '位化':
        bs = positions(x['where'], b, scope)
        have = {chart.hua(s) for bb in bs for s in chart.stars_in(bb)}
        if borrowed and x['where'] == '本宫':
            have |= {chart.hua(s) for s in borrowed}
        if x.get('has', True):
            return all(h in have for h in x['hua'])
        return not any(h in have for h in x['hua'])
    if t == '宫支':
        return BR[b % 12] in x['branches']
    if t == '空宫':
        return not chart.majors_in(b)
    if t == '性别':
        return chart.gender == x['g']
    if t == '身宫':
        return chart.shen == x['palace']
    if t == '年干':
        return None if chart.year_stem is None else chart.year_stem in x['stems']
    if t == '年支':
        return None if chart.year_branch is None else BR[chart.year_branch] in x['branches']
    if t == '生时':
        if chart.hour_branch is None:
            return None
        return (chart.hour_branch in DAY) == (x['when'] == '昼')
    return None   # 格、其他、未知写法：无法求值


def eval_rule(chart, rule, b, borrowed=None):
    """全部条件为真才命中；有无法求值的条件（格、其他）则不命中。年龄条件不在这里求值：先天规则的年龄只作应期标注；
    大限、流年规则的年龄在 read_one 里要求所走岁数与之有交集（age_ok、ages_in）。"""
    unk = []
    for x in rule['parsed_conditions']:
        if x['t'] == '年龄':
            continue
        v = eval_atom(chart, x, b, borrowed, rule['适用'])
        if v is None:
            unk.append(x['t']); continue
        if not v:
            return False, unk
    return (not unk), unk


def mentions(rule, star=None, cls=None, t=None):
    for x in rule['parsed_conditions']:
        if t and x['t'] == t and (star is None or x.get('star') == star):
            return True
        if x['t'] == '有无' and ((star and star in x['stars']) or (cls and cls in x['stars'])):
            return True
    return False


def operators(chart, rule, b):
    """倪师看盘算子：只修正「由本宫杀星引出的凶断」，且规则本身没有写到这个因素时才用。返回 (新方向, 新强度, 注记列表)。
    - 化忌对冲：「对冲比在本宫还凶」（T977）——规则条件是对宫化忌的凶断，强度升为断；
    以下依次判，前一条成立就不再看后面：
    - 紫微解厄：「煞星逢到紫微星的时候，这个煞星要去掉」（T10）——同宫有紫微，凶断改为中、倾向；
    - 杀星入庙：「看起来都是杀星，但杀星都入庙……叫凶处藏吉」（T313）——引出凶断的杀星全部庙旺，方向改为中；
    - 吉星减杀：「有杀星在里面，有吉星来的话杀星就杀的力量很差」（T294），「杀星一定要有吉星来化解」（T295）——同宫有吉星，强度降为倾向；
    - 杀星落陷：「杀星落陷代表是无解，这是很凶的」（T317）——没有吉星，引出凶断的杀星有落陷的，强度升为断。"""
    con = rule['结论']; pol, stg, notes = con['方向'], con['强度'], []
    if pol != '凶':
        return pol, stg, notes
    here = set(chart.stars_in(b))
    named = [st for x in rule['parsed_conditions'] if x['t'] == '有无' and x['where'] == '本宫' and x['has'] for st in x['stars']]
    trig = [st for st in SHA if (st in named or '杀星' in named) and st in here]
    if any(x['t'] == '位化' and x['where'] == '对宫' and '忌' in x['hua'] and x.get('has', True) for x in rule['parsed_conditions']):
        stg = '断'; notes.append('化忌从对宫冲来，比坐本宫更凶（T977）')
    if not trig:
        return pol, stg, notes
    if '紫微' in here and not mentions(rule, star='紫微'):
        return '中', '倾向', notes + ['同宫有紫微，煞星可解（T10）']
    lv = {st: chart.level(st) for st in trig if not mentions(rule, star=st, t='亮度')}
    has_ji = bool(here & set(JI)) and not mentions(rule, cls='吉星') and not any(mentions(rule, star=j) for j in JI)
    if lv and all(v == '庙旺' for v in lv.values()):
        pol = '中'; notes.append('、'.join(lv) + '入庙，凶处藏吉（T313）')
    elif has_ji:
        stg = '倾向'; notes.append('同宫有吉星，杀力减弱（T294）')
    elif any(v == '陷' for v in lv.values()):
        stg = '断'; notes.append('、'.join(k for k, v in lv.items() if v == '陷') + '落陷，凶中之凶（T317）')
    return pol, stg, notes


def specificity(rule):
    return sum(1 for x in rule['parsed_conditions'] if x['t'] != '年龄')


def try_rule(chart, r, b, via):
    """在宫 b 求值；不中且本宫空宫时借对宫再求一次。命中返回 hit 字典，否则 None。"""
    borrowed = chart.majors_in(b + 6) if not chart.majors_in(b) else None
    ok, _ = eval_rule(chart, r, b)
    if not ok and borrowed:
        ok, _ = eval_rule(chart, r, b, borrowed=borrowed)
        via = via + '（空宫借对宫）' if ok else via
    if not ok:
        return None
    pol, stg, notes = operators(chart, r, b)
    return {'rule': r['rule_id'], 'layer': r.get('layer', '倪师'), 'via': via, 'polarity': pol, 'strength': stg, 'operator_notes': notes}


def by_branch_health(r):
    """地支论病：任一宫、领域健康、条件里有宫支的规则（倪师「论病以宫的地支定内脏」「论病先不要管疾厄宫，要看杀星落在哪个地支宫」T1052、T1053、T1058）。"""
    return r['宫'] == '任一宫' and r['结论']['领域'] == '健康' and any(x['t'] == '宫支' for x in r['parsed_conditions'])


def natal_hits(chart, rules):
    hits = []
    natal = [r for r in rules if r['适用'] == '先天']
    for r in natal:
        if by_branch_health(r):
            # 按宫支所在的那一宫求值，病应在本人身上，归到疾厄（身体），不论那一宫是十二宫里的哪一宫
            for name in PALACES:
                h = try_rule(chart, r, chart.by_name[name]['branch'], f'地支论病（在{name}）')
                if h:
                    h['palace'] = '疾厄'; hits.append(h)
    for name in PALACES:
        b = chart.by_name[name]['branch']
        for r in natal:
            if by_branch_health(r):
                continue
            if r['宫'] == name:
                via = '本宫规则'
            elif r['宫'] == '身宫' and chart.shen == name:
                via = '身宫规则'
            elif r['宫'] == '任一宫' and (name in PERSON or r['结论']['领域'] in THEME.get(name, set())):
                via = '任一宫通义'
            else:
                continue
            h = try_rule(chart, r, b, via)
            if h:
                h['palace'] = name; hits.append(h)
    return hits


def age_ranges(rule):
    return [(x['lo'], x['hi']) for x in rule['parsed_conditions'] if x['t'] == '年龄']


def age_ok(rule, lo, hi):
    """大限：规则写了年龄（原话讲到岁数）时，这步大限的岁数要与之有交集，例如「23-32廉贞贪狼……半空折翅」只用于覆盖 23–32 岁的那步大限。"""
    return all(max(lo, a) <= min(hi, z) for a, z in age_ranges(rule))


def ages_in(rule, ages):
    """流年：只留落在规则年龄范围内的虚岁。"""
    return [g for g in ages if all(a <= g <= z for a, z in age_ranges(rule))]


def period_hits(chart, rules, scope, b):
    """大限或流年：把行运所到的宫 b 当作这段时间的命宫来读；规则的「宫」写命宫或任一宫的在此求值，写本命某宫名的只在行运走到该宫时用。"""
    name = chart.by_branch[b]['name']
    hits = []
    for r in rules:
        if r['适用'] != scope or r['宫'] not in ('任一宫', '命宫', name):
            continue
        h = try_rule(chart, r, b, '大限规则' if scope == '大限' else '流年规则')
        if h:
            h['palace'] = name; hits.append(h)
    return hits


def layer_filter(hits, by_id, key):
    """全书补层只留倪师层在同一键（宫或时段）、同一领域没有命中的。"""
    covered = {(key(h), by_id[h['rule']]['结论']['领域']) for h in hits if h['layer'] == '倪师'}
    return [h for h in hits if h['layer'] == '倪师' or (key(h), by_id[h['rule']]['结论']['领域']) not in covered]


def read_one(chart, rules, by_id):
    rules_by_id = {r['rule_id']: r for r in rules}
    natal = layer_filter(natal_hits(chart, rules), by_id, lambda h: h['palace'])
    dx = []
    for i, d in enumerate(chart.daxian):
        if d['startAge'] > 96:
            continue
        hs = [h for h in period_hits(chart, rules, '大限', d['palaceBranch']) if age_ok(rules_by_id[h['rule']], d['startAge'], d['endAge'])]
        for h in hs:
            h['span'] = (d['startAge'], d['endAge'])
        dx += layer_filter(hs, by_id, lambda h: h['span'])
    ln = []
    if chart.year_branch is not None:
        for b in range(12):
            hs = period_hits(chart, rules, '流年', b)
            ages = [a for a in range(1, 97) if (chart.year_branch + a - 1) % 12 == b]   # 虚岁 a 的流年年支
            for h in hs:
                h['year_branch'] = BR[b]; h['ages'] = ages_in(rules_by_id[h['rule']], ages)
            hs = [h for h in hs if h['ages']]
            ln += layer_filter(hs, by_id, lambda h: h['year_branch'])
    sihua = sorted(({'化': x.get('siHua'), '星': s, '宫': chart.by_branch[chart.star_at[s]]['name']} for s, x in chart.star.items() if x.get('siHua')),
                   key=lambda t: '禄权科忌'.index(t['化']))
    return {'natal': natal, 'daxian': dx, 'liunian': ln, 'sihua': sihua, 'shen': chart.shen, 'gender': chart.gender}


def consensus(readings):
    """并列候选：只保留各候选完全一致的结论。"""
    if len(readings) == 1:
        return dict(readings[0], n_candidates=1)
    def keyset(rd, part, f):
        return {f(h) for h in rd[part]}
    kn = lambda h: (h['palace'], h['rule'], h['polarity'], h['strength'])
    kd = lambda h: (h['span'], h['palace'], h['rule'], h['polarity'], h['strength'])
    kl = lambda h: (h['year_branch'], h['palace'], h['rule'], h['polarity'], h['strength'])
    out = {'n_candidates': len(readings)}
    for part, f in (('natal', kn), ('daxian', kd), ('liunian', kl)):
        common = set.intersection(*(keyset(rd, part, f) for rd in readings))
        out[part] = [h for h in readings[0][part] if f(h) in common]
    sh = [{(x['化'], x['星'], x['宫']) for x in rd['sihua']} for rd in readings]
    out['sihua'] = [x for x in readings[0]['sihua'] if (x['化'], x['星'], x['宫']) in set.intersection(*sh)]
    out['shen'] = readings[0]['shen'] if len({rd['shen'] for rd in readings}) == 1 else None
    out['gender'] = readings[0]['gender'] if len({rd['gender'] for rd in readings}) == 1 else None
    return out


def atoms(rule):
    return {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in rule['parsed_conditions'] if x['t'] != '年龄'}


def refines(a, b):
    """b 是否细化 a（a、b 为 (具体程度, 规则, 命中) 三元组）。"""
    A, B = atoms(a[1]), atoms(b[1])
    if not A < B:
        return False
    if a[2]['polarity'] != b[2]['polarity']:
        return True
    stars_a = {st for x in a[1]['parsed_conditions'] if x['t'] == '有无' and x['has'] for st in x['stars']}
    return all(x['t'] == '亮度' and x['star'] in stars_a for x in (json.loads(y) for y in B - A))


def resolve(xs):
    """同一组（同宫或同时段、同领域）里的取舍（研究方案 M2「冲突处理」）：
    0. 空宫明示优先：同组里有规则明写「空宫」而且直接命中，借对宫得来的结论让位（明写空宫的断语比借来的更贴合实际盘面）；
    1. 细化优先：规则 A 的条件被规则 B 完全包含（B 多了限定），且 B 与 A 吉凶相反（冲突时条件更具体的优先），
       或者 B 多出的只是 A 里那几颗星的亮度（倪师「同一颗星，庙、陷代表的意义不同，要先看亮度再下断」T199），A 让位；
    2. 断优先于倾向：剩下的规则里吉凶相反、条件同样具体时，有「断」的一方优先；
    3. 仍分不出，并列，记「两说」；
    4. 结论文字相同的只留一句（出处取条件最具体的那条）。"""
    if any('借' not in t[2]['via'] and any(x['t'] == '空宫' for x in t[1]['parsed_conditions']) for t in xs):
        xs = [t for t in xs if '借' not in t[2]['via']]
    keep = [t for t in xs if not any(refines(t, u) for u in xs if u is not t)]
    top = max(t[0] for t in keep)
    pols = {t[2]['polarity'] for t in keep if t[0] == top} - {'中'}
    if len(pols) > 1:
        strong = {t[2]['polarity'] for t in keep if t[0] == top and t[2]['strength'] == '断'} - {'中'}
        if len(strong) == 1:
            keep = [t for t in keep if t[2]['polarity'] in strong or t[2]['polarity'] == '中' or t[0] < top]
            pols = strong
    seen, out = set(), []
    for t in sorted(keep, key=lambda t: -t[0]):
        txt = t[1]['结论']['内容']
        if txt in seen:
            continue
        seen.add(txt); out.append(t)
    return out, len(pols) > 1


def summarize(hits, by_id, keyf):
    """按（键, 领域）归并，组内按 resolve() 取舍。"""
    groups = collections.defaultdict(list)
    for h in hits:
        r = by_id[h['rule']]
        groups[(keyf(h), r['结论']['领域'])].append((specificity(r), r, h))
    out = []
    for (k, dom), xs in groups.items():
        xs, two = resolve(xs)
        out.append({'键': k, '领域': dom, '两说': two,
                    '结论': [{'内容': t[1]['结论']['内容'], '方向': t[2]['polarity'], '强度': t[2]['strength'], '原方向': t[1]['结论']['方向'],
                             '算子': t[2]['operator_notes'], '涉生死': bool(t[1]['结论'].get('涉生死')), '层': t[2]['layer'],
                             '出处': {'T': t[1]['T'], '分P': t[1]['分P'], '时间': t[1]['时间'], '原话': t[1]['原话摘录']},
                             '推导': t[2]['via'], '条件': t[1]['条件']} for t in xs]})
    return out


def phrase(c, who, cite):
    txt = f'要特别注意{who}的健康与安全（原断涉及生死，按研究方案只作提醒）' if c['涉生死'] else c['内容']
    tags = []
    if c['层'] == '全书补':
        tags.append('全书补')
    if '借' in c['推导']:
        tags.append('借对宫')
    if cite:
        tags = [c['出处']['T']] + tags + c['算子']
    else:
        tags += [re.sub(r'（T\d+）', '', n) for n in c['算子']]
    return txt + (f"（{'，'.join(tags)}）" if tags else '')


def render_text(rd, by_id, cite=True):
    """中文成稿：照倪师看盘顺序。cite=True 时每句附出处（T 编号或《全书》句号）。"""
    L = []
    nat = summarize(rd['natal'], by_id, lambda h: h['palace'])
    by = collections.defaultdict(list)
    for g in nat:
        by[g['键']].append(g)
    order = ['长相', '个性', '行为', '路线', '成就', '财', '婚姻', '子女', '父母', '兄弟', '朋友合伙', '健康', '祖业田宅', '福德', '官非', '意外', '寿元', '其他']
    srt = lambda gs: sorted(gs, key=lambda g: order.index(g['领域']) if g['领域'] in order else 99)
    def line(name, g):
        who = WHO[name]
        return f"{g['领域']}：" + '；'.join(phrase(c, who, cite) for c in g['结论']) + ('〔两说〕' if g['两说'] else '')
    L.append('一、命宫（先天本人：长相、个性、行为模式、路线与成败）')
    for g in srt(by['命宫']):
        L.append('  ' + line('命宫', g))
    if not by['命宫']:
        L.append('  （知识库中没有可用于此命宫的断语）')
    L.append(f"二、身宫（后天发展）：在{rd['shen'] or '（各候选不一致）'}")
    for g in srt(by.get(rd['shen'], []) if rd['shen'] else []):
        cs = [c for c in g['结论'] if c['推导'].startswith('身宫规则')]
        if cs:
            L.append('  ' + f"{g['领域']}：" + '；'.join(phrase(c, '本人', cite) for c in cs))
    L.append('三、三方四正（财帛、官禄、迁移）')
    for name in ('财帛', '官禄', '迁移'):
        for g in srt(by[name]):
            L.append(f'  {name}·' + line(name, g))
    L.append('四、生年四化')
    L.append('  ' + ('，'.join(f"化{x['化']}在{x['宫']}（{x['星']}）" for x in rd['sihua']) or '（各候选不一致）'))
    L.append('五、六亲与诸宫')
    for name in ('兄弟', '夫妻', '子女', '仆役', '父母', '田宅', '福德', '疾厄'):
        for g in srt(by[name]):
            L.append(f'  {name}（{WHO[name]}）·' + line(name, g))
    L.append('六、十年大限（十年为主）')
    dxg = collections.defaultdict(list)
    for h in rd['daxian']:
        dxg[(h['span'], h['palace'])].append(h)
    for (span, pal), hs in sorted(dxg.items()):
        gs = summarize(hs, by_id, lambda h: h['palace'])
        body = '；'.join(f"{g['领域']}：" + '；'.join(phrase(c, '本人', cite) for c in g['结论']) for g in srt(gs))
        L.append(f'  {span[0]}–{span[1]}岁（行运走本命{pal}，这十年的主题偏{WHO[pal]}）：{body}')
    if not rd['daxian']:
        L.append('  （知识库中没有可用于各大限的断语）')
    L.append('七、流年（流年为辅；按年支每十二年一轮，岁数为虚岁）')
    lng = collections.defaultdict(list)
    for h in rd['liunian']:
        lng[(h['year_branch'], h['palace'], tuple(h['ages']))].append(h)
    for (yb, pal, ages), hs in sorted(lng.items(), key=lambda t: t[0][2][0]):
        gs = summarize(hs, by_id, lambda h: h['palace'])
        body = '；'.join(f"{g['领域']}：" + '；'.join(phrase(c, '本人', cite) for c in g['结论']) for g in srt(gs))
        L.append(f"  {yb}年（虚岁 {'、'.join(map(str, ages[:8]))}…，走本命{pal}）：{body}")
    if not rd['liunian']:
        L.append('  （知识库中没有可用于各流年的断语）')
    # 八、迷津：倪师「看到命宫他的一个人发展的模式以后，我们可以鼓励他，可以诱导他往他最适合路上面走」（T1328）；
    # 一辈子要注意的事（T1419–T1421）。只把上面已有的结论归拢，不新增断语。
    L.append('八、迷津（适合走的路，与一辈子要注意的事；只归拢上文结论）')
    seen, route = set(), []
    for name in ('命宫', rd['shen'], '官禄', '财帛', '迁移'):
        for g in by.get(name, []) if name else []:
            if g['领域'] in ('路线', '成就'):
                for c in g['结论']:
                    if c['方向'] != '凶' and c['内容'] not in seen:
                        seen.add(c['内容']); route.append(phrase(c, '本人', cite))
    L.append('  适合的路：' + ('；'.join(route) if route else '（没有可归拢的路线断语）'))
    warn, seen = [], set()
    for g in nat:
        for c in g['结论']:
            if c['方向'] == '凶' and c['强度'] == '断' and c['内容'] not in seen:
                seen.add(c['内容']); warn.append(f"{g['键']}：" + phrase(c, WHO[g['键']], cite))
    for h in rd['daxian']:
        r = by_id[h['rule']]
        if h['polarity'] == '凶' and h['strength'] == '断':
            c = {'内容': r['结论']['内容'], '涉生死': bool(r['结论'].get('涉生死')), '层': h['layer'], '推导': h['via'], '算子': h['operator_notes'],
                 '出处': {'T': r['T']}}
            k = f"{h['span'][0]}–{h['span'][1]}岁：" + phrase(c, '本人', cite)
            if k not in seen:
                seen.add(k); warn.append(k)
    L.append('  要注意：' + ('；'.join(warn) if warn else '（没有断定为凶的结论）'))
    return '\n'.join(L)


def load_rules(kb_paths):
    rules = []
    for p in kb_paths:
        if not p:
            continue
        kb = json.load(open(p, encoding='utf-8'))
        for r in kb['rules']:
            if r['valid'] and r['可操作']:
                rules.append(dict(r, layer=r.get('layer') or '倪师'))
    ids = [r['rule_id'] for r in rules]
    assert len(ids) == len(set(ids)), '规则编号重复'
    return rules


def secs(t):
    h, m, s = (int(x) for x in str(t).split(':'))
    return h * 3600 + m * 60 + s


def leave_out(rules, segments):
    """逐例留一：剔除出处落在任一讲述时段内的倪师层规则（时段已含前后各 2 分钟；分P 写法 'P9'、'P13（留出讲）' 都取数字，与 9、13 视为同一）。全书补层不受影响。"""
    def inside(r):
        m = re.match(r'P(\d+)', str(r.get('分P', '')))
        if r.get('layer') != '倪师' or not m or not r.get('时间'):
            return False
        p, t = int(m.group(1)), secs(r['时间'])
        return any(int(s['分P']) == p and s['start_s'] <= t <= s['end_s'] for s in segments)
    kept = [r for r in rules if not inside(r)]
    return kept, len(rules) - len(kept)


def read_candidates(rows, rules):
    by_id = {r['rule_id']: r for r in rules}
    rds = [read_one(Chart(row), rules, by_id) for row in rows]
    return consensus(rds), by_id


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kb', required=True)
    ap.add_argument('--kb-qs')
    ap.add_argument('--charts', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    rules = load_rules([a.kb, a.kb_qs])
    by_id = {r['rule_id']: r for r in rules}
    charts = json.load(open(a.charts, encoding='utf-8'))
    res = []
    for row in charts['rows']:
        if 'error' in row:
            res.append({'id': row['id'], 'error': row['error']}); continue
        rd = read_one(Chart(row), rules, by_id)
        res.append({'id': row['id'], 'reading': rd, 'n_hits': {k: len(rd[k]) for k in ('natal', 'daxian', 'liunian')}, 'text': render_text(rd, by_id)})
    with open(a.out, 'x', encoding='utf-8') as f:
        f.write(json.dumps({'schema': 'ni-engine-reading-v1', 'kb_rules_used': len(rules),
                            'by_layer': dict(collections.Counter(r['layer'] for r in rules)), 'readings': res}, ensure_ascii=False, indent=1) + '\n')
    ok = [r for r in res if 'n_hits' in r]
    print(json.dumps({'charts': len(res), 'rules_used': len(rules), 'mean_hits': {k: round(sum(r['n_hits'][k] for r in ok) / max(1, len(ok)), 1) for k in ('natal', 'daxian', 'liunian')}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
