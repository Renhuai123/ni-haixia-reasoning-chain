"""倪师推理链：裁定结果的核验、合并与一致程度 v1（只核验、计数、合并，不改任何内容；依据《00_推理链方案_v1.md》四）。
逐批核对 <裁定存档目录>/Kxx_裁定.json：
- 每条倪师条目都有且只有一项；
- 甲、乙的每个步编号（裁定材料包 manifest 的 step_ids）都有着落且只出现一次：在某个定稿步的「来源」里，或在「不收」里；不在材料里的编号算不合格；
- 每个定稿步照抽取的格式规定逐项核验（沿用 chain_validate_v1.check_step）；补入的步（来源为空）「改动」要以「补」开头。
一致程度（只作描述）：
- 按条：甲、乙对「这条原话有没有推理步」判断一致的比例（直接比两人的抽取结果）；
- 按步：定稿步里来源同时有甲、乙的、只有甲或只有乙的、补入的各多少；甲、乙各自的步被收、被不收各多少。
写出 <out>；文件已存在就停。用法：python3 chain_adjudicate_validate_v1.py --adj-packets <裁定材料目录> --adj-returns <裁定存档目录> --out <新文件>"""
import argparse, collections, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from chain_validate_v1 import check_step

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('adj-packets', 'adj-returns', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    man = json.load(open(os.path.join(a.adj_packets, 'manifest.json'), encoding='utf-8'))
    steps, methods, problems, warnings, inputs = [], [], [], [], {}
    agree = collections.Counter(); src = collections.Counter(); per_role = collections.Counter()
    for b in man['batches']:
        B = b['batch']
        text = {it['T']: it for it in json.load(open(os.path.join(a.adj_packets, B, 'batch.json'), encoding='utf-8'))['倪师条目']}
        ex = json.load(open(os.path.join(a.adj_packets, B, 'extractions.json'), encoding='utf-8'))['条目']
        for row in ex:
            r = [any(s.get('类型') == '推理步' for s in row[role]['步']) for role in '甲乙']
            agree['条目'] += 1; agree['推理步有无一致'] += r[0] == r[1]
            agree['两人都有推理步'] += r[0] and r[1]; agree['只一人有推理步'] += r[0] != r[1]
        p = os.path.join(a.adj_returns, f'{B}_裁定.json')
        if not os.path.exists(p):
            problems.append({'batch': B, 'problem': '没有可解析的裁定'}); continue
        inputs[B] = sha(p)
        items = json.load(open(p, encoding='utf-8')).get('items', [])
        got = [i.get('T') for i in items]
        if sorted(got) != sorted(b['items']) or len(got) != len(set(got)):
            problems.append({'batch': B, 'problem': '条目不一一对应', 'missing': sorted(set(b['items']) - set(got)), 'extra': sorted(set(got) - set(b['items']))})
        valid_ids = set(b['step_ids'])
        used = collections.Counter()
        for it in items:
            T = it.get('T')
            if T not in text:
                continue
            if str(it.get('方法', '')).strip():
                methods.append({'T': T, '方法': it['方法'], 'batch': B})
            for d in it.get('不收') or []:
                used[d.get('编号')] += 1
                per_role[(str(d.get('编号', '')).split('-')[-1][:1], '不收')] += 1
                if not str(d.get('理由', '')).strip():
                    problems.append({'T': T, 'problem': f"不收没写理由：{d.get('编号')}"})
            for j, s in enumerate(it.get('步') or [], 1):
                sid = f'{T}-c{j}'
                if not isinstance(s, dict):
                    problems.append({'step_id': sid, 'problem': '步不是对象'}); continue
                errs, warns, parsed, parsed_extra = check_step(s, text[T]['原话'])
                srcs = s.get('来源') if isinstance(s.get('来源'), list) else []
                if not isinstance(s.get('来源'), list):
                    errs.append('来源不是列表')
                for x in srcs:
                    used[x] += 1
                    per_role[(str(x).split('-')[-1][:1], '收')] += 1
                roles = {str(x).split('-')[-1][:1] for x in srcs}
                kind = '甲乙' if roles >= {'甲', '乙'} else ('只甲' if roles == {'甲'} else ('只乙' if roles == {'乙'} else '补入'))
                if kind == '补入' and not str(s.get('改动', '')).startswith('补'):
                    errs.append('来源为空但改动没写「补」')
                src[kind] += 1
                steps.append({'step_id': sid, 'T': T, '分P': text[T]['分P'], '时间': text[T]['时间'], 'batch': B, 'valid': not errs, 'errors': errs,
                              'parsed_conditions': parsed, 'parsed_extra': parsed_extra, '来源类别': kind,
                              **{k: s.get(k) for k in ('类型', '宫', '适用', '条件', '前提', '附加条件', '结论', '连接', '原话摘录', '命例特指', '可操作', '说明', '来源', '改动')}})
                if errs: problems.append({'step_id': sid, 'problem': errs})
                if warns: warnings.append({'step_id': sid, 'warning': warns})
        bad = sorted(x for x in used if x not in valid_ids)
        twice = sorted(x for x, n in used.items() if n > 1 and x in valid_ids)
        missing = sorted(valid_ids - set(used))
        if bad or twice or missing:
            problems.append({'batch': B, 'problem': '编号着落不对', '不在材料里': bad, '出现不止一次': twice, '没有着落': missing})
    c = collections.Counter((s['类型'], s['valid']) for s in steps)
    res = {'schema': 'chain-adjudicated-v1', 'inputs_sha256': inputs,
           'counts': {'定稿步': len(steps), '合格': sum(s['valid'] for s in steps), '定性步': c[('定性步', True)] + c[('定性步', False)],
                      '推理步': c[('推理步', True)] + c[('推理步', False)], '有步的条目': len({s['T'] for s in steps}),
                      '有推理步的条目': len({s['T'] for s in steps if s['类型'] == '推理步'}), '方法': len(methods),
                      'problems': len(problems), 'warnings': len(warnings)},
           '一致程度': {'按条': dict(agree), '按步·定稿来源': dict(src), '按步·甲乙各自': {f'{k[0]}·{k[1]}': v for k, v in sorted(per_role.items())}},
           'steps': steps, 'methods': methods, 'problems': problems, 'warnings': warnings}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'counts': res['counts'], '一致程度': res['一致程度']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
