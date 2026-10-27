# carteles.py : carteles de temporada del mapa 2048 (CanvasLabel de NEWGUI/Definition.xml + piezas en canvasTexture).
# Los CanvasLabel se pintan opacos (transparente = blanco) y muestran una ventana desplazada respecto a (u,v):
# x en [0, w*KX+56], y en [40, h*KY+46] texels. Un cartel "año" = 6 piezas, casi todas compartidas entre temporadas
# (emblema + "A·G", "R·C", decenas, unidades, filas en blanco). Un cartel "dibujo" = 1 pieza propia del tamaño del dibujo.
import re, io, base64, statistics
import numpy as np
from PIL import Image, ImageDraw, ImageFont
KX, KY = 47.0, 81.85
WX0, WX1, WY0, WY1 = 0, 56, 40, 46
R0 = (661, 1306)                         # rectángulo del cartel 2050 original en la textura
FW, FH = 760, 340
DOWN, RIGHT = 39, 31

def tam_dibujo(w, h):                    # píxeles que ve el juego de un cartel w x h
    return round(w * KX) + WX1, round(h * KY) + WY1 - WY0

def dilate(m, n):
    o = m.copy()
    for _ in range(n):
        t = o.copy(); t[1:] |= o[:-1]; t[:-1] |= o[1:]; t[:, 1:] |= o[:, :-1]; t[:, :-1] |= o[:, 1:]; o = t
    return o

def construir(A, defxml, temporadas, color, fuente, margen=12, zona_extra=True):
    """A: textura original (PIL RGBA). temporadas: [{'anio','x','y','evento','tipo':'anio'|'dibujo','w','h','png'}].
    Devuelve (textura nueva, xml de los CanvasLabel, lista de nombres para el ejecutable)."""
    A = A.convert('RGBA')
    F0 = A.crop((R0[0], R0[1], R0[0] + FW, R0[1] + FH)); px = F0.load()
    for y in range(FH):
        for x in range(FW):
            r, g, b, a = px[x, y]; ax, ay = R0[0] + x, R0[1] + y
            if ay < 1328 or ax < R0[0] + 60 or ax > 1335 or ay > 1590 or (a and r > 150 and g > 150 and b > 150):
                px[x, y] = (255, 255, 255, 0)
    cols = [A.getpixel((x, y))[:3] for x in range(1243, 1320, 3) for y in range(1470, 1548, 3) if A.getpixel((x, y))[3] > 250]
    BLUE = np.array([statistics.median(c[i] for c in cols) for i in range(3)], float)
    COL = np.array([int(color[i:i + 2], 16) for i in (1, 3, 5)], float) if color else BLUE
    F = ImageFont.truetype(fuente, 200)
    def glyph_alpha(ch, w=78, h=80):
        im = Image.new('L', (400, 300), 0); ImageDraw.Draw(im).text((50, 20), ch, font=F, fill=255)
        return np.array(im.crop(im.getbbox()).resize((w, h), Image.LANCZOS), float) / 255
    def put(img, ch, x, y):
        a = np.array(img, float); g = glyph_alpha(ch); h, w = g.shape
        sub = a[y:y + h, x:x + w]; ga = g[..., None]
        sub[..., :3] = sub[..., :3] * (1 - ga) + BLUE * ga
        sub[..., 3] = np.maximum(sub[..., 3], g * 255)
        return Image.fromarray(a.clip(0, 255).astype('uint8'), 'RGBA')
    def clear(img, x0, x1, y0, y1): ImageDraw.Draw(img).rectangle((x0, y0, x1, y1), fill=(255, 255, 255, 0))
    DY0 = 1466 - R0[1]
    def full(year):
        t, u = str(year)[2], str(year)[3]
        im = F0.copy(); clear(im, 1240 - R0[0], 1328 - R0[0], DY0, DY0 + 88)
        if t != '5':
            clear(im, 1158 - R0[0], 1240 - R0[0], DY0, DY0 + 88); im = put(im, t, 1161 - R0[0], 1469 - R0[1])
        return put(im, u, 1243 - R0[0], 1469 - R0[1])
    def shifted(img):
        c = Image.new('RGBA', (img.width, img.height + 2 * DOWN), (255, 255, 255, 0)); c.paste(img, (0, DOWN)); return c
    def piece(img, col, row, w, h):
        x0 = round(col * KX) + WX0; y0 = round(row * KY) + WY0
        return img.crop((x0, y0, x0 + round(w * KX) + WX1, y0 + round(h * KY) + WY1 - WY0))
    def art(year):
        im = shifted(full(year)); c = Image.new('RGBA', (im.width + RIGHT + 100, im.height), (255, 255, 255, 0)); c.paste(im, (RIGHT, 0)); return c
    def tint(img):                        # cambia el azul del cartel por el color elegido
        if color is None or color == '': return img
        a = np.array(img, float); lum = a[..., :3].mean(-1); lb = BLUE.mean()
        k = ((255 - lum) / max(1, 255 - lb)).clip(0, 1)[..., None]
        a[..., :3] = 255 * (1 - k) + COL * k
        return Image.fromarray(a.clip(0, 255).astype('uint8'), 'RGBA')
    # zonas ocupadas de la textura
    used = np.array(A)[..., 3] > 4
    for nm, v in re.findall(r'<CanvasLabel name="([^"]*)">\s*<Values ([^>]*)>', defxml):
        if nm.endswith('Label') or nm.endswith('CampaignTitle'): continue
        a = dict(re.findall(r'(\w+)="([^"]*)"', v))
        try: u, vv, w, h = float(a['u']), float(a['v']), float(a['width']), float(a['height'])
        except (KeyError, ValueError): continue
        x0, y0 = int(u * 2048) - 4, int(vv * 2048) - 4
        used[max(0, y0):y0 + int(h * KY) + 60, max(0, x0):x0 + int(w * KX) + 75] = True
    used = dilate(used, margen)
    libre_arriba = used[300:1000, 1620:].copy()       # hueco vacío a la derecha del hexágono X (probado en el juego)
    used[:1000] = True; used[:, :1100] = True          # iconos de eventos y de pistas
    if zona_extra: used[300:1000, 1620:] = libre_arriba
    _a = np.array(A); HIDDEN = (_a[..., 3] == 0) & (_a[..., :3] < 250).any(-1)   # rayados de los hexágonos (alfa 0)
    used |= dilate(HIDDEN, 8)
    used[1620:1960, 1500:1830] = True                  # zona que leen las caras de flechas/triángulos
    MOD = np.zeros((2048, 2048), bool)
    def place(w, h):
        ii = np.pad(np.cumsum(np.cumsum(used, 0), 1), ((1, 0), (1, 0)))
        for y in range(0, 2048 - h, 4):
            for x in range(0, 2048 - w, 4):
                if ii[y + h, x + w] - ii[y, x + w] - ii[y + h, x] + ii[y, x] == 0:
                    used[max(0, y - 2):y + h + 2, max(0, x - 2):x + w + 2] = True
                    MOD[y:y + h, x:x + w] = True
                    return x, y
        raise SystemExit('No cabe en la textura un cartel de %dx%d píxeles: usa menos carteles dibujados o más pequeños' % (w, h))
    out = A.copy()
    anios = [t for t in temporadas if t.get('tipo', 'anio') == 'anio']
    piezas = {}                                         # se colocan de mayor a menor para aprovechar los huecos
    if anios:
        base = art(2051)
        piezas['p1'], piezas['p2'], PB = tint(piece(base, 0, 0, 9, 4)), tint(piece(base, 9, 1, 6, 1)), piece(base, 9, 0, 6, 1)
        for d in sorted({str(t['anio'])[2] for t in anios}): piezas['t' + d] = tint(piece(art(2000 + 10 * int(d) + 1), 9, 2, 4, 1))
        for u in sorted({int(str(t['anio'])[3]) for t in anios}): piezas['u%d' % u] = tint(piece(art(2050 + u if u else 2060), 13, 2, 2, 1))
    for t in temporadas:
        if t.get('tipo') != 'dibujo': continue
        if not t.get('png'): raise SystemExit('La temporada %d tiene cartel de dibujo pero está sin dibujar' % t['anio'])
        im = Image.open(io.BytesIO(base64.b64decode(t['png'].split(',', 1)[1]))).convert('RGBA')
        piezas['d%d' % t['anio']] = im.resize(tam_dibujo(t['w'], t['h']), Image.LANCZOS)
    pos = {}
    for k, im in sorted(piezas.items(), key=lambda kv: -kv[1].width * kv[1].height):
        pos[k] = place(*im.size); out.paste(im, pos[k])
    dib = {int(k[1:]): v for k, v in pos.items() if k[0] == 'd'}
    o = np.array(out)
    pb = None
    if anios:
        blank = dilate(o[..., 3] > 0, 4) | dilate(HIDDEN, 4)
        ii = np.pad(np.cumsum(np.cumsum(blank, 0), 1), ((1, 0), (1, 0))); w4, h4 = PB.size
        for y in range(1100, 2048 - h4, 4):
            for x in range(1360, 2048 - w4, 4):
                if ii[y + h4, x + w4] - ii[y, x + w4] - ii[y + h4, x] + ii[y, x] == 0: pb = (x, y); break
            if pb: break
    o[(o[..., 3] == 0) & MOD, :3] = 255
    def uv(p): return (p[0] - WX0) / 2048, (p[1] - WY0) / 2048
    def lab(name, x, y, p, w, h, ev):
        u, v = uv(p)
        return ('<CanvasLabel name="%s">\r\n\t\t\t\t\t<Values x="%d" y="%d" u="%r" v="%r" width="%d" height="%d" linkedevent="%s"></Values>'
                '\r\n\t\t\t\t</CanvasLabel>\r\n\t\t\t\t') % (name, x, y, u, v, w, h, ev)
    xml, nombres = [], []
    for t in temporadas:
        y_, ev, n = t['anio'], t['evento'], 'A%02d' % (t['anio'] % 100)
        bx, by = t['x'], t['y']
        if t.get('tipo') == 'dibujo':
            xml.append(lab(n + 'a', bx, by, dib[y_], t['w'], t['h'], ev)); nombres.append(n + 'a'); continue
        d, u = str(y_)[2], int(str(y_)[3])
        xml += [lab(n + 'a', bx, by, pos['p1'], 9, 4, ev), lab(n + 'b', bx + 9, by, pb, 6, 1, ev),
                lab(n + 'c', bx + 9, by + 1, pos['p2'], 6, 1, ev), lab(n + 'd', bx + 9, by + 2, pos['t' + d], 4, 1, ev),
                lab(n + 'e', bx + 13, by + 2, pos['u%d' % u], 2, 1, ev), lab(n + 'f', bx + 9, by + 3, pb, 6, 1, ev)]
        nombres += [n + c for c in 'abcdef']
    libre = int((~used).sum())
    return Image.fromarray(o, 'RGBA'), ''.join(xml), nombres, libre
