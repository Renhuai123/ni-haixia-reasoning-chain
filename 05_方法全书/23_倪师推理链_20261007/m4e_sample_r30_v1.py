"""M4e 样张：拿开发用随机盘 r30（freeze_check_v1/rand_charts.json，论文第 6 节的示例盘）把三组论断各出一份，随方案登记，
让读者看到审者实际读到的样子（依据《00h_三项补充研究方案_v2.md》甲、三）。r30 不是命例，不剔除任何步或规则；只做呈现。
写出 <out>；文件已存在就停。用法：python3 m4e_sample_r30_v1.py --kb <chain_kb_v1.json> --v3kb <倪师层> --v3kb-qs <全书补层> --out <新文件.txt>"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE); sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E
import ni_engine_v3 as V3
import m4e_render_v1 as RD


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('kb', 'v3kb', 'v3kb-qs', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    row = next(r for r in json.load(open(os.path.join(E_DIR, 'freeze_check_v1', 'rand_charts.json'), encoding='utf-8'))['rows'] if r['id'] == 'r30')
    ch = E.Chart(row)
    nodes, steps = C.load_kb(a.kb)
    by_id = {s['step_id']: s for s in steps}
    dead = set(RD.death_nodes(nodes))
    der = C.infer_candidates([row], nodes, steps)
    rules = E.load_rules([a.v3kb, a.v3kb_qs])
    rd, rby = V3.read_candidates([row], rules)
    syn = V3.synthesize(rd, rby, [ch], ())
    parts = [('链组', RD.render_chain_m4e(der, nodes, by_id, ch.shen, dead)), ('平铺组', RD.render_flat_m4e(der, nodes, ch.shen, dead)),
             ('第三版先天组', RD.v3_natal(V3.render_text_v3(rd, rby, syn, cite=False)))]
    txt = ''.join(f'===== {k}（开发用随机盘 r30，未剔除）=====\n{t}\n' for k, t in parts)
    open(a.out, 'x', encoding='utf-8').write(txt)
    print({k: (t.count('\n'), len(t)) for k, t in parts})


if __name__ == '__main__':
    main()
