"""M4e：每题陈述的「源 T 表」（依据《00h_三项补充研究方案_v2.md》甲、二「剔除与泄露核对」）。建题之前先建、先登记。
陈述来自前作 M3 的整理：每条陈述记有命例编号（含分P）、字幕行号与原话。本程序对每题本人的每条陈述，找出同一分P里可能是它来源的倪师条目（T）：
(i) 时间：T 的时段（起点到起点后 WIN 秒）与这条陈述所引字幕行的起止时间有任何重叠；
(ii) 文字：T 的原话与陈述的原话（都去掉空白与标点）有 NGRAM 个字以上的连续相同片段。
两条有一条成立就记为源 T。另报：每题陈述带年龄与不带年龄的条数（只作描述）。
题目与陈述的次序同 m4_v1（陈述序号 = persons[本人]['statements'] 的次序，从 1 起）。
写出 <out>；文件已存在就停。只打印计数。
用法：python3 m4e_sources_v1.py --m4 <m4_v1> --persons <m3_statements_merged_v1.json> --cues <m3_statement_packets_v2> --corpus <ni_corpus.txt> --out <新文件.json>"""
import argparse, glob, hashlib, json, os, re

WIN = 60
NGRAM = 8
norm = lambda s: re.sub(r'[\s\W_]+', '', str(s))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def secs(x):
    return sum(int(a) * b for a, b in zip(x.split(':'), (3600, 60, 1)))


def grams(s, k=NGRAM):
    return {s[i:i + k] for i in range(len(s) - k + 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for k in ('m4', 'persons', 'cues', 'corpus', 'out'):
        ap.add_argument('--' + k, required=True)
    a = ap.parse_args()
    assert not os.path.exists(a.out)
    key = json.load(open(os.path.join(a.m4, 'key_v1.json'), encoding='utf-8'))
    persons = {p['person_id']: p for p in json.load(open(a.persons, encoding='utf-8'))['persons']}
    cues = {}
    for f in glob.glob(os.path.join(a.cues, 'S_p*', 'cues.txt')):
        p = int(re.search(r'S_p(\d+)', f).group(1))
        t = {}
        for ln in open(f, encoding='utf-8'):
            m = re.match(r'\[(\d+) (\d+:\d+:\d+)\]', ln)
            if m:
                t[int(m.group(1))] = secs(m.group(2))
        cues[p] = t
    corpus = []
    for ln in open(a.corpus, encoding='utf-8'):
        T, P, tm, _, txt = ln.rstrip('\n').split('｜', 4)
        corpus.append((T, int(re.match(r'P(\d+)', P).group(1)), secs(tm), norm(txt)))
    out = {'说明': __doc__.split('\n')[0], 'WIN': WIN, 'NGRAM': NGRAM, 'inputs_sha256': {'key_v1': sha(os.path.join(a.m4, 'key_v1.json')), 'persons': sha(a.persons), 'corpus': sha(a.corpus)},
           'items': {}}
    for iid, v in sorted(key['items'].items()):
        sts = persons[v['person']]['statements']
        assert len(sts) == v['n_statements'], iid
        rows, allT, n_age = [], set(), 0
        for k, s in enumerate(sts, 1):
            p = int(re.match(r'P(\d+)', s['命例编号']).group(1))
            ts = [cues[p][n] for n in s['行号'] if n in cues.get(p, {})]
            assert ts, (iid, k, '字幕行号对不上')
            lo, hi = min(ts), max(ts)
            g = grams(norm(s['原话']))
            by_time = sorted(T for T, pp, t, _ in corpus if pp == p and t <= hi and t + WIN >= lo)
            by_text = sorted(T for T, pp, t, txt in corpus if pp == p and g & grams(txt))
            src = sorted(set(by_time) | set(by_text), key=lambda x: int(x[1:]))
            allT |= set(src)
            n_age += bool(str(s.get('年龄') or '').strip())
            rows.append({'序号': k, '分P': p, '字幕起止秒': [lo, hi], '源T·时间': by_time, '源T·文字': by_text})
        out['items'][iid] = {'person': v['person'], '陈述条数': len(sts), '带年龄': n_age, '不带年龄': len(sts) - n_age,
                             '源T': sorted(allT, key=lambda x: int(x[1:])), '逐条': rows}
    open(a.out, 'x', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({iid: [x['陈述条数'], x['带年龄'], len(x['源T'])] for iid, x in out['items'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
