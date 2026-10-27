# Patch a PSARC preserving original compressed blocks of untouched entries byte-for-byte.
# parchear(base, out, archivos) con archivos = {'data/xml/SP.xml': bytes, ...}
import struct, zlib, os, hashlib
def parchear(base, out, archivos):
    f = open(base, 'rb'); hdr = f.read(32)
    magic, ver, comp, toclen, tes, ne, bs, flags = struct.unpack('>4sI4sIIIII', hdr)
    toc = f.read(toclen - 32)
    zb = {65536: 2, 16777216: 3}.get(bs, 4)
    ents = [toc[i*tes:(i+1)*tes] for i in range(ne)]
    bl = toc[ne*tes:]; bsz = [int.from_bytes(bl[i*zb:(i+1)*zb], 'big') for i in range(len(bl)//zb)]
    def info(e): return struct.unpack('>I', e[16:20])[0], int.from_bytes(e[20:25], 'big'), int.from_bytes(e[25:30], 'big')
    def raw_blocks(e):
        bi, us, off = info(e); n = max(1, -(-us // bs)) if us else 0
        f.seek(off); return [f.read(bsz[bi+k] or bs) for k in range(n)], [bsz[bi+k] for k in range(n)]
    def decomp(e):
        bi, us, off = info(e); blocks, sizes = raw_blocks(e); data = b''
        for b, s in zip(blocks, sizes):
            rem = us - len(data)
            if (s or bs) == min(bs, rem):
                try: d = zlib.decompress(b)
                except Exception: d = b
            else: d = zlib.decompress(b)
            data += d
        return data[:us]
    names = decomp(ents[0]).decode().split('\n')
    lower = {n.lower(): i + 1 for i, n in enumerate(names)}
    repl = {}; adds = []
    for rel, data in archivos.items():
        idx = lower.get(rel.lower())
        if idx: repl[idx] = data
        else: adds.append((rel, data))
    def encode(data):
        blocks, sizes = [], []
        for i in range(0, len(data), bs):
            c = data[i:i+bs]; z = zlib.compress(c, 9)
            if len(z) < len(c): blocks.append(z); sizes.append(len(z))
            else: blocks.append(c); sizes.append(0 if len(c) == bs else len(c))
        return blocks, sizes
    if adds:
        names2 = names + [r for r, _ in adds]
        repl[0] = '\n'.join(names2).encode()
        for r, d in adds:
            ents.append(hashlib.md5(r.upper().encode()).digest() + b'\0' * 14)
            repl[len(ents) - 1] = d
        ne = len(ents)
    allb = []; newents = []
    for i, e in enumerate(ents):
        if i in repl: blocks, sizes = encode(repl[i]); us = len(repl[i])
        else: blocks, sizes = raw_blocks(e); us = info(e)[1]
        newents.append([e[:16], len(allb), us, blocks, sizes]); allb += list(zip(blocks, sizes))
    toclen2 = 32 + ne*tes + zb*len(allb)
    off = toclen2; tocb = b''; blb = b''
    for md5, bi, us, blocks, sizes in newents:
        tocb += md5 + struct.pack('>I', bi) + us.to_bytes(5, 'big') + off.to_bytes(5, 'big')
        off += sum(len(b) for b in blocks)
    for b, s in allb: blb += s.to_bytes(zb, 'big')
    with open(out, 'wb') as o:
        o.write(struct.pack('>4sI4sIIIII', magic, ver, comp, toclen2, tes, ne, bs, flags) + tocb + blb)
        for b, s in allb: o.write(b)
