"""论文示例盘 r30：第四版推理链与第三版成稿并排（依据论文提纲补记一；只做呈现，不做统计）。
r30 取自 21_倪师断法引擎_20261005/freeze_check_v1/rand_charts.json（第六稿的示例盘，开发用随机盘，不对应真人）。
第四版：ni_chain_engine_v1.infer + render_chain（推理链知识库 chain_kb_v1.json，全部引擎可用步）；
第三版：ni_engine_v3.read_candidates + synthesize + render_text_v3（倪师知识库 kb_final_v1/kb_merged_v2.json，不加《全书》补层，不关步骤）。
另报 r30 命宫在覆盖检验口径下的几项数（推理步走到的层、最长链步数、用上的推理步条数），供与 600 张留出盘的分布对照。
写出 <out>.json 与 <out>.txt；文件已存在就停。用法：python3 example_r30_v1.py --out <新文件名，不带扩展名>"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
E_DIR = os.path.join(os.path.dirname(HERE), '21_倪师断法引擎_20261005')
sys.path.insert(0, HERE)
sys.path.insert(0, E_DIR)
import ni_chain_engine_v1 as C
import ni_engine_v1 as E
import ni_engine_v3 as V3


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    for ext in ('.json', '.txt'):
        assert not os.path.exists(a.out + ext)
    row = next(r for r in json.load(open(os.path.join(E_DIR, 'freeze_check_v1', 'rand_charts.json'), encoding='utf-8'))['rows'] if r['id'] == 'r30')
    ch = E.Chart(row)
    nodes, steps = C.load_kb(os.path.join(HERE, 'chain_kb_v1.json'))
    by = {s['step_id']: s for s in steps}
    der = C.infer(ch, nodes, steps)
    text4 = C.render_chain(der, nodes, by, ch)
    dp = der['命宫']
    r_layers = sorted({nodes[n]['层'] for n, xs in dp.items() if any(x['premises'] for x in xs)}, key=C.LAYER_ORDER.index)
    cov = {'推理步走到的层': r_layers, '最长链步数': max((xs[0]['depth'] for xs in dp.values()), default=0),
           '用上的推理步条数': len({x['step'] for xs in dp.values() for x in xs if x['premises']}),
           '命宫结点': len(dp), '最短推法也要经过推理步的结点': sum(1 for xs in dp.values() if xs[0]['premises']),
           '两说处数': len(C.two_sayings(dp, nodes))}
    ming = {n: {'层': nodes[n]['层'], '名': nodes[n]['名'],
                '推法': [{'step': x['step'], 'T': by[x['step']]['T'], '类型': by[x['step']]['类型'], 'premises': x['premises'], 'depth': x['depth'],
                          'via': x['via'], '方向': x['方向'], '强度': x['强度'], 'notes': x['notes'], '条件': by[x['step']].get('条件'),
                          '附加条件': by[x['step']].get('附加条件'), '原话摘录': by[x['step']]['原话摘录']} for x in xs]}
            for n, xs in dp.items()}
    rules = E.load_rules([os.path.join(E_DIR, 'kb_final_v1', 'kb_merged_v2.json')])
    rd, by_id = V3.read_candidates([row], rules)
    syn = V3.synthesize(rd, by_id, [ch])
    text3 = V3.render_text_v3(rd, by_id, syn, cite=True)
    res = {'schema': 'example-r30-v1', 'chart_id': 'r30', 'shen': ch.shen, '第四版·命宫覆盖口径': cov,
           '第四版·命宫主线': C.main_chains(dp, nodes, by, k=8), '第四版·命宫结点': ming,
           '第四版·各宫结点数': {p: len(der[p]) for p in C.PALACES}, '第四版成稿': text4, '第三版成稿': text3}
    open(a.out + '.json', 'x', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    open(a.out + '.txt', 'x', encoding='utf-8').write('【第四版：推理链】\n' + text4 + '\n\n【第三版成稿（对照）】\n' + text3 + '\n')
    print(json.dumps({'覆盖口径': cov, '主线': res['第四版·命宫主线']}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
