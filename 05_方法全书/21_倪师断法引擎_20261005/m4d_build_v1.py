"""M4d 第三版配对复检：建题 v1（依据《21_第三版流年起法_方案_v1.md》三、3；只打印编号与计数，不打印陈述或论断内容）。
由 m4c_build_v1.py 改来，做法与 M4c 完全相同，只把论断换成第三版（ni_engine_v3：流年按倪海厦的起法）：
- 每题的规则集与 M4b、M4c 相同（剔除四位当事人全部讲述时段内的倪师层规则），逐题核对条数；
- 《取舍规则表》的对称留一同 M4c，逐题核对关掉的步骤与 M4c 的答案表完全相同；
- 两组出题包：全文组 judge_packets_full（第三版全文，不带出处）、综合论断组 judge_packets_syn（只给「综合论断」一节，不带出处）。
题目、陈述文件、干扰人选、A–D 次序、审者说明、输出模板从 M4（m4_v1）原样沿用：逐字节复制并核对 SHA-256。
另核对：每份论断引用的规则里，出处落在四位当事人讲述时段内的必须为 0。
另报（只作描述）：每组 112 份论断里，与 M4c 同一份论断文字不同的份数与题号。
写出 <out>/judge_packets_full/Mxx/、<out>/judge_packets_syn/Mxx/、<out>/key_m4d_v1.json、<out>/manifest.json；目录已存在就停。
用法：python3 m4d_build_v1.py --m4 <m4_v1> --m4b <m4b_v1> --m4c <m4c_v1> --kb <倪师层> --kb-qs <全书补层> --persons <m3_statements_merged_v1.json> --corpus <ni_corpus.txt> --out <新目录>"""
import argparse, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ni_engine_v1 as E
import ni_engine_v2 as V
import ni_engine_v3 as V3
from m4_build_v2 import run_charts, write, body_text, sha

TREF = re.compile(r'（(T\d+)')
GUARDED = {'A路9', 'B婚5', 'C祖5'}             # 装了开关的步骤（《16》第30条）
RULE_PREFIX = {('A', 'R1'): 'A路', ('A', 'R2'): 'A成', ('B', 'R1'): 'B婚', ('B', 'R2'): 'B子', ('C', 'R1'): 'C父', ('C', 'R2'): 'C兄', ('C', 'R3'): 'C祖'}


def table_steps():
    """《取舍规则表》各「次序」步骤所引的 T 编号：{代码里的步骤编号: [T...]}。"""
    out = {}
    for g in 'ABC':
        tab = json.loads(open(os.path.join(HERE, 'v2_principles_v1', 'returns', f'{g}_裁定.json'), encoding='utf-8').read())
        for r in tab['取舍规则']:
            for st in r['次序']:
                out[f"{RULE_PREFIX[(g, r['编号'])]}{st['步']}"] = list(st['依据'])
    return out


def in_segments(T, corpus, segs):
    if T not in corpus:
        return False
    p, tm = corpus[T]
    m = re.match(r'P(\d+)', p)
    return bool(m) and any(int(s['分P']) == int(m.group(1)) and s['start_s'] <= E.secs(tm) <= s['end_s'] for s in segs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('m4', 'm4b', 'm4c', 'kb', 'kb-qs', 'persons', 'corpus', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    rules = E.load_rules([a.kb, a.kb_qs])
    persons = {p['person_id']: p for p in json.load(open(a.persons, encoding='utf-8'))['persons']}
    key = json.load(open(os.path.join(a.m4, 'key_v1.json'), encoding='utf-8'))
    keyb = json.load(open(os.path.join(a.m4b, 'key_m4b_v1.json'), encoding='utf-8'))
    keyc = json.load(open(os.path.join(a.m4c, 'key_m4c_v1.json'), encoding='utf-8'))
    man = json.load(open(os.path.join(a.m4, 'manifest.json'), encoding='utf-8'))
    corpus = {}
    for ln in open(a.corpus, encoding='utf-8'):
        t = ln.rstrip('\n').split('｜')
        corpus[t[0]] = (t[1], t[2])
    steps = table_steps()
    allT = sorted({t for v in steps.values() for t in v})
    need = sorted({c for v in key['items'].values() for c in v['letters'].values()})
    rows = run_charts({f"{pid}#{i}": b['form'] for pid in need for i, b in enumerate(persons[pid]['candidates'])})
    cand_rows = {pid: [rows[f'{pid}#{i}'] for i in range(len(persons[pid]['candidates']))] for pid in need}
    for pid, rs in cand_rows.items():
        assert all('error' not in r for r in rs), pid
    os.makedirs(a.out)
    newkey = {'seed': key['seed'], 'derived_from': ['m4_v1/key_v1.json', 'm4b_v1/key_m4b_v1.json', 'm4c_v1/key_m4c_v1.json'], 'engine': 'ni_engine_v3',
              'design': 'symmetric-leave-four-out+table-steps (same as M4c)', 'items': {}}
    newman = {'schema': 'm4d-packets-v1', 'arms': {'full': [], 'syn': []}}
    changed = {'full': [], 'syn': []}
    for pk in man['judge_packs']:
        (iid,) = pk['items']
        v = key['items'][iid]
        owners = [v['letters'][L] for L in 'ABCD']
        segs = [s for c in owners for s in persons[c]['segments']]
        rs, removed = E.leave_out(rules, segs)
        assert len(rs) == keyb['items'][iid]['rules_used'], (iid, '规则集与 M4b 不同')
        hitT = {t for t in allT if in_segments(t, corpus, segs)}
        disabled = sorted(sid for sid, ts in steps.items() if ts and all(t in hitT for t in ts))
        assert set(disabled) <= GUARDED, (iid, '要关的步骤没有开关', sorted(set(disabled) - GUARDED))
        assert disabled == keyc['items'][iid]['disabled_steps'], (iid, '关掉的步骤与 M4c 不同')
        assert len(rs) == keyc['items'][iid]['rules_used'], (iid, '规则集与 M4c 不同')
        partial = sorted(sid for sid, ts in steps.items() if any(t in hitT for t in ts) and sid not in disabled)
        by_t = {}
        for r in rs:
            by_t.setdefault(r['T'], []).append(r)
        src = os.path.join(a.m4, 'judge_packets', pk['pack'])
        dirs = {arm: os.path.join(a.out, f'judge_packets_{arm}', pk['pack']) for arm in ('full', 'syn')}
        for d in dirs.values():
            os.makedirs(d)
            for fn in ('instructions.txt', 'output_template.json', f'{iid}_陈述.txt'):
                shutil.copyfile(os.path.join(src, fn), os.path.join(d, fn))
                assert sha(os.path.join(d, fn)) == pk['files_sha256'][fn], (iid, fn)
        self_rules = 0
        for L, c in v['letters'].items():
            rd, by_id = V3.read_candidates(cand_rows[c], rs)
            charts = [E.Chart(row) for row in cand_rows[c]]
            syn = V3.synthesize(rd, by_id, charts, disabled)
            write(dirs['full'], f'{iid}_论断{L}.txt', body_text(V3.render_text_v3(rd, by_id, syn, cite=False)))
            write(dirs['syn'], f'{iid}_论断{L}.txt', body_text(V3.render_text_v3(rd, by_id, syn, cite=False, only_synthesis=True)))
            for arm in ('full', 'syn'):
                old = os.path.join(a.m4c, f'judge_packets_{arm}', pk['pack'], f'{iid}_论断{L}.txt')
                if open(old, encoding='utf-8').read() != open(os.path.join(dirs[arm], f'{iid}_论断{L}.txt'), encoding='utf-8').read():
                    changed[arm].append(f'{iid}{L}')
            for T in set(TREF.findall(V3.render_text_v3(rd, by_id, syn, cite=True))):
                for r in by_t.get(T, []):
                    m = re.match(r'P(\d+)', str(r.get('分P', '')))
                    if m and r.get('时间') and any(int(s['分P']) == int(m.group(1)) and s['start_s'] <= E.secs(r['时间']) <= s['end_s'] for s in segs):
                        self_rules += 1
        assert self_rules == 0, (iid, '论断里仍有当事人自己的命例规则')
        newkey['items'][iid] = dict(keyb['items'][iid], disabled_steps=disabled, table_T_in_segments=sorted(hitT), table_steps_partially_in_segments=len(partial))
        for arm, d in dirs.items():
            newman['arms'][arm].append({'pack': pk['pack'], 'items': [iid], 'files_sha256': {fn: sha(os.path.join(d, fn)) for fn in sorted(os.listdir(d))}})
    newkey['changed_vs_m4c'] = {arm: {'n': len(v), 'of': 4 * len(newkey['items']), 'which': v} for arm, v in changed.items()}
    write(a.out, 'key_m4d_v1.json', newkey)
    write(a.out, 'manifest.json', newman)
    dis = {i: x['disabled_steps'] for i, x in newkey['items'].items() if x['disabled_steps']}
    print(json.dumps({'items': len(newkey['items']), 'disabled_steps': dis, 'changed_vs_m4c': {arm: v['n'] for arm, v in newkey['changed_vs_m4c'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
