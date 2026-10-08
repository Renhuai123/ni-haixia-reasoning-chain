"""倪师推理链：抽取（或裁定）结果的格式核验与合并 v1（只核验、计数、合并，不改任何内容；依据《00_推理链方案_v1.md》三、四）。
逐批核对 <存档目录>/Kxx_<角色>.json：
- 每条倪师条目都有且只有一项；
- 每一步：类型（定性步／推理步）、宫、适用合法；定性步至少一个条件，推理步至少一个前提且写了连接；
  条件、附加条件逐条符合知识库的写法（沿用 kb_validate_v2.check_cond，含「天空」应写地空）；
  前提与结论的层只许用说明里列的那些，判断不为空；结论的方向、强度合法；
  原话摘录逐字出自该条原话，结论的原话说法出自原话摘录，前提的原话说法出自该条原话（都去掉空白后比较）；
  「可操作」与是否用了「其他:」一致。
- 判断里出现十四主星星名的，记为提醒（不算不合格）。
有不合格：照样写出合并结果，该步带 valid=false 并逐条列入 problems；引擎不得使用 valid=false 的步。
写出 <out>；文件已存在就停。用法：python3 chain_validate_v1.py --packets <材料目录> --returns <存档目录> --role 甲 --out <新文件>"""
import argparse, collections, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005'))
from kb_validate_v2 import check_cond, PALACE_SET, SCOPES, MAJOR

LAYERS = ['定性', '长相', '个性', '行为', '路线', '成败', '财', '婚姻', '子女', '父母', '兄弟', '朋友合伙', '健康', '祖业田宅', '福德', '官非', '意外', '寿元', '其他']
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
norm = lambda s: re.sub(r'\s+', '', s if isinstance(s, str) else '')


def check_step(s, text):
    errs, warns, parsed, parsed_extra = [], [], [], []
    kind = s.get('类型')
    if kind not in ('定性步', '推理步'): errs.append('类型不合法')
    if s.get('宫') not in PALACE_SET: errs.append('宫不合法')
    if s.get('适用') not in SCOPES: errs.append('适用不合法')

    def conds(key, out, need):
        cs = s.get(key)
        if cs is None:
            cs = []
        if not isinstance(cs, list):
            errs.append(f'{key}不是列表'); return
        if need and not cs:
            errs.append(f'{key}为空')
        for c in cs:
            ok, res = check_cond(str(c))
            if ok: out.append(res)
            else: errs.append(f'{key}「{c}」：{res}')
    if kind == '定性步':
        conds('条件', parsed, True)
    elif kind == '推理步':
        conds('附加条件', parsed_extra, False)
        pre = s.get('前提')
        if not isinstance(pre, list) or not pre:
            errs.append('推理步没有前提')
        else:
            for p in pre:
                if not isinstance(p, dict) or p.get('层') not in LAYERS or not str(p.get('判断', '')).strip():
                    errs.append(f'前提不合法：{p}'); continue
                if not norm(p.get('原话说法')) or norm(p.get('原话说法')) not in norm(text):
                    errs.append(f'前提「{p.get("判断")}」的原话说法不是原话的逐字片段')
        if not str(s.get('连接', '')).strip(): errs.append('推理步没写连接')
    allp = parsed + parsed_extra
    if any('天空' in (x.get('stars') or []) for x in allp): errs.append('倪师说的天空应写地空')
    if bool(s.get('可操作')) == any(x.get('t') == '其他' for x in allp): errs.append('可操作与「其他:」不一致')
    con = s.get('结论') or {}
    if con.get('层') not in LAYERS: errs.append('结论层不合法')
    if not str(con.get('判断', '')).strip(): errs.append('结论判断为空')
    if con.get('方向') not in ('吉', '凶', '中'): errs.append('方向不合法')
    if con.get('强度') not in ('断', '倾向'): errs.append('强度不合法')
    q = norm(s.get('原话摘录'))
    if not q or q not in norm(text): errs.append('原话摘录不是原话的逐字片段')
    if not norm(con.get('原话说法')) or norm(con.get('原话说法')) not in q: errs.append('结论的原话说法不在原话摘录里')
    for p in ([con] + [p for p in (s.get('前提') or []) if isinstance(p, dict)]):
        if any(st in str(p.get('判断', '')) for st in MAJOR): warns.append(f'判断「{p.get("判断")}」里有星名')
    return errs, warns, parsed, parsed_extra


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('packets', 'returns', 'role', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    man = json.load(open(os.path.join(a.packets, 'manifest.json'), encoding='utf-8'))
    steps, methods, problems, warnings, inputs = [], [], [], [], {}
    for b in man['batches']:
        text = {it['T']: it for it in json.load(open(os.path.join(a.packets, b['batch'], 'batch.json'), encoding='utf-8'))['倪师条目']}
        p = os.path.join(a.returns, f"{b['batch']}_{a.role}.json")
        if not os.path.exists(p):
            problems.append({'batch': b['batch'], 'problem': '没有可解析的回复'}); continue
        inputs[b['batch']] = sha(p)
        items = json.load(open(p, encoding='utf-8')).get('items', [])
        got = [i.get('T') for i in items]
        if sorted(got) != sorted(b['items']) or len(got) != len(set(got)):
            problems.append({'batch': b['batch'], 'problem': '条目不一一对应', 'missing': sorted(set(b['items']) - set(got)), 'extra': sorted(set(got) - set(b['items']))})
        for it in items:
            T = it.get('T')
            if T not in text:
                continue
            if str(it.get('方法', '')).strip():
                methods.append({'T': T, '方法': it['方法'], 'batch': b['batch']})
            ss = it.get('步')
            if not isinstance(ss, list):
                problems.append({'T': T, 'problem': '步不是列表'}); continue
            for j, s in enumerate(ss, 1):
                sid = f'{T}-{a.role}-s{j}'
                if not isinstance(s, dict):
                    problems.append({'step_id': sid, 'problem': '步不是对象'}); continue
                errs, warns, parsed, parsed_extra = check_step(s, text[T]['原话'])
                steps.append({'step_id': sid, 'T': T, '分P': text[T]['分P'], '时间': text[T]['时间'], 'batch': b['batch'], 'valid': not errs, 'errors': errs,
                              'parsed_conditions': parsed, 'parsed_extra': parsed_extra,
                              **{k: s.get(k) for k in ('类型', '宫', '适用', '条件', '前提', '附加条件', '结论', '连接', '原话摘录', '命例特指', '可操作', '说明')}})
                if errs: problems.append({'step_id': sid, 'problem': errs})
                if warns: warnings.append({'step_id': sid, 'warning': warns})
    c = collections.Counter((s['类型'], s['valid']) for s in steps)
    res = {'schema': 'chain-validated-v1', 'role': a.role, 'inputs_sha256': inputs,
           'counts': {'步': len(steps), '合格': sum(s['valid'] for s in steps), '定性步': c[('定性步', True)] + c[('定性步', False)],
                      '推理步': c[('推理步', True)] + c[('推理步', False)], '有步的条目': len({s['T'] for s in steps}),
                      '有推理步的条目': len({s['T'] for s in steps if s['类型'] == '推理步'}), '方法': len(methods),
                      'problems': len(problems), 'warnings': len(warnings)},
           'steps': steps, 'methods': methods, 'problems': problems, 'warnings': warnings}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(res['counts'], ensure_ascii=False))


if __name__ == '__main__':
    main()
