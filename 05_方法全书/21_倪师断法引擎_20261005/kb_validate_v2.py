"""M1 知识库抽取结果的格式核验与合并 v2（只核验、计数、合并，不改任何内容；与 v1 只差：认可财星、贵星两个星类与「无化」写法，材料目录为 kb_packets_v2）。
逐批核对：
- 每条倪师条目都有且只有一项；类型是「规则／方法／不收」之一；规则型至少一条规则，方法型写了方法，不收型写了理由。
- 每条规则：宫、适用、结论各字段取值合法；条件逐条符合说明里的写法，星名是排盘引擎里有的星名或约定星类；原话摘录逐字出自该条原话（去掉空白后比较）。
- 「可操作」与条件是否用了「其他:」一致。
有任何不合格：照样写出合并结果，但把不合格项逐条列入 problems，规则带 valid=false，引擎不得使用 valid=false 的规则。
用法：python3 kb_validate_v2.py --returns kb_returns_v1 --out <新目录>"""
import argparse, collections, hashlib, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PALACES = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄', '迁移', '仆役', '官禄', '田宅', '福德', '父母']
PALACE_SET = set(PALACES) | {'身宫', '任一宫'}
SCOPES = {'先天', '大限', '流年', '小限'}
DOMAINS = {'长相', '个性', '行为', '路线', '成就', '财', '婚姻', '子女', '父母', '兄弟', '朋友合伙', '健康', '祖业田宅', '福德',
           '官非', '意外', '寿元', '其他'}
MAJOR = ['紫微', '天机', '太阳', '武曲', '天同', '廉贞', '天府', '太阴', '贪狼', '巨门', '天相', '天梁', '七杀', '破军']
STARS = set(MAJOR) | {'副截', '副旬', '地劫', '地空', '大耗', '天伤', '天使', '天刑', '天哭', '天月', '天空', '天虚', '孤辰', '寡宿', '截空', '擎羊',
                      '旬空', '火星', '蜚廉', '铃星', '阴煞', '陀罗', '三台', '八座', '凤阁', '华盖', '台辅', '右弼', '天喜', '天官', '天寿', '天巫',
                      '天德', '天才', '天福', '天贵', '天钺', '天马', '天魁', '封诰', '左辅', '年解', '恩光', '文昌', '文曲', '月德', '禄存', '红鸾',
                      '解神', '龙池', '劫煞', '咸池', '天厨', '天姚', '破碎', '龙德'}
CLASSES = {'吉星': ['左辅', '右弼', '文昌', '文曲', '天魁', '天钺'], '杀星': ['擎羊', '陀罗', '火星', '铃星', '地空', '地劫'],
           '杀破狼': ['七杀', '破军', '贪狼'], '主星': MAJOR, '财星': ['禄存', '武曲', '贪狼'], '贵星': ['紫微', '太阳', '武曲', '天同']}
BRANCH = '子丑寅卯辰巳午未申酉戌亥'
HUA = {'禄', '权', '科', '忌'}
WHERE = {'本宫', '对宫', '三方', '三方四正'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
norm = lambda s: re.sub(r'\s+', '', s or '')


def check_cond(c):
    """返回 (是否合法, 解析结果或错误说明)。"""
    if c == '空宫':
        return True, {'t': '空宫'}
    if ':' not in c:
        return False, '不是「键:值」写法'
    k, v = c.split(':', 1)
    if k == '其他':
        return (bool(v.strip()), {'t': '其他', 'text': v.strip()})
    stars = lambda s: [x for x in s.split(',') if x]
    m = re.fullmatch(r'(本宫|对宫|三方|三方四正)(有|无)', k)
    if m:
        xs = stars(v)
        bad = [x for x in xs if x not in STARS and x not in CLASSES]
        return (not bad and bool(xs), {'t': '有无', 'where': m.group(1), 'has': m.group(2) == '有', 'stars': xs} if not bad and xs else f'星名不合法: {bad or "空"}')
    if k == '夹':
        xs = stars(v)
        bad = [x for x in xs if x not in STARS and x not in CLASSES]
        return (not bad and 1 <= len(xs) <= 2, {'t': '夹', 'stars': xs} if not bad else f'星名不合法: {bad}')
    if k == '亮度':
        m = re.fullmatch(r'(.+)=(庙旺|平闲|陷)', v)
        return (bool(m) and m.group(1) in STARS, {'t': '亮度', 'star': m.group(1), 'level': m.group(2)} if m and m.group(1) in STARS else '亮度写法不合法')
    if k == '化':
        m = re.fullmatch(r'(.+)=([禄权科忌])', v)
        return (bool(m) and m.group(1) in STARS, {'t': '化', 'star': m.group(1), 'hua': m.group(2)} if m and m.group(1) in STARS else '化写法不合法')
    m = re.fullmatch(r'(本宫|对宫|三方|三方四正)(无?)化', k)
    if m:
        hs = [x for x in v.split(',') if x]
        ok = bool(hs) and all(h in HUA for h in hs)
        return (ok, {'t': '位化', 'where': m.group(1), 'hua': hs, 'has': m.group(2) != '无'} if ok else '位化写法不合法')
    if k == '宫支':
        bs = v.split('|')
        return (bool(bs) and all(len(b) == 1 and b in BRANCH for b in bs), {'t': '宫支', 'branches': bs} if all(len(b) == 1 and b in BRANCH for b in bs) else '宫支不合法')
    if k == '性别':
        return (v in ('男', '女'), {'t': '性别', 'g': v} if v in ('男', '女') else '性别不合法')
    if k == '身宫':
        return (v in PALACES, {'t': '身宫', 'palace': v} if v in PALACES else '身宫写法不合法')
    if k == '格':
        return (bool(v.strip()), {'t': '格', 'name': v.strip()})
    if k == '年龄':
        m = re.fullmatch(r'(\d+)(?:-(\d+))?', v)
        return (bool(m), {'t': '年龄', 'lo': int(m.group(1)), 'hi': int(m.group(2) or m.group(1))} if m else '年龄写法不合法')
    return False, f'未知条件键: {k}'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--returns', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    man = json.load(open(os.path.join(HERE, 'kb_packets_v2/manifest.json'), encoding='utf-8'))
    text = {}
    for b in man['batches']:
        for it in json.load(open(os.path.join(HERE, 'kb_packets_v2', b['batch'], 'batch.json'), encoding='utf-8'))['倪师条目']:
            text[it['T']] = it
    rules, methods, dropped, problems, inputs = [], [], [], [], {}
    for b in man['batches']:
        p = os.path.join(a.returns, b['batch'] + '.json')
        if not os.path.exists(p):
            problems.append({'batch': b['batch'], 'problem': '没有可解析的回复'}); continue
        inputs[b['batch']] = sha(p)
        items = json.load(open(p, encoding='utf-8')).get('items', [])
        got = [i.get('T') for i in items]
        if sorted(got) != sorted(b['items']) or len(got) != len(set(got)):
            problems.append({'batch': b['batch'], 'problem': '条目不一一对应', 'missing': sorted(set(b['items']) - set(got)), 'extra': sorted(set(got) - set(b['items']))})
        for it in items:
            T = it.get('T'); kind = it.get('类型')
            if T not in text:
                continue
            if kind == '方法':
                if not str(it.get('方法', '')).strip():
                    problems.append({'T': T, 'problem': '方法型没写方法'})
                methods.append({'T': T, '方法': it.get('方法', ''), 'batch': b['batch']})
            elif kind == '不收':
                if not str(it.get('不收理由', '')).strip():
                    problems.append({'T': T, 'problem': '不收没写理由'})
                dropped.append({'T': T, '理由': it.get('不收理由', ''), 'batch': b['batch']})
            elif kind == '规则':
                rs = it.get('规则') or []
                if not rs:
                    problems.append({'T': T, 'problem': '规则型没有规则'})
                if str(it.get('方法', '')).strip():
                    methods.append({'T': T, '方法': it.get('方法', ''), 'batch': b['batch']})
                for j, r in enumerate(rs, 1):
                    errs, parsed = [], []
                    if r.get('宫') not in PALACE_SET: errs.append('宫不合法')
                    if r.get('适用') not in SCOPES: errs.append('适用不合法')
                    conds = r.get('条件') or []
                    if not isinstance(conds, list): errs.append('条件不是列表'); conds = []
                    for c in conds:
                        ok, res = check_cond(str(c))
                        if ok: parsed.append(res)
                        else: errs.append(f'条件「{c}」：{res}')
                    if any('天空' in (x.get('stars') or []) for x in parsed): errs.append('倪师说的天空应写地空（排盘引擎的天空是另一颗星）')
                    uses_other = any(x.get('t') == '其他' for x in parsed)
                    if bool(r.get('可操作')) == uses_other: errs.append('可操作与「其他:」不一致')
                    con = r.get('结论') or {}
                    if con.get('领域') not in DOMAINS: errs.append('领域不合法')
                    if con.get('方向') not in ('吉', '凶', '中'): errs.append('方向不合法')
                    if con.get('强度') not in ('断', '倾向'): errs.append('强度不合法')
                    if not str(con.get('内容', '')).strip(): errs.append('结论内容为空')
                    q = norm(r.get('原话摘录'))
                    if not q or q not in norm(text[T]['原话']): errs.append('原话摘录不是原话的逐字片段')
                    rid = f'{T}-r{j}'
                    rules.append({'rule_id': rid, 'T': T, '分P': text[T]['分P'], '时间': text[T]['时间'], 'batch': b['batch'], 'valid': not errs,
                                  'errors': errs, 'parsed_conditions': parsed, **{k: r.get(k) for k in ('宫', '适用', '条件', '结论', '原话摘录', '命例特指', '可操作', '说明')}})
                    if errs:
                        problems.append({'rule_id': rid, 'problem': errs})
            else:
                problems.append({'T': T, 'problem': f'类型不合法: {kind}'})
    os.makedirs(a.out)
    stat = {'rules': len(rules), 'valid_rules': sum(r['valid'] for r in rules), 'operational_valid_rules': sum(r['valid'] and bool(r['可操作']) for r in rules),
            'case_specific_rules': sum(bool(r['命例特指']) for r in rules), 'methods': len(methods), 'dropped': len(dropped), 'problems': len(problems),
            'by_palace': dict(collections.Counter(r['宫'] for r in rules if r['valid'])),
            'by_domain': dict(collections.Counter((r['结论'] or {}).get('领域') for r in rules if r['valid'])),
            'by_scope': dict(collections.Counter(r['适用'] for r in rules if r['valid'])),
            'by_strength': dict(collections.Counter((r['结论'] or {}).get('强度') for r in rules if r['valid']))}
    out = {'schema': 'ni-kb-merged-v2', 'inputs_sha256': inputs, 'stats': stat, 'rules': rules, 'methods': methods, 'dropped': dropped, 'problems': problems}
    open(os.path.join(a.out, 'kb_merged_v2.json'), 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(stat, ensure_ascii=False))


if __name__ == '__main__':
    main()
