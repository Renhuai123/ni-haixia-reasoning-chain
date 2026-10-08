"""第二次认本人检验（M4f）两组对照所借的人，与本人在性别、五行局、候选结构上是否一致（设计描述，事后补算；回应第十四稿内审 R4 第 3 条）。
只读 key_m4f_v1.json，不读任何审者结果。
- 换陈述组：陈述借自 π(i)；换论断组：焦点论断借自 π′(i) 的真盘（陪衬三份与正题相同）。
- 性别：本人性别定得下时取 gender；定不下（候选盘男女都有）记「不定」。方案的约束是「两人性别都确定时须同性别」。
- 候选结构：structure（各候选与第一张的农历日差及性别）是否完全相同；候选张数是否相同。
用法：python3 m4f_pi_match_v1.py --key m4f_v1/key_m4f_v1.json --out chain_results_v1/m4f_pi_match_v1.json"""
import argparse, json, os


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--key', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    k = json.load(open(a.key, encoding='utf-8'))
    items = k['items']
    by_person = {v['person']: v for v in items.values()}
    out = {'schema': 'm4f-pi-match-v1', '说明': __doc__.split('\n')[0], '组': {}}
    for arm, fld in (('换陈述', '换陈述_person'), ('换论断', '换论断_person')):
        rows = {}
        for i, v in sorted(items.items()):
            o = by_person[v[fld]]
            g1, g2 = v['gender'], o['gender']
            rows[i] = {'借自': v[fld], '本人性别': g1 or '不定', '对方性别': g2 or '不定',
                       '性别': '同' if g1 and g2 and g1 == g2 else ('异' if g1 and g2 else '有一方不定'),
                       '五行局同': v['ju'] == o['ju'], '候选张数同': len(v['structure']) == len(o['structure']), '候选结构全同': v['structure'] == o['structure']}
        out['组'][arm] = {'题数': len(rows),
                          '性别相同': sum(r['性别'] == '同' for r in rows.values()), '性别不同': sum(r['性别'] == '异' for r in rows.values()),
                          '有一方性别不定': sum(r['性别'] == '有一方不定' for r in rows.values()),
                          '五行局相同': sum(r['五行局同'] for r in rows.values()), '候选张数相同': sum(r['候选张数同'] for r in rows.values()),
                          '候选结构全同': sum(r['候选结构全同'] for r in rows.values()), '逐题': rows}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({arm: {kk: vv for kk, vv in r.items() if kk != '逐题'} for arm, r in out['组'].items()}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
