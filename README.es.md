# Editor de campañas para WipEout 2048

*[English](README.md)*

Editor web para crear temporadas nuevas en el mapa de la campaña 2048 de **WipEout 2048** (PS Vita, versión europea PCSF00007 1.04), más allá de 2050. Genera el mod listo para Vita3K, o parches para compartirlo sin repartir archivos del juego.


## Qué se puede hacer

- Añadir y quitar temporadas (hasta 28) y eventos.
- Elegir el tipo de cada evento (carrera, contrarreloj, zona, eliminator) a partir de cualquiera de los 60 eventos originales.
- Cambiar pista, clase (C, B, A, A+), vueltas, IA, armas y objetivos de pase y élite.
- Mover eventos y carteles por el mapa, cambiar la forma de cada casilla y el orden de desbloqueo.
- Cambiar el color de los carteles de temporada o dibujar carteles propios.
- Ver en rojo lo que se pisa o se sale de la zona que admite el juego.

El ejecutable se parchea para quitar los límites del juego: memoria para el progreso, memoria de textos, tabla de carteles y desbloqueo al repetir un evento. Los detalles están en [`construir.py`](construir.py).

## Requisitos

- Python 3 con Pillow y NumPy: `pip install pillow numpy`
- ImageMagick (la orden `magick`).
- Opcional: `xdelta3` para generar parches `.xdelta`.
- Tu copia de WipEout 2048 europeo 1.04 instalada en Vita3K. Copia a `juego/`:
  - `ux0/app/PCSF00007/eboot.bin`
  - `ux0/app/PCSF00007/PSP2/data2.psarc`

## Uso

```sh
python3 servidor.py      # o ./iniciar.sh  /  iniciar.bat en Windows
```

Se abre http://localhost:8765. "Construir mod" deja en `salida/` el `eboot.bin` y el `data2.psarc` para copiar sobre los del juego, y los parches `eboot.ips`, `eboot.xdelta` y `data2.xdelta`. El archivo `campana.json` se puede compartir: quien tenga el editor puede construir esa campaña.

Más detalles, límites y avisos sobre las partidas guardadas: [`LEEME.txt`](LEEME.txt).

## Campaña 2051-2070

La campaña de ejemplo (`campana.ejemplo.json`) tiene 20 temporadas y 210 eventos. Los parches para jugarla sin el editor están en [Releases](../../releases).
