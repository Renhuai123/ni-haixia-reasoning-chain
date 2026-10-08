"""倪师断法引擎第三版：流年按倪海厦的起法（依据《21_第三版流年起法_方案_v1.md》）。
第一版（ni_engine_v1.py）、第二版（ni_engine_v2.py、v2_synth_*.py）都已定版，本文件只调用、不修改它们。与第二版的差别只有：
1. 流年宫：虚岁 a 的流年宫 ＝（起宫 ＋ 方向 ×（a − 1））模 12。起宫按出生年支：申子辰起戌、巳酉丑起未（T1353、T1359、T1364、T1365），
   寅午戌起辰、亥卯未起丑（原话未明讲，按通行小限起法补全）；男命顺行（地支序号加 1），女命逆行（减 1）（T1356、T1361）；
   虚岁＝流年年份 − 出生年份 ＋ 1（T1354）。第一、二版用的是太岁宫（虚岁 a 那年的年支所在之宫）。
2. 第二版综合取舍里「虚岁 a 的流年宫」（Ctx.year_branch_of_age）改用上面的算法；取舍规则表与其余代码不动。
3. 并列候选的流年结论，除宫、规则、方向、强度外，还要求虚岁相同才算一致（性别不同的候选，同一宫的虚岁不同）。
4. 成稿第七节：标题写明起法；各行只写「虚岁 a、b……（走本命某宫）」，不再写年支。
用法：作为模块调用 read_one / read_candidates / synthesize / render_text_v3。"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_engine_v1 as E
import ni_engine_v2 as V
from v2_synth_common import Ctx

BR = E.BR
START = {}
for _yb, _s in ((8, 10), (0, 10), (4, 10), (5, 7), (9, 7), (1, 7), (2, 4), (6, 4), (10, 4), (11, 1), (3, 1), (7, 1)):
    START[_yb] = _s   # 申子辰→戌；巳酉丑→未；寅午戌→辰；亥卯未→丑（地支序号：子 0 … 亥 11）
LN_TITLE_V3 = '七、流年（流年为辅；按倪海厦的起法：依生年地支定 1 岁所在之宫，男顺女逆；岁数为虚岁）'


def xiaoxian_branch(chart, a):
    """虚岁 a 的流年宫地支序号；生年地支或性别缺失时为 None。"""
    if chart.year_branch is None or chart.gender not in ('男', '女'):
        return None
    step = 1 if chart.gender == '男' else -1
    return (START[chart.year_branch] + step * (a - 1)) % 12


def read_one(chart, rules, by_id):
    """同第一版 read_one，只把流年那一段的「虚岁 → 宫」改为倪海厦的起法。"""
    rd = E.read_one(chart, rules, by_id)
    rules_by_id = {r['rule_id']: r for r in rules}
    ln = []
    if xiaoxian_branch(chart, 1) is not None:
        for b in range(12):
            hs = E.period_hits(chart, rules, '流年', b)
            ages = [a for a in range(1, 97) if xiaoxian_branch(chart, a) == b]
            for h in hs:
                h['year_branch'] = BR[b]       # 第三版：这里存的是流年宫的地支，供分组与合并用，不是年支
                h['ages'] = E.ages_in(rules_by_id[h['rule']], ages)
            hs = [h for h in hs if h['ages']]
            ln += E.layer_filter(hs, by_id, lambda h: h['year_branch'])
    rd['liunian'] = ln
    return rd


def consensus(readings):
    """同第一版 consensus；流年另要求虚岁相同。"""
    out = E.consensus(readings)
    if len(readings) > 1:
        kl = lambda h: (h['year_branch'], h['palace'], h['rule'], h['polarity'], h['strength'], tuple(h['ages']))
        common = set.intersection(*({kl(h) for h in rd['liunian']} for rd in readings))
        out['liunian'] = [h for h in readings[0]['liunian'] if kl(h) in common]
    return out


def read_candidates(rows, rules):
    by_id = {r['rule_id']: r for r in rules}
    rds = [read_one(E.Chart(row), rules, by_id) for row in rows]
    return consensus(rds), by_id


class Ctx3(Ctx):
    def year_branch_of_age(self, a):
        """第三版：虚岁 a 的流年宫地支序号（倪海厦起法）；各候选不一致时为 None。第二版各处都把它当「当年流年宫」用。"""
        bs = {xiaoxian_branch(c, a) for c in self.charts}
        if len(bs) != 1 or None in bs:
            return None
        return bs.pop()


def synthesize(rd, by_id, charts, disabled=()):
    """同第二版 synthesize，上下文换成 Ctx3。"""
    import v2_synth_A as SA, v2_synth_B as SB, v2_synth_C as SC
    ctx = Ctx3(rd, by_id, charts, disabled)
    res = SA.synthesize(ctx) + SB.synthesize(ctx) + SC.synthesize(ctx)
    return {'属性': res, 'marks': V.compute_marks(res)}


LN_LINE = re.compile(r'^  [子丑寅卯辰巳午未申酉戌亥]年（虚岁 ([^，（）]*)，走本命(..)）：')


def render_text_v3(rd, by_id, synth=None, cite=True, only_synthesis=False):
    """同第二版成稿；第七节标题写明起法，各行去掉年支。"""
    t = V.render_text_v2(rd, by_id, synth, cite=cite, only_synthesis=only_synthesis)
    if only_synthesis:
        return t
    out, in7 = [], False
    for ln in t.split('\n'):
        if ln.startswith('七、流年'):
            in7 = True
            out.append(LN_TITLE_V3)
            continue
        if ln.startswith('八、'):
            in7 = False
        if in7:
            m = LN_LINE.match(ln)
            if m:
                ln = f'  虚岁 {m.group(1)}（走本命{m.group(2)}）：' + ln[m.end():]
        out.append(ln)
    return '\n'.join(out)
