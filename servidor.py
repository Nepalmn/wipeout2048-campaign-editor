# servidor.py : editor de campañas en http://localhost:8765 (guarda en campana.json y construye el mod)
import http.server, os, json, shutil, time, subprocess, sys, webbrowser
D = os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=D, **k)
    def responder(s, code, txt):
        b = txt.encode('utf8'); s.send_response(code); s.send_header('Content-Type', 'text/plain; charset=utf-8')
        s.send_header('Content-Length', str(len(b))); s.end_headers(); s.wfile.write(b)
    def do_POST(s):
        datos = s.rfile.read(int(s.headers.get('Content-Length', 0)))
        if s.path == '/guardar':
            p = os.path.join(D, 'campana.json'); os.makedirs(os.path.join(D, 'copias'), exist_ok=True)
            if os.path.exists(p): shutil.copy(p, os.path.join(D, 'copias', 'campana.%s.json' % time.strftime('%Y%m%d-%H%M%S')))
            json.dump(json.loads(datos), open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
            return s.responder(200, 'ok')
        if s.path == '/construir':
            r = subprocess.run([sys.executable, '-I', os.path.join(D, 'construir.py')], capture_output=True, text=True, cwd=D)
            return s.responder(200 if r.returncode == 0 else 500, (r.stdout + r.stderr).strip())
        s.send_error(404)
    def end_headers(s):
        s.send_header('Cache-Control', 'no-store'); super().end_headers()
    def log_message(s, *a): pass
if __name__ == '__main__':
    if not os.path.exists(os.path.join(D, 'trabajo', 'plantillas.json')):
        subprocess.run([sys.executable, '-I', os.path.join(D, 'preparar.py')], check=True)
    if not os.path.exists(os.path.join(D, 'campana.json')):
        shutil.copy(os.path.join(D, 'campana.ejemplo.json'), os.path.join(D, 'campana.json'))
    print('Editor en http://localhost:8765  (Ctrl+C para cerrar)')
    if '--sin-navegador' not in sys.argv: webbrowser.open('http://localhost:8765')
    http.server.ThreadingHTTPServer(('127.0.0.1', 8765), H).serve_forever()
