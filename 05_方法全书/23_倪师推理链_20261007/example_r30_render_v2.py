"""示例盘 r30 的推理链成稿按 ni_chain_render_v2 重出（依据《00f_内审后更正与事后补充分析_v1.md》一、3；只做呈现）。
推理结果与 example_r30_v1 完全相同（同一知识库、同一引擎），只换成稿排版：身宫与财帛同宫时只写一遍，序号连续。
写出 <out>；文件已存在就停。用法：python3 example_r30_render_v2.py --out <新文件.txt>"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE); sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E
from ni_chain_render_v2 import render_chain


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    row = next(r for r in json.load(open(os.path.join(E_DIR, 'freeze_check_v1', 'rand_charts.json'), encoding='utf-8'))['rows'] if r['id'] == 'r30')
    ch = E.Chart(row)
    nodes, steps = C.load_kb(os.path.join(HERE, 'chain_kb_v1.json'))
    by = {s['step_id']: s for s in steps}
    der = C.infer(ch, nodes, steps)
    t2 = render_chain(der, nodes, by, ch)
    t1 = C.render_chain(der, nodes, by, ch)
    lines1 = {l for l in t1.split('\n') if l.startswith('  ')}
    lines2 = {l for l in t2.split('\n') if l.startswith('  ')}
    assert lines1 == lines2, '判断行与 v1 不同'
    open(a.out, 'x', encoding='utf-8').write(t2 + '\n')
    print({'v1行数': len(t1.split('\n')), 'v2行数': len(t2.split('\n')), '宫标题': [l for l in t2.split('\n') if l[:1].isdigit()]})


if __name__ == '__main__':
    main()
