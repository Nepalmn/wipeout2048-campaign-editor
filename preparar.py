# preparar.py : lee juego/eboot.bin y juego/data2.psarc (WipEout 2048 EU PCSF00007 1.04) y deja en trabajo/
# lo que necesitan el editor y construir.py. Solo hace falta ejecutarlo una vez.
import os, sys, re, json, hashlib, struct
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(D, 'herramientas'))
import psarc_leer, gxt
J, T = os.path.join(D, 'juego'), os.path.join(D, 'trabajo')
MD5 = {'eboot.bin': '8a27cac8b94630a56b4aa9e36c201a2f', 'data2.psarc': 'ed8a9e47eabb85e349918aca38438081'}
TIPOS = {'-1353052320': 'carrera', '-1915183557': 'contrarreloj', '1018671239': 'zona', '1311982788': 'eliminator'}
CAMPOS = ['m_speedClass', 'm_numOfLaps', 'm_skillScale', 'm_bDisableWeapons', 'm_trackDef', 'm_PassObjective',
          'm_EliteObjective', 'm_buttonShape', 'm_x', 'm_y', 'm_description', 'm_bPreventSpeedShips', 'm_bPreventAgilityShips',
          'm_bPreventCombatShips', 'm_bPreventProtoShips', 'm_pPlayerShipModelData']

def md5(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()

def field(b, f):
    m = re.search(r'<M_[A-Z0-9_]+ name="%s".*?</M_[A-Z0-9_]+>' % f, b, re.S)
    if not m: return None
    v = re.findall(r'<ARRAY value="([^"]*)"', m.group(0))
    return v[0] if v else ''

def main():
    for n, h in MD5.items():
        p = os.path.join(J, n)
        if not os.path.exists(p): sys.exit('Falta juego/%s (cópialo de tu WipEout 2048 europeo 1.04)' % n)
        if md5(p) != h: sys.exit('juego/%s no es el de la 1.04 europea sin modificar (MD5 %s, esperado %s)' % (n, md5(p), h))
    os.makedirs(os.path.join(T, 'orig'), exist_ok=True)
    for pat in ('data/xml/sp.xml', 'data/plugins/frontend/newgui/definition.xml', 'data/fe/newimages/canvastexture.gxt'):
        psarc_leer.read(os.path.join(J, 'data2.psarc'), out=os.path.join(T, 'orig'), pattern=pat)
    O = os.path.join(T, 'orig', 'data')
    sp = open(os.path.join(O, 'xml/SP.xml'), encoding='utf8').read()
    # textura de los carteles en PNG
    gxt.leer(os.path.join(O, 'FE/NewImages/canvasTexture.gxt')).save(os.path.join(T, 'atlas_orig.png'))
    # eventos originales (fijos en el mapa) y plantillas para los nuevos
    orig, plant = [], []
    for m in re.finditer(r'<instance instanceid="([-0-9]+)" typedefid="([-0-9]+)" name="([^"]*)".*?</instance>', sp, re.S):
        b = m.group(0); x, y, s = field(b, 'm_x'), field(b, 'm_y'), field(b, 'm_buttonShape')
        if not x or not y or s is None: continue
        orig.append({'n': m.group(3), 'x': int(x), 'y': int(y), 's': s or '0'})
        if m.group(2) in TIPOS and re.match(r'20(48|49|50) - Event [0-9-]+$', m.group(3)):
            plant.append(dict(n=m.group(3), tipo=TIPOS[m.group(2)], **{f: field(b, f) for f in CAMPOS}))
    pistas = {m.group(2): m.group(1) for m in re.finditer(r'<instance instanceid="([-0-9]+)" typedefid="205052969" name="([^"]*)"', sp)}
    objetivos = {m.group(2): m.group(1) for m in re.finditer(r'<instance instanceid="([-0-9]+)" typedefid="380278911" name="([^"]*)"', sp)
                 if not m.group(2).startswith('20')}
    naves = {m.group(2): m.group(1) for m in re.finditer(r'<instance instanceid="([-0-9]+)" typedefid="520725191" name="([^"]*)"', sp) if m.group(2) != 'WINGMAN'}
    pista_de = {v: k for k, v in pistas.items()}
    for p in plant: p['pista'] = pista_de.get(p['m_trackDef'] or '', '?')
    # objetivo numérico de pase/élite de cada plantilla (centésimas en contrarreloj, zona en zona, puntos en eliminator)
    obj = {m.group(1): m.group(0) for m in re.finditer(r'<instance instanceid="([-0-9]+)" typedefid="380278911".*?</instance>', sp, re.S)}
    for p in plant:
        for k, f in (('objPase', 'm_PassObjective'), ('objElite', 'm_EliteObjective')):
            b = obj.get(p[f] or '')
            p[k] = int(field(b, 'm_ObjectiveTarget') or 0) if b and p['tipo'] != 'carrera' else None
    # carteles originales del mapa 2048 (para no taparlos)
    xml = open(os.path.join(O, 'plugins/frontend/NEWGUI/Definition.xml'), encoding='utf8').read()
    labs = []
    for nm, v in re.findall(r'<CanvasLabel name="([^"]*)">\s*<Values ([^>]*)>', xml):
        if nm.endswith('Label') or nm.endswith('CampaignTitle') or nm.startswith('MPSeason'): continue   # MPSeason = mapa online
        a = dict(re.findall(r'(\w+)="([^"]*)"', v))
        try: labs.append({'n': nm, 'x': int(a['x']), 'y': int(a['y']), 'w': int(a['width']), 'h': int(a['height'])})
        except (KeyError, ValueError): pass
    json.dump({'orig': orig, 'origLabels': labs}, open(os.path.join(T, 'base.json'), 'w'))
    json.dump({'plantillas': plant, 'pistas': pistas, 'objetivos': objetivos, 'naves': naves}, open(os.path.join(T, 'plantillas.json'), 'w'), indent=0, ensure_ascii=False)
    print('Listo: %d eventos originales, %d plantillas, %d pistas, %d naves, %d carteles originales' % (len(orig), len(plant), len(pistas), len(naves), len(labs)))

if __name__ == '__main__': main()
