# Editor de campañas para WipEout 2048

*[English](README.md)*

Editor web para crear temporadas nuevas en el mapa de la campaña 2048 de **WipEout 2048** (PS Vita, versión europea PCSF00007 1.04), más allá de 2050. Genera el mod listo para Vita3K, o parches para compartirlo sin repartir archivos del juego.


## Qué se puede hacer

- Añadir y quitar temporadas (hasta 24) y eventos.
- Elegir el tipo de cada evento (carrera, contrarreloj, zona, eliminator) a partir de cualquiera de los 60 eventos originales.
- Cambiar pista, clase (C, B, A, A+), vueltas, IA, armas y objetivos de pase y élite.
- Curva de dificultad: la IA sube poco a poco a lo largo de los eventos nuevos (y luego retocas cada evento).
- Tiempos propios en las contrarrelojes (m:ss.cc), zona a alcanzar en las zonas y puntos en los eliminators.
- Naves rivales: elige la nave de cada uno de los 7 pilotos de la IA (o rellénalos todos por clase de un clic).
- Textos propios para cada evento (en español e inglés; los demás idiomas conservan su traducción original).
- Restricciones de naves por evento: tipos permitidos (velocidad, agilidad, combate, prototipo) o una nave obligatoria (cualquiera de las 20).
- Mover eventos y carteles por todo el mapa, cambiar la forma de cada casilla y el orden de desbloqueo. Los carteles se dibujan con los triángulos exactos que ocupan en el juego.
- Cambiar el color de los carteles de temporada o dibujar carteles propios.
- Ver en rojo lo que se pisa o se sale de la zona que admite el juego.

El ejecutable se parchea para quitar los límites del juego: memoria para el progreso, memoria de textos, tabla de carteles, desbloqueo al repetir un evento y que las finales de las temporadas nuevas no muestren las copas de 2048-2050. Las carreras con un número de vueltas distinto de 3 llevan su texto actualizado automáticamente. Los detalles están en [`construir.py`](construir.py).

## Cómo instalar la campaña 2051-2070 (parches)

Solo necesitas tu propia copia del juego y un navegador. No se reparte ningún archivo del juego: los parches solo llevan los cambios.

**1. Qué necesitas**
- WipEout 2048 **europeo** (PCSF00007) con la actualización **1.04**, instalado en Vita3K.
- Los parches de [Releases](../../releases): `eboot.xdelta` y `data2.xdelta` (hacen falta los dos).

**2. Busca los archivos del juego**
- En Vita3K: *Archivo → Abrir carpeta de datos* (Open Pref Path). Entra en `ux0/app/PCSF00007/`.
- Necesitas dos archivos: `eboot.bin` (en esa carpeta) y `PSP2/data2.psarc`.
- **Haz una copia de los dos** antes de nada.

**3. Parchéalos en el navegador con [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/)**
1. *ROM file*: elige tu `eboot.bin`. *Patch file*: elige `eboot.xdelta`. Pulsa **Apply patch**. Se descarga `eboot (patched).bin`.
2. Recarga la página. *ROM file*: elige tu `data2.psarc` (110 MB, tarda unos segundos; el aviso «file is too big» de la suma de comprobación es normal). *Patch file*: `data2.xdelta`. Pulsa **Apply patch**. Se descarga `data2 (patched).psarc`.
3. Cambia el nombre de las descargas a `eboot.bin` y `data2.psarc`.

Si un parche falla, tus archivos no son los de la 1.04 europea. Los MD5 para comprobarlo están en `LEEME.txt`, dentro de la release.

**4. Vuelve a ponerlos en su sitio**
- `eboot.bin` → `ux0/app/PCSF00007/eboot.bin`
- `data2.psarc` → `ux0/app/PCSF00007/PSP2/data2.psarc`

**5. A jugar**
- Antes, haz copia de tu partida (`ux0/user/00/savedata/PCSF00007`).
- Conservas tu progreso. Las temporadas nuevas aparecen en el mapa de la campaña después de 2050. Si ya habías terminado 2050, vuelve a pasar **2050 - Evento 9** una vez para abrir 2051.

**Si usas Firestar:** si tienes un mod de Firestar (por ejemplo, una banda sonora) instalado en el DLC 2, trae su propia copia de los textos del juego, que tapa los de la campaña. Los 10 eventos con el texto corregido mostrarían una clave como `CAMP_…_TXT`. Para arreglarlo, pon tu `dlc2.psarc` en la carpeta `juego/` del editor y construye: el editor añade los textos también a tu DLC, sin tocar tu banda sonora.

**Con la línea de comandos** (xdelta3):
```sh
xdelta3 -d -s eboot.bin eboot.xdelta eboot_nuevo.bin
xdelta3 -d -B 134217728 -s data2.psarc data2.xdelta data2_nuevo.psarc
```

**PS Vita / PSTV real** (sin probar todavía): los archivos parcheados deberían funcionar con rePatch en `ux0:rePatch/PCSF00007/` (`eboot.bin` y `PSP2/data2.psarc`). Los parches están hechos sobre el `eboot.bin` descifrado que instala Vita3K, así que el de un volcado de consola puede tener otro MD5.

## Editor: requisitos

- Python 3 con Pillow y NumPy: `pip install pillow numpy`
- ImageMagick (la orden `magick`).
- Opcional: `xdelta3` para generar parches `.xdelta`.
- Tu copia de WipEout 2048 europeo 1.04 instalada en Vita3K. Copia a `juego/`:
  - `ux0/app/PCSF00007/eboot.bin`
  - `ux0/app/PCSF00007/PSP2/data2.psarc`

## Editor: uso

```sh
python3 servidor.py      # o ./iniciar.sh  /  iniciar.bat en Windows
```

Se abre http://localhost:8765. "Construir mod" deja en `salida/` el `eboot.bin` y el `data2.psarc` para copiar sobre los del juego, y los parches `eboot.ips`, `eboot.xdelta` y `data2.xdelta`. El archivo `campana.json` se puede compartir: quien tenga el editor puede construir esa campaña.

Más detalles, límites y avisos sobre las partidas guardadas: [`LEEME.txt`](LEEME.txt).

## Campaña 2051-2070

La campaña de ejemplo (`campana.ejemplo.json`) tiene 20 temporadas y 210 eventos: clases A y A+, IA difícil en los eventos nuevos (2048-2050 quedan sin tocar), una contrarreloj, una zona y un eliminator por temporada, y 30 eventos con restricciones de naves. También corrige un fallo de traducción del juego original: el texto en español del eliminator 2050 - Evento 3 decía «Agilidad» en un evento de naves de velocidad.

Los tiempos de las contrarrelojes son todavía los del juego original: si haces buenos tiempos, compártelos para ajustar la campaña. Los parches para jugarla sin el editor están en [Releases](../../releases).
