"""引擎第二版·综合取舍的通用部件（依据《15》；不含任何命理判断，命理判断都在各组规则表的实现里：v2_synth_A.py、v2_synth_B.py、v2_synth_C.py）。
- evidence：第一版的全部命中，带归类；
- Ctx：取舍的上下文（论断、规则、并列候选的命盘）；
- 条件特征：条件里有没有化忌、四化、六杀，点名了哪些星、写没写亮度；
- Contest：按规则表的互斥关系与各步胜负逐步淘汰，剩下的互斥对子记为两说。"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_engine_v1 as E
from v2_claims_final_v1 import rule_claims

LAYERS = (('natal', '先天'), ('daxian', '大限'), ('liunian', '流年'))


def scope_key(layer, h):
    """说法所在的位置：先天＝宫；大限＝（岁段, 宫）；流年＝（年支, 宫, 虚岁）。与第一版成稿的分节一致。"""
    if layer == '先天':
        return h['palace']
    if layer == '大限':
        return (tuple(h['span']), h['palace'])
    return (h['year_branch'], h['palace'], tuple(h['ages']))


def evidence(rd, by_id):
    """综合取舍的输入：第一版的全部命中（同组取舍之前），每条带归类。《取舍规则表》自己规定冲突怎样处理（例如不按断与倾向取舍），
    所以这里不先套第一版的同组取舍；第一版的同组取舍只决定下文细目显示哪几句。"""
    out = []
    for part, layer in LAYERS:
        for h in rd[part]:
            r = by_id[h['rule']]
            cs = rule_claims(r)
            if not cs:
                continue
            out.append({'时间层': layer, '位置': scope_key(layer, h), '宫': h['palace'], '领域': r['结论']['领域'], '规则': r['rule_id'], 'T': r['T'],
                        '规则宫': r['宫'], '内容': r['结论']['内容'], '方向': h['polarity'], '强度': h['strength'], '原方向': r['结论']['方向'],
                        '原强度': r['结论']['强度'], '算子': h['operator_notes'], '具体程度': E.specificity(r), '推导': h['via'],
                        '借对宫': '借' in h['via'], '涉生死': bool(r['结论'].get('涉生死')),
                        '岁段': tuple(h['span']) if 'span' in h else None, '年支': h.get('year_branch'),
                        '虚岁': tuple(h['ages']) if 'ages' in h else None, 'claims': cs})
    return out


def soft(s):
    """修正后不再为凶的凶断（算子按 T10 紫微可解、T313 杀星入庙改了方向）。"""
    return s['原方向'] == '凶' and s['方向'] != '凶'


class Ctx:
    """综合取舍的上下文：论断（并列候选已取交集）、规则表、并列候选的命盘（随机盘只有一张）。
    命盘上的特征（星的亮度、某宫有什么星、四化在哪）要每个候选都成立才算（all_charts），保守。"""

    def __init__(self, rd, by_id, charts, disabled=()):
        self.rd, self.by_id, self.charts = rd, by_id, charts
        self.gender = rd.get('gender')
        self.ev = evidence(rd, by_id)
        self.disabled = set(disabled)   # 关掉的取舍步骤（M4c 对称留一用：依据全部出自题内当事人讲述时段的步骤）；平时为空

    def on(self, sid):
        return sid not in self.disabled

    def rule(self, s):
        return self.by_id[s['规则']]

    def daxian_spans(self):
        """各步大限（起岁, 止岁, 大限宫地支）；各候选不一致的去掉。只列起运不晚于 96 岁的（与第一版相同）。"""
        sets = [{(d['startAge'], d['endAge'], d['palaceBranch']) for d in c.daxian if d['startAge'] <= 96} for c in self.charts]
        return sorted(set.intersection(*sets)) if sets else []

    def span_of_age(self, a):
        for s, e, b in self.daxian_spans():
            if s <= a <= e:
                return (s, e, b)
        return None

    def year_branch_of_age(self, a):
        """虚岁 a 那一年的流年地支（与第一版 read_one 同一算法）；各候选不一致时为 None。"""
        ys = {c.year_branch for c in self.charts}
        if len(ys) != 1 or None in ys:
            return None
        return (ys.pop() + a - 1) % 12

    def palace_branch(self, name):
        bs = {c.by_name[name]['branch'] for c in self.charts}
        return bs.pop() if len(bs) == 1 else None

    def sihua_palace(self, hua):
        """生年某化（禄权科忌）所在的宫名（各候选一致才给）。"""
        xs = [x for x in self.rd['sihua'] if x['化'] == hua]
        return xs[0]['宫'] if xs else None

    def sihua_star(self, hua):
        xs = [x for x in self.rd['sihua'] if x['化'] == hua]
        return xs[0]['星'] if xs else None


# ---------- 取舍要用的条件特征（只看规则条件的解析结果，与第一版求值用的是同一份） ----------
SIX_SHA = E.SHA   # 六杀：擎羊 陀罗 火星 铃星 地空 地劫


def conds(r):
    return [x for x in r['parsed_conditions'] if x['t'] != '年龄']


def cond_has_ji(r):
    """条件含化忌：只认规则表列出的三种写法——某星化忌（化:X=忌）、本宫化:忌、对宫化:忌（B 组 R1 第7步、C 组 R1 第7步、G6）。
    三方、三方四正化忌不算；写「无化」的不算。"""
    return any((x['t'] == '化' and x['hua'] == '忌') or (x['t'] == '位化' and x['where'] in ('本宫', '对宫') and '忌' in x['hua'] and x.get('has', True))
               for x in conds(r))


def cond_has_sihua(r):
    """条件含四化（禄权科忌任一种，含「无化」写法）。"""
    return any(x['t'] in ('化', '位化') for x in conds(r))


def cond_has_sha(r):
    """条件含六杀：点名擎羊、陀罗、火星、铃星、地空、地劫，或写「杀星」类。"""
    return any(x['t'] == '有无' and x['has'] and (set(x['stars']) & set(SIX_SHA) or '杀星' in x['stars']) for x in conds(r))


def cond_named_stars(r, where=('本宫',)):
    """条件里「有」的星（不含星类名），默认只看本宫。"""
    return [s for x in conds(r) if x['t'] == '有无' and x['has'] and x['where'] in where for s in x['stars'] if s not in E.CLASSES]


def cond_bright_stars(r):
    return {x['star'] for x in conds(r) if x['t'] == '亮度'}


def cond_atoms(r):
    return E.atoms(r)


def all_charts(charts, f):
    """并列候选时，命盘上的特征要每个候选都成立才算（保守）；随机盘只有一个候选。"""
    return bool(charts) and all(f(c) for c in charts)


# ---------- 取舍过程（机械部分：只按规则表的互斥关系与各步的胜负判定逐步淘汰，不含命理判断） ----------
class Contest:
    """一个对象·属性在一个时间段里的取舍。
    support：取值 → 支持它的说法列表；pairs：规则表列出的互斥对子（无序）。
    每一步给一个判定函数 decide(a, sa, b, sb) → 'a' / 'b' / None（a、b 为互斥的两个取值，sa、sb 为各自的说法）；
    同一步里对所有仍在冲突的对子各判一次，判输的取值一并淘汰（记下步骤编号与胜方）。
    各步走完仍在冲突的对子，记为两说。"""

    def __init__(self, support, pairs):
        self.support = {v: list(ss) for v, ss in support.items() if ss}
        self.pairs = {frozenset(p) for p in pairs if len(set(p)) == 2}
        self.out = {}      # 取值 → (步骤编号, 胜方取值, 说明)
        self.frozen = {}   # 对子 → (步骤编号, 说明)：规则表写明「写两说」的对子，后面各步不再取舍
        self.removed = []  # (步骤编号, 取值, 说法)：按说法剔除的
        self.log = []

    def alive(self):
        return [v for v in self.support if v not in self.out and self.support[v]]

    def all_conflicts(self):
        al = self.alive()
        return [(a, b) for i, a in enumerate(al) for b in al[i + 1:] if frozenset((a, b)) in self.pairs]

    def conflicts(self):
        """仍待取舍的对子（已冻结为两说的不算）。"""
        return [p for p in self.all_conflicts() if frozenset(p) not in self.frozen]

    def freeze(self, sid, a, b, note=''):
        k = frozenset((a, b))
        if k in self.pairs and k not in self.frozen:
            self.frozen[k] = (sid, note)
            self.log.append((sid, [('两说', tuple(sorted(k)))]))

    def remove_statements(self, sid, pred, values=None, note=''):
        """按说法剔除（规则表写「某些说法不取」时用）；剔光了的取值随之淘汰。"""
        for v in list(self.support):
            if values is not None and v not in values:
                continue
            keep = [x for x in self.support[v] if not pred(v, x)]
            self.removed += [(sid, v, x) for x in self.support[v] if pred(v, x)]
            if len(keep) < len(self.support[v]):
                self.log.append((sid, [('剔除说法', v, len(self.support[v]) - len(keep))]))
                self.support[v] = keep
                if not keep and v not in self.out:
                    self.out[v] = (sid, None, note)

    def step(self, sid, decide, note=''):
        lose = {}
        for a, b in self.conflicts():
            w = decide(a, self.support[a], b, self.support[b])
            if w == 'a':
                lose.setdefault(b, a)
            elif w == 'b':
                lose.setdefault(a, b)
        for v, by in lose.items():
            self.out[v] = (sid, by, note)
        if lose:
            self.log.append((sid, sorted(lose.items())))
        return lose

    def drop(self, sid, value, note=''):
        """规则表直接排除某个取值（不是两两比较，例如「四宫都没有禄就不取经商」）。"""
        if value in self.support and value not in self.out:
            self.out[value] = (sid, None, note)
            self.log.append((sid, [(value, None)]))

    def result(self):
        al = self.alive()
        two = self.all_conflicts()
        tied = {v for p in two for v in p}
        return {'主断': [v for v in al if v not in tied], '两说': [sorted(p) for p in two], '淘汰': dict(self.out),
                '两说出处': {tuple(sorted(p)): self.frozen.get(frozenset(p), ('各步走完仍互斥', '')) for p in two}}


def side_any(ss, f):
    return any(f(s) for s in ss)


def prefer(f):
    """常用判定：一方有说法满足 f、另一方没有，取前者；两方都有或都没有，不定。"""
    def decide(a, sa, b, sb):
        x, y = side_any(sa, f), side_any(sb, f)
        return 'a' if x and not y else 'b' if y and not x else None
    return decide
