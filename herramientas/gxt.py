# gxt.py : texturas GXT de la Vita para canvasTexture.gxt
#   leer(ruta) -> PIL RGBA   (PVRTC-II 4bpp, el formato original del juego, o DXT5)
#   escribir(img, ruta)      -> DXT5 (UBC3) con mipmaps, como lo usa el mod (necesita ImageMagick)
import struct, subprocess, tempfile, os
import numpy as np
from PIL import Image

def _morton(n):                    # índice z de cada (y, x) de una rejilla n x n
    i = np.arange(n)
    def sp(v):
        r = np.zeros_like(v)
        for b in range(16): r |= ((v >> b) & 1) << (2 * b)
        return r
    return (sp(i)[:, None] << 1) | sp(i)[None, :]

def _exp(v, bits): return (v << (8 - bits)) | (v >> (2 * bits - 8)) if bits >= 4 else (v << 5) | (v << 2) | (v >> 1)

def _pvrtc2(body, w, h):
    bw, bh = w // 4, h // 4
    blk = np.frombuffer(body[:bw * bh * 8], '<u4').reshape(-1, 2)
    idx = _morton(bw).T.reshape(-1)
    mod = blk[idx, 0].reshape(bh, bw).astype(np.int64); col = blk[idx, 1].reshape(bh, bw).astype(np.int64)
    opaque = (col >> 31) & 1; hard = (col >> 15) & 1; mode = col & 1
    def colors(c, isB):
        sh = 16 if isB else 0; v = (c >> sh) & 0x7fff
        r5, g5, b5 = (v >> 10) & 31, (v >> 5) & 31, (v & 31) if isB else ((v >> 1) & 15) << 1 | ((v >> 4) & 1)
        o = np.stack([_exp(r5, 5), _exp(g5, 5), _exp(b5, 5), np.full_like(r5, 255)], -1)
        a3, r4, g4 = (v >> 12) & 7, (v >> 8) & 15, (v >> 4) & 15
        b4 = (v & 15) if isB else ((v >> 1) & 7) << 1 | ((v >> 3) & 1)
        t = np.stack([_exp(r4, 4), _exp(g4, 4), _exp(b4, 4), _exp(a3, 3)], -1)
        return np.where(opaque[..., None] == 1, o, t).astype(np.float64)
    A, B = colors(col, False), colors(col, True)
    # interpolación bilineal entre centros de bloque (bordes en bucle, como PVRTC)
    def up(C):
        ys = (np.arange(h) - 2) / 4.0; xs = (np.arange(w) - 2) / 4.0
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int); fy = (ys - y0)[:, None, None]; fx = (xs - x0)[None, :, None]
        y0m, y1m = y0 % bh, (y0 + 1) % bh; x0m, x1m = x0 % bw, (x0 + 1) % bw
        c00 = C[y0m][:, x0m]; c01 = C[y0m][:, x1m]; c10 = C[y1m][:, x0m]; c11 = C[y1m][:, x1m]
        return (c00 * (1 - fx) + c01 * fx) * (1 - fy) + (c10 * (1 - fx) + c11 * fx) * fy
    Ai, Bi = up(A), up(B)
    # bloques con transición brusca: colores propios del bloque, sin interpolar
    hp = np.repeat(np.repeat(hard, 4, 0), 4, 1)[..., None]
    Ai = np.where(hp, np.repeat(np.repeat(A, 4, 0), 4, 1), Ai); Bi = np.where(hp, np.repeat(np.repeat(B, 4, 0), 4, 1), Bi)
    m = np.zeros((h, w), np.int64)
    for py in range(4):
        for px in range(4):
            m[py::4, px::4] = (mod >> (2 * (py * 4 + px))) & 3
    mp = np.repeat(np.repeat(mode, 4, 0), 4, 1)
    wt = np.where(mp == 0, np.array([0, 3, 5, 8])[m], np.array([0, 4, 4, 8])[m]) / 8.0
    out = Ai * (1 - wt[..., None]) + Bi * wt[..., None]
    out[..., 3] = np.where((mp == 1) & (m == 2), 0, out[..., 3])      # punch-through
    return Image.fromarray(out.clip(0, 255).round().astype(np.uint8), 'RGBA')

def leer(ruta):
    d = open(ruta, 'rb').read()
    assert d[:4] == b'GXT\0', 'no es GXT'
    off, size = struct.unpack_from('<II', d, 0x20)
    fmt = struct.unpack_from('<I', d, 0x34)[0]; w, h = struct.unpack_from('<HH', d, 0x38)
    if fmt >> 24 == 0x83: return _pvrtc2(d[off:off + size], w, h)
    raise SystemExit('formato de textura no soportado: %08x' % fmt)

def escribir(img, ruta, nmip=10):
    tmp = tempfile.mkdtemp(); png = os.path.join(tmp, 'a.png'); dds = os.path.join(tmp, 'a.dds'); img.save(png)
    subprocess.run(['magick', png, '-define', 'dds:compression=dxt5', '-define', 'dds:mipmaps=%d' % (nmip - 1),
                    '-define', 'dds:cluster-fit=true', dds], check=True)
    d = open(dds, 'rb').read(); assert d[:4] == b'DDS ' and d[84:88] == b'DXT5'
    h, w = struct.unpack_from('<II', d, 12); pos = 128; body = b''
    for lvl in range(nmip):
        mw, mh = max(1, w >> lvl), max(1, h >> lvl); bx, by = (mw + 3) // 4, (mh + 3) // 4; n = bx * by * 16
        lin = np.frombuffer(d[pos:pos + n], np.uint8).reshape(by * bx, 16); pos += n
        m = min(bx, by); k = m.bit_length() - 1
        yy, xx = np.mgrid[0:by, 0:bx]
        z = _morton(m)[xx & (m - 1), yy & (m - 1)] | (((xx >> k) if bx >= by else (yy >> k)) << (2 * k))
        sw = np.zeros_like(lin); sw[z.reshape(-1)] = lin; body += sw.tobytes()
    hdr = b'GXT\0' + struct.pack('<IIIIIII', 0x10000003, 1, 0x40, len(body), 0, 0, 0)
    tex = struct.pack('<IIiIIIHHBBH', 0x40, len(body), -1, 0, 0, 0x87000000, w, h, nmip, 0, 0)
    open(ruta, 'wb').write(hdr + tex + body)
