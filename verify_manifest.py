"""核对本仓库：逐个重算 MANIFEST.tsv 里每个文件的 SHA-256，看与清单是否一致；
清单标「与登记一致」「与较早一次登记一致」的文件，再到登记表摘录（02_实验/preregistration_hashes.json）里核对：该路径确实登记过这个指纹。
只用 Python 标准库。用法：python3 verify_manifest.py"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


rows = [l.rstrip('\n').split('\t') for l in open(os.path.join(HERE, 'MANIFEST.tsv'), encoding='utf-8')][1:]
reg = json.load(open(os.path.join(HERE, '02_实验', 'preregistration_hashes.json'), encoding='utf-8'))
seen = {}
for f, h in reg.get('files', {}).items():
    seen.setdefault(f, set()).add(h)
for a in reg['amendments']:
    for f, h in a['files'].items():
        seen.setdefault(f, set()).add(h)
miss, bad, regbad = [], [], []
for path, size, h, st in rows:
    p = os.path.join(HERE, path)
    if not os.path.isfile(p):
        miss.append(path)
    elif os.path.getsize(p) != int(size) or sha(p) != h:
        bad.append(path)
    elif st in ('与登记一致', '与较早一次登记一致') and h not in seen.get(path, ()):
        regbad.append(path)
ok_reg = sum(1 for r in rows if r[3] in ('与登记一致', '与较早一次登记一致'))
print(f'清单里 {len(rows)} 个文件：缺 {len(miss)} 个，指纹或大小不符 {len(bad)} 个；'
      f'标为与登记一致的 {ok_reg} 个里，在登记表摘录里找不到的 {len(regbad)} 个。')
for x in (miss + bad + regbad)[:20]:
    print('  ', x)
sys.exit(1 if miss or bad or regbad else 0)
