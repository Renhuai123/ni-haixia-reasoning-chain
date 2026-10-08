"""M4f 功效模拟 v1（依据《00l_三项深化方案》v2 戊「功效」；回应独立审稿必2）。只模拟，不读任何数据。
模型（每题、每组）：
  S_i ~ 伯努利(s)：本人论断在这一题「整体上更吸引审者」（真人盘相对随机盘的整体差异），正题与换陈述组共用（两组四份论断相同）；
  M_i ~ 伯努利(δ)：本人论断「贴近本人」，只在正题起作用；
  S'_i ~ 伯努利(s)：换论断组里那份「他人真论断」的整体吸引，与 S_i 独立；
  正题：S_i 或 M_i 为真时这一题偏好本人，否则偏好四份里随意一份；换陈述组：S_i 为真时偏好本人，否则随意（另抽）；
  换论断组：S'_i 为真时偏好他人真论断，否则随意；
  每名审者以 c = 0.7 的概率选这一题偏好的那份，否则四份里随意选；每组每题 k 名审者。
检验同 m4f_analyze_v1：主检验为条件精确检验（单尾 0.05）；正负对比为每题票数差的符号翻转精确检验（单尾 0.05）。
种子：「METIS-M4f-功效模拟-20261008」，每格模拟 N 次。
用法：python3 m4f_power_sim_v1.py --n 1000"""
import argparse, hashlib, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m4f_analyze_v1 as A

OWN = A.OWN


def rng(seed):
    return random.Random(int(hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16], 16))


def votes(r, pref, k, c=0.7):
    n = {o: 0 for o in OWN}
    rk = {o: 0.0 for o in OWN}
    for _ in range(k):
        ch = pref if r.random() < c else r.choice(OWN)
        n[ch] += 1
        rest = [o for o in OWN if o != ch]
        r.shuffle(rest)
        for j, o in enumerate([ch] + rest, 1):
            rk[o] += j
    return n, rk


def one(r, s, d, k, items=28):
    pos, nega, negb = {}, {}, {}
    for i in range(items):
        S, M, S2 = r.random() < s, r.random() < d, r.random() < s
        pp = '焦点' if (S or M) else r.choice(OWN)
        pa = '焦点' if S else r.choice(OWN)
        pb = '焦点' if S2 else r.choice(OWN)   # 换论断组：焦点是他人真论断
        for D, p in ((pos, pp), (nega, pa), (negb, pb)):
            n, rk = votes(r, p, k)
            D[i] = {'n': n, 'rank': rk, 'valid': k, 'k': k}
    its = list(range(items))
    main = A.arm_stats(its, pos)['P(X≥实测)'] < 0.05
    out = {'主检验': main}
    for nm, neg in (('对比换陈述', nega), ('对比换论断', negb)):
        dd = [pos[i]['n']['焦点'] - neg[i]['n']['焦点'] for i in its]
        dist = A.conv([{x: 0.5, -x: 0.5} if x else {0: 1.0} for x in dd])
        out[nm] = A.tail_ge(dist, sum(dd)) < 0.05
    out['负对照偏高'] = A.arm_stats(its, nega)['P(X≥实测)'] < 0.05
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--n', type=int, default=1000)
    ap.add_argument('--calib', action='store_true', help='零假设校准：s = δ = 0，每组每题 2、3、5 名审者，各模拟 n 次（种子「METIS-M4f-零假设校准-20261008|k」）')
    a = ap.parse_args()
    if a.calib:
        for k in (2, 3, 5):
            r = rng(f'METIS-M4f-零假设校准-20261008|{k}')
            runs = [one(r, 0.0, 0.0, k) for _ in range(a.n)]
            print(k, {key: round(sum(x[key] for x in runs) / a.n, 4) for key in runs[0]}, flush=True)
        return
    res = {}
    for k in (2, 3, 5):
        for s in (0.0, 0.1, 0.2):
            for d in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
                r = rng(f'METIS-M4f-功效模拟-20261008|{k}|{s}|{d}')
                runs = [one(r, s, d, k) for _ in range(a.n)]
                res[f'k={k} s={s} δ={d}'] = {key: round(sum(x[key] for x in runs) / a.n, 3) for key in runs[0]}
                print(f'k={k} s={s} δ={d}', res[f'k={k} s={s} δ={d}'], flush=True)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == '__main__':
    main()
