# construir.py [campana.json] : genera el mod a partir de la campaña del editor.
# Salida en salida/: eboot.bin y data2.psarc listos para copiar, eboot.ips y (si hay xdelta3) data2.xdelta.
import os, sys, re, json, struct, shutil, subprocess, random, zlib, html
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(D, 'herramientas'))
import carteles, gxt, psarc_parche
from PIL import Image
J, T, S = os.path.join(D, 'juego'), os.path.join(D, 'trabajo'), os.path.join(D, 'salida')
CLASES = {'C': '1', 'B': '2', 'A': '3', 'A+': '4'}
MAX_TEMPORADAS, MAX_PROBADO = 24, 210
GRID = ['2075556815', '2075556815', '2075556815', '-1708507528', '-1708507528', '-1126722970', '-1126722970']

def set_opt(b, f, v):
    return re.sub(r'(<M_[A-Z0-9_]+ name="%s".*?<ARRAY value=")[^"]*(")' % f, lambda m: m.group(1) + v + m.group(2), b, count=1, flags=re.S)

def campo(b, f):
    m = re.search(r'<M_[A-Z0-9_]+ name="%s".*?</M_[A-Z0-9_]+>' % f, b, re.S)
    if not m: return None
    v = re.findall(r'<ARRAY value="([^"]*)"', m.group(0)); return v[0] if v else ''

textos = {}   # clave -> (español, inglés) de los textos propios de los eventos

def generar_sp(sp, C, P):
    bloques = {m.group(1): m.group(0) for m in re.finditer(r'<instance instanceid="([-0-9]+)".*?</instance>', sp, re.S)}
    por_nombre = {re.search(r' name="([^"]*)"', b).group(1): i for i, b in bloques.items()}
    pistas, objetivos = P['pistas'], P['objetivos']
    usados = set(bloques)
    evs = [(t, k, e) for t, temp in enumerate(C['temporadas']) for k, e in enumerate(temp['eventos'])]
    for _, _, e in evs:
        e['id'] = str(e.get('id') or '')
        while not e['id'] or e['id'] in usados or e['id'] in por_nombre: e['id'] = str(random.randint(-2**31, 2**31 - 1))
        usados.add(e['id'])
    ultimo = previo = por_nombre['2050 - Event 9']; nuevos = []; textos.clear()
    for i, (t, k, e) in enumerate(evs):
        src = por_nombre[e['plantilla']]; b = bloques[src]; nombre = '%d - Event %d' % (2051 + t, k + 1)
        b = b.replace('instanceid="%s"' % src, 'instanceid="%s"' % e['id'], 1)
        b = re.sub(r' name="[^"]*"', ' name="%s"' % nombre, b, count=1)
        sig = evs[i + 1][2]['id'] if i + 1 < len(evs) else ''
        cambios = [('m_pBranchEvent', ''), ('m_buttonShape', str(e.get('forma', '0'))), ('m_pEventRequired', previo if k == 0 else ''),
                   ('m_pNextEvent', sig), ('m_x', str(e['x'])), ('m_y', str(e['y'])),
                   ('m_canvasTweak_x', '0'), ('m_canvasTweak_y', '0')]          # las plantillas traen ajustes finos de posición: fuera
        tipo = e['tipo']
        if campo(b, 'm_speedClass') and e.get('clase'): cambios.append(('m_speedClass', CLASES[e['clase']]))
        if campo(b, 'm_skillScale') and e.get('ia'): cambios.append(('m_skillScale', str(e['ia'])))
        if tipo == 'carrera':
            if e.get('vueltas'): cambios.append(('m_numOfLaps', str(e['vueltas'])))
            if 'armas' in e: cambios.append(('m_bDisableWeapons', 'false' if e['armas'] else 'true'))
            if e.get('pase'): cambios.append(('m_PassObjective', objetivos[e['pase']]))
            if e.get('elite'): cambios.append(('m_EliteObjective', objetivos[e['elite']]))
        if e.get('pista') and tipo != 'zona' and campo(b, 'm_trackDef'):
            cambios.append(('m_trackDef', pistas[e['pista']]))
            if tipo == 'carrera': cambios.insert(0, ('m_description', 'MP_%s_RACE_FLASH' % e['pista'].upper()))
        # naves: 'clasesNave' = clases permitidas (velocidad/agilidad/combate/prototipo), 'nave' = nave obligatoria ('' = ninguna)
        if e.get('nave') and 'clasesNave' in e:           # la clase de la nave obligatoria siempre permitida
            cl = {'Speed': 'velocidad', 'Agility': 'agilidad', 'Combat': 'combate', 'Proto': 'prototipo'}[e['nave'].rsplit('_', 1)[1]]
            if cl not in e['clasesNave']: e['clasesNave'] = e['clasesNave'] + [cl]
        if 'clasesNave' in e:
            for cl, f in (('velocidad', 'm_bPreventSpeedShips'), ('agilidad', 'm_bPreventAgilityShips'), ('combate', 'm_bPreventCombatShips'), ('prototipo', 'm_bPreventProtoShips')):
                if campo(b, f) is not None: cambios.append((f, 'false' if cl in e['clasesNave'] else 'true'))
        if 'nave' in e and campo(b, 'm_pPlayerShipModelData') is not None: cambios.append(('m_pPlayerShipModelData', P['naves'][e['nave']] if e['nave'] else ''))
        # objetivos propios (contrarreloj: centésimas; zona: zona alcanzada; eliminator: puntos): copia del objetivo de la plantilla
        for k, f, suf in (('objPase', 'm_PassObjective', 'Pass'), ('objElite', 'm_EliteObjective', 'Elite')):
            if tipo != 'carrera' and e.get(k) is not None and campo(b, f):
                ob = bloques[campo(b, f)]; oid = str(zlib.crc32(('%s-%s' % (e['id'], suf)).encode()) - 2**31)
                ob = ob.replace('instanceid="%s"' % campo(b, f), 'instanceid="%s"' % oid, 1)
                ob = re.sub(r' name="[^"]*"', ' name="%s %s"' % (nombre, suf), ob, count=1)
                nuevos.append(set_opt(ob, 'm_ObjectiveTarget', str(int(e[k])))); cambios.append((f, oid))
        base_desc = next((v for f, v in cambios if f == 'm_description'), campo(b, 'm_description'))
        vueltas_txt = int(e['vueltas']) if tipo == 'carrera' and e.get('vueltas') and int(e['vueltas']) != 3 and str(base_desc).startswith('MP_') else None
        if e.get('texto') or e.get('textoEn') or vueltas_txt:                 # texto propio (o el de la pista con las vueltas reales)
            clave = 'CAMP_%s_TXT' % e['id'].replace('-', 'M'); textos[clave] = (e.get('texto'), e.get('textoEn'), base_desc, vueltas_txt)
            cambios.append(('m_description', clave))
        if C.get('desbloquearTodo'): cambios.append(('m_bForceAlwaysUnlocked', 'true'))      # solo para pruebas
        for f, v in cambios: b = set_opt(b, f, v)
        rivales = [P['naves'][n] for n in e['rivales']] if e.get('rivales') else (GRID if tipo == 'carrera' and e['plantilla'] == '2050 - Event 9' else None)
        gm = re.search(r'<M_PGRIDSHIPMODELDATA.*?</M_PGRIDSHIPMODELDATA>', b, re.S)
        if rivales and gm and len(re.findall(r'<ARRAY value="[^"]*"', gm.group(0))) == len(rivales):   # naves de los 7 rivales
            ng = gm.group(0)
            for a, g in zip(re.findall(r'<ARRAY value="[^"]*"', gm.group(0)), rivales): ng = ng.replace(a, '<ARRAY value="%s"' % g, 1)
            b = b.replace(gm.group(0), ng)
        nuevos.append(b)
        if k == len(C['temporadas'][t]['eventos']) - 1: previo = e['id']
    if evs:
        t9 = bloques[ultimo]; sp = sp.replace(t9, set_opt(t9, 'm_pNextEvent', evs[0][2]['id']))
    sp = sp.replace('</mjolnir>', ''.join(nuevos) + '</mjolnir>')
    if C.get('iaOriginales'):
        def rep(m):
            b = m.group(0)
            if not re.search(r' name="20(4[89]|50) - Event [0-9-]+"', b[:300]): return b
            return re.sub(r'(name="m_skillScale".*?<ARRAY value=")[^"]*(")', r'\g<1>%s\2' % C['iaOriginales'], b, count=1, flags=re.S)
        sp = re.sub(r'<instance instanceid=.*?</instance>', rep, sp, flags=re.S)
    return sp, len(evs)

def parchear_eboot(d, nombres):
    def off(va): return va - 0x81000000 + 0x2000 if va < 0x81519000 else va - 0x81519000 + 0x51b000
    for va, old, new in [(0x812d9510, '5ff42041', '5ff48021'), (0x812da05e, '37d1', '00bf'), (0x812b3fec, '5ddc', '00bf')]:
        o = off(va); assert d[o:o + len(old) // 2].hex() == old; d[o:o + len(new) // 2] = bytes.fromhex(new)
    o = off(0x8151c134); assert struct.unpack_from('<I', d, o)[0] == 0x78000; struct.pack_into('<I', d, o, 0x200000)
    # pila del hilo principal 256 KB -> 1 MB (SceProcessParam: puntero al tamaño, apunta a una constante 0x100000 del código);
    # al cargar la campaña el juego recorre la cadena de eventos recursivamente y en una Vita real desborda la pila
    o = off(0x8152ae08); assert struct.unpack_from('<I', d, o)[0] == 0 and struct.unpack_from('<I', d, off(0x813f4bf4))[0] == 0x100000
    struct.pack_into('<I', d, o, 0x813f4bf4)
    T0 = 0x814adc20; viejos = [struct.unpack_from('<I', d, off(0x8151e9b8 + 4 * i))[0] for i in range(48)]
    cad = T0 + 4 * (48 + len(nombres)); ptrs = []; blob = b''
    for n in nombres: ptrs.append(cad + len(blob)); blob += n.encode() + b'\0'
    fin = cad + len(blob)
    if fin >= 0x814ae2a4: raise SystemExit('Demasiados carteles (%d piezas): quita temporadas o usa carteles dibujados' % len(nombres))
    d[off(T0):off(fin)] = struct.pack('<%dI' % (48 + len(nombres)), *(viejos + ptrs)) + blob
    def movwt(va, imm16, top):
        o = off(va); h1, h2 = struct.unpack_from('<HH', d, o)
        assert (h1 & 0xfbf0) == (0xf2c0 if top else 0xf240)
        h1 = (h1 & 0xfbf0) | ((imm16 >> 12) & 0xf) | (((imm16 >> 11) & 1) << 10)
        h2 = (h2 & 0x8f00) | (((imm16 >> 8) & 7) << 12) | (imm16 & 0xff)
        struct.pack_into('<HH', d, o, h1, h2)
    for lo, hi in [(0x810eefe6, 0x810eefec), (0x810f0002, 0x810f0014), (0x810f100c, 0x810f1014)]:
        movwt(lo, T0 & 0xffff, False); movwt(hi, T0 >> 16, True)
    for va in (0x810ef0a8, 0x810f00d4, 0x810f10cc):
        o = off(va); assert d[o] == 0x30; d[o] = 48 + len(nombres)
    # Las finales nuevas (forma 9/10/11) no deben enseñar la copa de 2048-2050: en la página de premios (0x81053532),
    # en vez de leer la forma directamente se llama a este trozo, que la pone a 0 si el nombre es "2051".."2079 - ...".
    CUEVA = 0x814ae2a4                     # final de la zona de cadenas de depuración sin uso (después de la tabla de carteles)
    assert fin <= CUEVA, 'la tabla de carteles invade el código de las finales'
    ldr = bytes(d[off(0x81053532):off(0x81053532) + 4]); assert ldr.hex() == 'd4f89c41'
    cueva = ldr + bytes.fromhex('2878 3228 0ad1 6878 3028 07d1 a878 3528 04d3 02d8 e878 3028 00d0 0024 7047'.replace(' ', ''))
    d[off(CUEVA):off(CUEVA) + len(cueva)] = cueva
    def bl(desde, hasta):                  # BL Thumb-2 (T1)
        imm = (hasta - (desde + 4)) >> 1; S = (imm >> 23) & 1; i1 = (imm >> 22) & 1; i2 = (imm >> 21) & 1
        j1, j2 = (1 - i1) ^ S, (1 - i2) ^ S
        return struct.pack('<HH', 0xf000 | (S << 10) | ((imm >> 11) & 0x3ff), 0xd000 | (j1 << 13) | (j2 << 11) | (imm & 0x7ff))
    d[off(0x81053532):off(0x81053532) + 4] = bl(0x81053532, CUEVA)
    return d

def ips(a, b):
    out = bytearray(b'PATCH'); i = 0
    while i < len(b):
        if a[i] == b[i]: i += 1; continue
        j = i
        while j < len(b) and j - i < 0xffff and (a[j] != b[j] or (j + 1 < len(b) and a[j + 1] != b[j + 1])): j += 1
        if i == 0x454f46: i -= 1
        out += i.to_bytes(3, 'big') + (j - i).to_bytes(2, 'big') + b[i:j]; i = j
    return bytes(out + b'EOF')

def con_textos(t, idioma):
    """Devuelve entries.xml (texto) con los textos propios insertados en orden (el juego los busca por búsqueda binaria)."""
    nl = '\r\n' if '\r\n' in t else '\n'
    orig = dict(re.findall(r'<entry id="([^"]*)" string="([^"]*)"', t))       # textos del idioma (ya escapados)
    def texto(es, en, base, vueltas=None):   # español -> 'es'; inglés -> 'en'; si no se cambió, el original de ese idioma
        propio = es if idioma == 'spanish' else en
        if propio: return html.escape(propio, quote=True)
        t0 = orig.get(base, html.escape(es or en or '', quote=True))
        return re.sub(r'(?<!\d)3(?!\d)', str(vueltas), t0, count=1) if vueltas else t0   # "carrera de 3 vueltas" -> N
    sep = nl if nl in t else ''          # Firestar deja todo el archivo en una sola línea
    t = re.sub(r'<entry id="CAMP_[^"]*" string="[^"]*"></entry>(\r?\n)?', '', t)   # quitar textos propios de una construcción anterior
    for k, v in sorted(textos.items()):
        nueva = '<entry id="%s" string="%s"></entry>%s' % (k, texto(*v), sep)
        pos = next((m.start() for m in re.finditer(r'<entry id="([^"]*)"', t) if m.group(1).encode() > k.encode()), t.rindex('</StringTable>'))
        t = t[:pos] + nueva + t[pos:]
    return t.encode('utf8')

def xdelta3():
    for p in (os.path.join(D, 'herramientas', 'xdelta3'), os.path.join(D, 'herramientas', 'xdelta3.exe'), shutil.which('xdelta3')):
        if p and os.path.exists(p): return p

def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, 'campana.json')
    if not os.path.exists(os.path.join(T, 'plantillas.json')): sys.exit('Primero ejecuta preparar.py')
    C = json.load(open(ruta, encoding='utf8')); P = json.load(open(os.path.join(T, 'plantillas.json'), encoding='utf8'))
    temps = C['temporadas']
    if len(temps) > MAX_TEMPORADAS: sys.exit('Máximo %d temporadas' % MAX_TEMPORADAS)
    if any(not t['eventos'] for t in temps): sys.exit('Hay temporadas sin eventos')
    O = os.path.join(T, 'orig', 'data')
    sp, n = generar_sp(open(os.path.join(O, 'xml/SP.xml'), encoding='utf8', newline='').read(), C, P)
    print('Eventos nuevos: %d en %d temporadas%s' % (n, len(temps), ' (más de %d no está probado)' % MAX_PROBADO if n > MAX_PROBADO else ''))
    json.dump(C, open(ruta, 'w', encoding='utf8'), ensure_ascii=False, indent=1)          # guarda los id asignados
    defxml = open(os.path.join(O, 'plugins/frontend/NEWGUI/Definition.xml'), encoding='utf8', newline='').read()
    lista = [dict(anio=2051 + i, x=t['cartel']['x'], y=t['cartel']['y'], evento='%d - Event 1' % (2051 + i), **{k: v for k, v in t['cartel'].items() if k not in 'xy'})
             for i, t in enumerate(temps)]
    fuente = next((f for f in [C.get('fuente'), os.path.join(D, 'fuente', 'fuente.ttf'), '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
                               '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf'] if f and os.path.exists(f)), None)
    if not fuente: sys.exit('Pon una fuente .ttf en fuente/fuente.ttf (se usa para las cifras de los carteles)')
    atlas, labxml, nombres, libre = carteles.construir(Image.open(os.path.join(T, 'atlas_orig.png')), defxml, lista, C.get('colorCarteles') or None, fuente)
    print('Carteles: %d piezas; quedan ~%d píxeles libres en la textura' % (len(nombres), libre))
    if C.get('pruebaCarteles'): labxml = re.sub(r' linkedevent="[^"]*"', '', labxml)     # solo para pruebas: carteles siempre visibles
    i = defxml.index('<CanvasLabel name="Trophy-2048-2-3">'); defxml = defxml[:i] + labxml + defxml[i:]
    os.makedirs(S, exist_ok=True); tex = os.path.join(T, 'canvasTexture.gxt'); gxt.escribir(atlas, tex)
    archivos = {'data/xml/SP.xml': sp.encode('utf8'), 'data/plugins/frontend/NEWGUI/Definition.xml': defxml.encode('utf8'),
                'data/FE/NewImages/canvasTexture.gxt': open(tex, 'rb').read()}
    # textos propios: se añaden a los 15 idiomas (español en español, inglés en el resto)
    for idioma in sorted(os.listdir(os.path.join(O, 'plugins/languages'))) if textos else []:
        ruta = os.path.join(O, 'plugins/languages', idioma, 'entries.xml')
        archivos['data/plugins/languages/%s/entries.xml' % idioma] = con_textos(open(ruta, encoding='utf8', newline='').read(), idioma)
    if textos: print('Textos propios: %d (en 15 idiomas)' % len(textos))
    psarc_parche.parchear(os.path.join(J, 'data2.psarc'), os.path.join(S, 'data2.psarc'), archivos)
    # el DLC 2 trae su propia copia de los textos y se carga después de data2: si el jugador lo tiene, hay que parchearlo también
    dlc2 = os.path.join(J, 'dlc2.psarc')
    if os.path.exists(os.path.join(S, 'dlc2.psarc')): os.remove(os.path.join(S, 'dlc2.psarc'))
    if textos and os.path.exists(dlc2):
        sys.path.insert(0, os.path.join(D, 'herramientas')); import psarc_leer, tempfile
        tmp = tempfile.mkdtemp(); psarc_leer.read(dlc2, out=tmp, pattern='plugins/languages/')
        arch_dlc = {}
        for idioma in sorted(os.listdir(os.path.join(tmp, 'data/plugins/languages'))):
            ruta = os.path.join(tmp, 'data/plugins/languages', idioma, 'entries.xml')
            if os.path.exists(ruta): arch_dlc['data/plugins/languages/%s/entries.xml' % idioma] = con_textos(open(ruta, encoding='utf8', newline='').read(), idioma)
        psarc_parche.parchear(dlc2, os.path.join(S, 'dlc2.psarc'), arch_dlc)
        print('DLC 2: textos añadidos también en salida/dlc2.psarc')
    a = open(os.path.join(J, 'eboot.bin'), 'rb').read(); b = bytes(parchear_eboot(bytearray(a), nombres))
    open(os.path.join(S, 'eboot.bin'), 'wb').write(b); open(os.path.join(S, 'eboot.ips'), 'wb').write(ips(a, b))
    x = xdelta3()
    if x:
        for nm in ('eboot', 'data2') + (('dlc2',) if os.path.exists(os.path.join(J, 'dlc2.psarc')) and textos else ()):
            ext = '.bin' if nm == 'eboot' else '.psarc'
            subprocess.run([x, '-e', '-9', '-S', 'none', '-f', '-B', '134217728', '-s', os.path.join(J, nm + ext), os.path.join(S, nm + ext), os.path.join(S, nm + '.xdelta')], check=True)
    print('Hecho. En salida/: eboot.bin, data2.psarc, eboot.ips' + (', eboot.xdelta, data2.xdelta' if x else ' (instala xdelta3 para sacar también los .xdelta)'))

if __name__ == '__main__': main()
