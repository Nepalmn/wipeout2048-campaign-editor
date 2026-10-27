# construir.py [campana.json] : genera el mod a partir de la campaña del editor.
# Salida en salida/: eboot.bin y data2.psarc listos para copiar, eboot.ips y (si hay xdelta3) data2.xdelta.
import os, sys, re, json, struct, shutil, subprocess, random, zlib
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
    ultimo = previo = por_nombre['2050 - Event 9']; nuevos = []
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
        if C.get('desbloquearTodo'): cambios.append(('m_bForceAlwaysUnlocked', 'true'))      # solo para pruebas
        for f, v in cambios: b = set_opt(b, f, v)
        if tipo == 'carrera' and e['plantilla'] == '2050 - Event 9':
            gm = re.search(r'<M_PGRIDSHIPMODELDATA.*?</M_PGRIDSHIPMODELDATA>', b, re.S).group(0); ng = gm
            for a, g in zip(re.findall(r'<ARRAY value="[^"]*"', gm), GRID): ng = ng.replace(a, '<ARRAY value="%s"' % g, 1)
            b = b.replace(gm, ng)
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
    T0 = 0x814adc20; viejos = [struct.unpack_from('<I', d, off(0x8151e9b8 + 4 * i))[0] for i in range(48)]
    cad = T0 + 4 * (48 + len(nombres)); ptrs = []; blob = b''
    for n in nombres: ptrs.append(cad + len(blob)); blob += n.encode() + b'\0'
    fin = cad + len(blob)
    if fin >= 0x814adc1c + 1712: raise SystemExit('Demasiados carteles (%d piezas): quita temporadas o usa carteles dibujados' % len(nombres))
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
    psarc_parche.parchear(os.path.join(J, 'data2.psarc'), os.path.join(S, 'data2.psarc'), {
        'data/xml/SP.xml': sp.encode('utf8'), 'data/plugins/frontend/NEWGUI/Definition.xml': defxml.encode('utf8'),
        'data/FE/NewImages/canvasTexture.gxt': open(tex, 'rb').read()})
    a = open(os.path.join(J, 'eboot.bin'), 'rb').read(); b = bytes(parchear_eboot(bytearray(a), nombres))
    open(os.path.join(S, 'eboot.bin'), 'wb').write(b); open(os.path.join(S, 'eboot.ips'), 'wb').write(ips(a, b))
    x = xdelta3()
    if x:
        for nm in ('eboot', 'data2'):
            ext = '.bin' if nm == 'eboot' else '.psarc'
            subprocess.run([x, '-e', '-9', '-f', '-B', '134217728', '-s', os.path.join(J, nm + ext), os.path.join(S, nm + ext), os.path.join(S, nm + '.xdelta')], check=True)
    print('Hecho. En salida/: eboot.bin, data2.psarc, eboot.ips' + (', eboot.xdelta, data2.xdelta' if x else ' (instala xdelta3 para sacar también los .xdelta)'))

if __name__ == '__main__': main()
