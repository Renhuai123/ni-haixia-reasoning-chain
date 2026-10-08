"""倪师断法引擎 v2（第二版）：在第一版命中结果之上加「综合取舍」。
依据：《15》方案；《15a》《15b》结论归类；《15c》取舍原则分组整理；《取舍规则表》（v2_principles_v1 三组裁定结果的合集）。
原则：
- 知识库、命中计算、同组取舍、算子一律用第一版（ni_engine_v1.py，已冻结）；本文件只调用第一版的函数，不改第一版。
- 综合取舍的输入是第一版成稿里实际列出的说法：先天按（宫、领域），大限按（岁段、宫、领域），流年按（年支、宫、领域），
  做完第一版的同组取舍（resolve）之后剩下的那些。这样「综合论断」只归拢下文看得到的说法。
- 每条说法按 v2_claims_final_v1.rule_claims 归成（属性, 取值）。
- 成稿：开头加「综合论断」一节；后面各节与第一版逐字相同，只在被取舍掉的说法后标「已取舍」。不传取舍结果时，成稿与第一版逐字相同。
用法：import ni_engine_v2 as V；V.statements(rd, by_id)；V.render_text_v2(rd, by_id, synth, cite)"""
import collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_engine_v1 as E
from v2_claims_final_v1 import rule_claims
from v2_synth_common import LAYERS, scope_key


def kept_groups(hits, by_id, keyf):
    """与 E.summarize 相同的分组与同组取舍，但返回保留下来的（具体程度, 规则, 命中）三元组，以便知道每句出自哪条规则。"""
    groups = collections.defaultdict(list)
    for h in hits:
        r = by_id[h['rule']]
        groups[(keyf(h), r['结论']['领域'])].append((E.specificity(r), r, h))
    out = []
    for (k, dom), xs in groups.items():
        ys, two = E.resolve(xs)
        out.append((k, dom, two, ys))
    return out


def statements(rd, by_id):
    """第一版成稿里实际列出的每一句说法，带出处、方向强度与归类。"""
    out = []
    for part, layer in LAYERS:
        if layer == '先天':
            gs = kept_groups(rd[part], by_id, lambda h: h['palace'])
            buckets = [((layer, k), dom, two, ys) for k, dom, two, ys in gs]
        else:
            by = collections.defaultdict(list)
            for h in rd[part]:
                by[scope_key(layer, h)].append(h)
            buckets = []
            for sk, hs in by.items():
                for k, dom, two, ys in kept_groups(hs, by_id, lambda h: h['palace']):
                    buckets.append(((layer, sk), dom, two, ys))
        for (lay, sk), dom, two, ys in buckets:
            for spec, r, h in ys:
                out.append({'时间层': lay, '位置': sk, '宫': h['palace'], '领域': dom, '组内两说': two, '规则': r['rule_id'], 'T': r['T'],
                            '规则宫': r['宫'], '内容': r['结论']['内容'], '方向': h['polarity'], '强度': h['strength'],
                            '原方向': r['结论']['方向'], '原强度': r['结论']['强度'], '算子': h['operator_notes'], '具体程度': spec,
                            '推导': h['via'], '借对宫': '借' in h['via'], '涉生死': bool(r['结论'].get('涉生死')),
                            '岁段': tuple(h['span']) if 'span' in h else None, '年支': h.get('year_branch'), '虚岁': tuple(h['ages']) if 'ages' in h else None,
                            'claims': rule_claims(r)})
    return out


def phrase2(c, who, cite, extra=()):
    """第一版 phrase 加上额外标记（如「已取舍」）；extra 为空时与 E.phrase 逐字相同。"""
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
    tags += list(extra)
    return txt + (f"（{'，'.join(tags)}）" if tags else '')


def render_text_v2(rd, by_id, synth=None, cite=True, only_synthesis=False):
    """第二版成稿。synth 为 None 时与 E.render_text 逐字相同（回归检查用）；
    synth 给出时开头加「综合论断」，各节被取舍掉的说法加「已取舍」标记；only_synthesis 时只出「综合论断」一节（M4c 第二组用）。"""
    L = []
    mark = (synth or {}).get('marks', {})   # (时间层, 位置, 内容) → 标记文字列表

    def ext(layer, key, c):
        return mark.get((layer, key, c['内容']), ())
    if synth is not None:
        L += synth_lines(synth, cite)
        if only_synthesis:
            return '\n'.join(L)
    nat = E.summarize(rd['natal'], by_id, lambda h: h['palace'])
    by = collections.defaultdict(list)
    for g in nat:
        by[g['键']].append(g)
    order = ['长相', '个性', '行为', '路线', '成就', '财', '婚姻', '子女', '父母', '兄弟', '朋友合伙', '健康', '祖业田宅', '福德', '官非', '意外', '寿元', '其他']
    srt = lambda gs: sorted(gs, key=lambda g: order.index(g['领域']) if g['领域'] in order else 99)

    def line(name, g):
        who = E.WHO[name]
        return f"{g['领域']}：" + '；'.join(phrase2(c, who, cite, ext('先天', name, c)) for c in g['结论']) + ('〔两说〕' if g['两说'] else '')
    L.append('一、命宫（先天本人：长相、个性、行为模式、路线与成败）')
    for g in srt(by['命宫']):
        L.append('  ' + line('命宫', g))
    if not by['命宫']:
        L.append('  （知识库中没有可用于此命宫的断语）')
    L.append(f"二、身宫（后天发展）：在{rd['shen'] or '（各候选不一致）'}")
    for g in srt(by.get(rd['shen'], []) if rd['shen'] else []):
        cs = [c for c in g['结论'] if c['推导'].startswith('身宫规则')]
        if cs:
            L.append('  ' + f"{g['领域']}：" + '；'.join(phrase2(c, '本人', cite, ext('先天', rd['shen'], c)) for c in cs))
    L.append('三、三方四正（财帛、官禄、迁移）')
    for name in ('财帛', '官禄', '迁移'):
        for g in srt(by[name]):
            L.append(f'  {name}·' + line(name, g))
    L.append('四、生年四化')
    L.append('  ' + ('，'.join(f"化{x['化']}在{x['宫']}（{x['星']}）" for x in rd['sihua']) or '（各候选不一致）'))
    L.append('五、六亲与诸宫')
    for name in ('兄弟', '夫妻', '子女', '仆役', '父母', '田宅', '福德', '疾厄'):
        for g in srt(by[name]):
            L.append(f'  {name}（{E.WHO[name]}）·' + line(name, g))
    L.append('六、十年大限（十年为主）')
    dxg = collections.defaultdict(list)
    for h in rd['daxian']:
        dxg[(h['span'], h['palace'])].append(h)
    for (span, pal), hs in sorted(dxg.items()):
        gs = E.summarize(hs, by_id, lambda h: h['palace'])
        key = (tuple(span), pal)
        body = '；'.join(f"{g['领域']}：" + '；'.join(phrase2(c, '本人', cite, ext('大限', key, c)) for c in g['结论']) for g in srt(gs))
        L.append(f'  {span[0]}–{span[1]}岁（行运走本命{pal}，这十年的主题偏{E.WHO[pal]}）：{body}')
    if not rd['daxian']:
        L.append('  （知识库中没有可用于各大限的断语）')
    L.append('七、流年（流年为辅；按年支每十二年一轮，岁数为虚岁）')
    lng = collections.defaultdict(list)
    for h in rd['liunian']:
        lng[(h['year_branch'], h['palace'], tuple(h['ages']))].append(h)
    for (yb, pal, ages), hs in sorted(lng.items(), key=lambda t: t[0][2][0]):
        gs = E.summarize(hs, by_id, lambda h: h['palace'])
        key = (yb, pal, ages)
        body = '；'.join(f"{g['领域']}：" + '；'.join(phrase2(c, '本人', cite, ext('流年', key, c)) for c in g['结论']) for g in srt(gs))
        L.append(f"  {yb}年（虚岁 {'、'.join(map(str, ages[:8]))}…，走本命{pal}）：{body}")
    if not rd['liunian']:
        L.append('  （知识库中没有可用于各流年的断语）')
    L.append('八、迷津（适合走的路，与一辈子要注意的事；只归拢上文结论）')
    seen, route = set(), []
    for name in ('命宫', rd['shen'], '官禄', '财帛', '迁移'):
        for g in by.get(name, []) if name else []:
            if g['领域'] in ('路线', '成就'):
                for c in g['结论']:
                    if c['方向'] != '凶' and c['内容'] not in seen:
                        seen.add(c['内容']); route.append(phrase2(c, '本人', cite, ext('先天', name, c)))
    L.append('  适合的路：' + ('；'.join(route) if route else '（没有可归拢的路线断语）'))
    warn, seen = [], set()
    for g in nat:
        for c in g['结论']:
            if c['方向'] == '凶' and c['强度'] == '断' and c['内容'] not in seen:
                seen.add(c['内容']); warn.append(f"{g['键']}：" + phrase2(c, E.WHO[g['键']], cite, ext('先天', g['键'], c)))
    for h in rd['daxian']:
        r = by_id[h['rule']]
        if h['polarity'] == '凶' and h['strength'] == '断':
            c = {'内容': r['结论']['内容'], '涉生死': bool(r['结论'].get('涉生死')), '层': h['layer'], '推导': h['via'], '算子': h['operator_notes'],
                 '出处': {'T': r['T']}}
            k = f"{h['span'][0]}–{h['span'][1]}岁：" + phrase2(c, '本人', cite, ext('大限', (tuple(h['span']), h['palace']), c))
            if k not in seen:
                seen.add(k); warn.append(k)
    L.append('  要注意：' + ('；'.join(warn) if warn else '（没有断定为凶的结论）'))
    return '\n'.join(L)


# ---------------- 综合取舍：调度、「已取舍」标记、成稿 ----------------
LABEL = {
    '路线': {'当官': '当官（公职、文官、教职）', '武职': '武职（军警、司法、外交）', '经商': '经商（做生意、自己做事业）',
             '受雇': '受雇（在私人企业上班、领薪水、辅佐）', '专业': '专业（专业技术、自由业、才艺）',
             '非当官': '不走公职', '非武职': '不做武职', '非经商': '不做生意', '非受雇': '不受雇于人', '非专业': '不走专业技术'},
    '成就': {'高': '高（主管、掌权、名声）', '低': '低（佐才、副职、位高无权、事倍功半）'},
    '婚姻': {'婚变': '婚变（生离或死别）', '多婚': '不止一次婚姻', '偏房': '偏房（没有名分）', '不好': '婚姻不好', '好': '婚姻好',
             '早婚': '早婚', '晚婚': '晚婚', '不成': '婚事难成', '会结婚': '会结婚'},
    '子女': {'无子': '本人命盘无子', '有子': '有子', '凶': '子女凶（冲突、难管或远离）'},
    '父母': {'父·凶': '父亲有凶', '母·凶': '母亲有凶', '父母·凶': '父母有凶', '父·吉': '父亲吉', '母·吉': '母亲吉', '父母·吉': '父母吉'},
    '兄弟': {'凶': '兄弟有凶（不和、夭折、是非、合伙破财）', '吉': '兄弟得利'},
    '祖业田宅': {'有祖业': '有祖业', '无祖业': '无祖业', '破祖业': '破祖业（会把父母亲的财产耗掉）'},
}


def label(attr, v):
    return LABEL.get(attr, {}).get(v, v)


def synthesize(rd, by_id, charts, disabled=()):
    """按《取舍规则表》做综合取舍。charts＝并列候选的 Chart 列表（随机盘一张）；disabled＝关掉的取舍步骤（M4c 对称留一用，平时为空）。
    返回 {'属性': [各属性结果], 'marks': {...}}。"""
    import v2_synth_A as SA, v2_synth_B as SB, v2_synth_C as SC
    from v2_synth_common import Ctx
    ctx = Ctx(rd, by_id, charts, disabled)
    res = SA.synthesize(ctx) + SB.synthesize(ctx) + SC.synthesize(ctx)
    return {'属性': res, 'marks': compute_marks(res)}


def scopes(R):
    """一个属性结果里的全部取舍段：先天、各大限、各大限里的流年。"""
    yield R['先天']
    for d in R['大限']:
        if d.get('大限'):
            yield d['大限']
        for y in d.get('流年', []):
            yield y


def compute_marks(results):
    """「已取舍」：某属性被淘汰或不作证据的说法，若同一句（时间层、位置、内容）在任何一段都没有被采用，就在细目里标出。
    作为前提照列的（如「有祖业而破」里的有祖业）、两说另列里的，算采用。"""
    key = lambda x: (x['时间层'], x['位置'], x['内容'])
    elim, keep = collections.defaultdict(set), collections.defaultdict(set)
    for R in results:
        attr = R['属性']
        for sc in scopes(R):
            c = sc.get('contest')
            used = set(sc.get('主断', [])) | {v for p in sc.get('两说', []) for v in p}
            if c is not None:
                for v, ss in c.support.items():
                    for x in ss:
                        (keep if v in used else elim)[key(x)].add(attr)
                for _, v, x in c.removed:
                    elim[key(x)].add(attr)
            for _, x in sc.get('不取', []):
                elim[key(x)].add(attr)
            for x in sc.get('前提', []):
                keep[key(x)].add(attr)
            for t in sc.get('两说另列', []):
                for ss in t[4:6]:
                    for x in ss:
                        keep[key(x)].add(attr)
    out = {}
    for k, attrs in elim.items():
        left = sorted(attrs - keep.get(k, set()))
        if left:
            out[k] = ['已取舍：' + '、'.join(left)]
    return out


CAP_QINGXIANG = ('父母', '兄弟', '子女')   # 六亲：主断最高只作倾向（B 子女第7步、C G9）


def _strength(attr, ss, main=True):
    """强度照列各条修正后的强度（C 组 G9、R3 第7步）：几条强度相同就标那一种，不同就标「断、倾向各有」；
    六亲（父母、兄弟、子女）只在主断上封顶为倾向（规则表「出主断时强度最高只写倾向」）。带出处时另逐条列出。"""
    if attr in CAP_QINGXIANG and main:
        return '倾向'
    sts = {x['强度'] for x in ss}
    return sts.pop() if len(sts) == 1 else '断、倾向各有'



def _support(sc, v):
    c = sc.get('contest')
    if c is not None and v in c.support:
        return c.support[v]
    return sc.get('依据', {}).get(v, [])


def _src(ss, cite):
    if not cite or not ss:
        return ''
    return '（' + '、'.join(sorted({f"{x['宫']}{x['规则']}·{x['强度']}" for x in ss})) + '）'


def _val(attr, sc, v, cite, main=True):
    ss = _support(sc, v)
    lab = sc.get('合写', {}).get(v) or label(attr, v)
    return f"{lab}〔{_strength(attr, ss, main)}〕" + _src(ss, cite) if ss else lab


def _tag(sid_list, cite):
    return f"（{'，'.join(sid_list)}）" if cite and sid_list else ''


def group_pairs(pairs, src):
    """两说对子按共同的取值归组，便于阅读：同一个取值与几个取值各自两说时，写成「一说X；一说A、B」。只改排版，不改取舍。"""
    left = [tuple(sorted(p)) for p in pairs]
    out = []
    while left:
        cnt = collections.Counter(v for p in left for v in p)
        hub = max(sorted(cnt), key=lambda v: cnt[v])
        mine = [p for p in left if hub in p]
        others = sorted(p[0] if p[1] == hub else p[1] for p in mine)
        sids = sorted({src.get(p, ('', ''))[0] for p in mine} - {''})
        out.append((hub, others, sids))
        left = [p for p in left if hub not in p]
    return out


def _scope_text(attr, sc, cite):
    """一段取舍结果写成一句：主断（标修正后的强度）；两说（每一说标强度）；附注。"""
    parts = []
    main = [_val(attr, sc, v, cite) for v in sc.get('主断', [])]
    if main:
        won = sorted({w[0] for w in sc.get('淘汰', {}).values()}) if cite else []
        parts.append('、'.join(main) + _tag(won, cite))
    for hub, others, sids in group_pairs(sc.get('两说', []), sc.get('两说出处', {})):
        if len(others) == 1:
            parts.append(f"〔两说：{_val(attr, sc, hub, cite, False)}／{_val(attr, sc, others[0], cite, False)}〕" + _tag(sids, cite))
        else:
            parts.append(f"〔两说：一说{_val(attr, sc, hub, cite, False)}；一说{'、'.join(_val(attr, sc, o, cite, False) for o in others)}〕" + _tag(sids, cite))
    for t in sc.get('两说另列', []):
        x, y, sid = t[0], t[1], t[2]
        sx, sy = (t[4], t[5]) if len(t) >= 6 else ([], [])
        fx = f"{label(attr, x)}〔{_strength(attr, sx, False)}〕{_src(sx, cite)}" if sx else label(attr, x)
        fy = f"{label(attr, y)}〔{_strength(attr, sy, False)}〕{_src(sy, cite)}" if sy else label(attr, y)
        parts.append(f"〔两说：{fx}／{fy}〕" + _tag([sid], cite))
    for v, x in sc.get('外地', []):
        parts.append(f"到外地：{label(attr, v)}" + _src([x], cite))
    for k, v, x in sc.get('若走', []):
        parts.append(f"若走{label('路线', k).split('（')[0]}则{label(attr, v).split('（')[0]}" + _src([x], cite))
    if sc.get('置产'):
        parts.append('置产：' + '；'.join(f"{x['内容']}〔{x['强度']}〕" + _src([x], cite) for x in sc['置产']))
    notes = [n for n in sc.get('附注', []) if n[0] not in ('A路2', 'A成2', 'A成3') or '吉处藏凶' in n[1]]
    for sid, txt, ts in notes:
        parts.append(f"（{txt}）" + _tag([sid] + list(ts), cite))
    return '；'.join(parts)


def synth_lines(synth, cite):
    """「综合论断」一节。流年层各年的说法不在这里逐年列出（见第七节），只列先天、各大限与规则表规定的应期（技术选择）。"""
    L = ['〇、综合论断（按倪师讲过的取舍道理，把下文各宫、各运限的说法归拢成主断；被取舍掉的说法仍在下文，标「已取舍」；定不下的写「两说」）']
    for R in synth['属性']:
        t = _scope_text(R['属性'], R['先天'], cite)
        head = R['属性'] if R['对象'] == R['属性'] else f"{R['属性']}（{R['对象']}）"
        L.append(f"  {head}：" + (t or '（没有可归拢的说法）'))
    rows = collections.defaultdict(list)
    for R in synth['属性']:
        for d in R['大限']:
            t = _scope_text(R['属性'], d['大限'], cite) if d.get('大限') else ''
            extra = [f"（{x[1]}）" + _tag([x[0]] + list(x[2]), cite) for x in d.get('附注', [])]
            if d.get('婚变应期'):
                extra.append('（婚变应期：' + '、'.join(f"虚岁 {a}" + (f"，{k}" if k else '') for a, k in d['婚变应期']) + '）')
            body = '；'.join([x for x in [t] if x] + extra)
            if body:
                rows[tuple(d['岁段'])].append(f"{R['属性']} {body}")
    if rows:
        L.append('  各十年（大限为主，只管该岁数区间）：')
        for span in sorted(rows):
            L.append(f"    {span[0]}–{span[1]}岁：" + '　'.join(rows[span]))
    return L
