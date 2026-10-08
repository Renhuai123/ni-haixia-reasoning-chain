"""倪师推理链：建抽取材料包 v1（依据《00_推理链方案_v1.md》四）。
- batch.json、context.txt 从知识库的 35 批（21_倪师断法引擎_20261005/kb_packets_v2/Kxx）逐字节复制，复制后核对 SHA-256 与来源相同；
- instructions.txt 由说明模板生成：模板里的 {{CONDITIONS}} 换成知识库抽取说明（kb_packets_v2/K01/instructions.txt）里「条件」一项下面的原文，
  从「- 条件：」的下一行起、到「- 结论：」的上一行止，逐字照搬（含星类写法）；
- output_template.json：本批每条一项（T、步、方法），另附定性步、推理步各一个写法示例（示意星名「甲星」，不是原话）。
写出 <out>/Kxx/ 与 <out>/manifest.json；目录已存在就停。
用法：python3 build_chain_packets_v1.py --instructions <说明模板> --batches K06,K10 --out <新目录>（--batches all 为全部 35 批）"""
import argparse, hashlib, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005', 'kb_packets_v2')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

EX_Q = {'类型': '定性步', '宫': '命宫', '适用': '先天', '条件': ['本宫有:甲星'],
        '结论': {'层': '定性', '判断': '将星', '原话说法': '将星', '方向': '中', '强度': '倾向'},
        '原话摘录': '甲星坐命的人是将星', '命例特指': False, '可操作': True, '说明': '示意，不是原话'}
EX_R = {'类型': '推理步', '宫': '命宫', '适用': '先天', '前提': [{'层': '定性', '判断': '将星', '原话说法': '将星'}], '附加条件': [],
        '结论': {'层': '路线', '判断': '适合当武官', '原话说法': '适合当武官', '方向': '中', '强度': '倾向'}, '连接': '所以',
        '原话摘录': '甲星坐命的人是将星，所以这种人适合当武官', '命例特指': False, '可操作': True, '说明': '示意，不是原话'}


def conditions_block():
    lines = open(os.path.join(KB, 'K01', 'instructions.txt'), encoding='utf-8').read().split('\n')
    i = next(k for k, l in enumerate(lines) if l.startswith('- 条件：'))
    j = next(k for k, l in enumerate(lines) if l.startswith('- 结论：'))
    assert i < j and lines[i + 1].startswith('  - 本宫有:')
    return '\n'.join(lines[i + 1:j])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--instructions', required=True)
    ap.add_argument('--batches', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    kbman = json.load(open(os.path.join(KB, 'manifest.json'), encoding='utf-8'))
    allb = [b['batch'] for b in kbman['batches']]
    want = allb if a.batches == 'all' else a.batches.split(',')
    assert all(b in allb for b in want)
    tpl = open(a.instructions, encoding='utf-8').read()
    assert tpl.count('{{CONDITIONS}}') == 1
    ins = tpl.replace('{{CONDITIONS}}', conditions_block())
    os.makedirs(a.out)
    man = {'schema': 'chain-packets-v1', 'instructions_template': os.path.basename(a.instructions), 'instructions_template_sha256': sha(a.instructions),
           'kb_instructions_sha256': sha(os.path.join(KB, 'K01', 'instructions.txt')), 'batches': []}
    for b in want:
        d = os.path.join(a.out, b)
        os.makedirs(d)
        src = {}
        for fn in ('batch.json', 'context.txt'):
            shutil.copyfile(os.path.join(KB, b, fn), os.path.join(d, fn))
            src[fn] = sha(os.path.join(KB, b, fn))
            assert sha(os.path.join(d, fn)) == src[fn]
        open(os.path.join(d, 'instructions.txt'), 'x', encoding='utf-8').write(ins)
        items = [it['T'] for it in json.load(open(os.path.join(d, 'batch.json'), encoding='utf-8'))['倪师条目']]
        tmpl = {'batch': b, 'items': [{'T': t, '步': [], '方法': ''} for t in items], '定性步示例': EX_Q, '推理步示例': EX_R}
        open(os.path.join(d, 'output_template.json'), 'x', encoding='utf-8').write(json.dumps(tmpl, ensure_ascii=False, indent=1) + '\n')
        man['batches'].append({'batch': b, 'items': items, 'source_sha256': src,
                               'sha256': {fn: sha(os.path.join(d, fn)) for fn in ('batch.json', 'context.txt', 'instructions.txt', 'output_template.json')}})
    open(os.path.join(a.out, 'manifest.json'), 'x', encoding='utf-8').write(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'batches': len(man['batches']), 'items': sum(len(b['items']) for b in man['batches'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
