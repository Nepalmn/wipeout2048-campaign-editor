WipEout 2048 Campaign Editor (2048 campaign map)
=================================================

Create new seasons after 2050 and build the mod, ready for Vita3K (or as patches to share).

What you can do
- Add and remove seasons (up to 24) and events.
- Choose each event's type (race, time trial, zone, eliminator), starting from any of the 60
  original events as a template.
- Change track, class (C, B, A, A+), laps, AI, weapons, and pass/elite objectives.
- Custom time-trial targets (m:ss.cc), zone targets for Zone events and points for Eliminators.
- Ship restrictions per event: allowed classes (speed, agility, combat, prototype) or a forced ship
  (any of the 20).
- Move events and banners anywhere on the map, change each tile's shape and its unlock order.
  The editor draws banners with the exact triangles they cover in game.
- Change the colour of the season banners, or draw your own banner (brush, text, shapes or an
  imported image).
- The editor marks in red anything that overlaps or falls outside the area the game supports.

Game limits (why there are caps)
- More than 210 new events has not been tested.
- Hand-drawn banners take space in a game texture that is almost full: about 2 drawings of 7x3,
  3 of 6x2 or 4 of 4x2 fit. If they don't fit, "Construir mod" (Build) tells you.
- Banners are opaque: if two overlap, one covers the other. Events are drawn on top of banners.
- In the editor a banner fills its whole area; in game only the drawing shows (the rest is white).

Requirements
- Python 3 with Pillow and NumPy:   pip install pillow numpy
- ImageMagick (the "magick" command) to write the texture.
- Optional: xdelta3, to also build .xdelta patches.
- A .ttf font at fuente/fuente.ttf for the digits on the banners (if missing, DejaVu Sans Bold
  or Arial Bold from the system is used).
- WipEout 2048 EU (PCSF00007) with the 1.04 update, as installed by Vita3K.
  Copy these two files from your game into the juego/ folder:
     ux0/app/PCSF00007/eboot.bin
     ux0/app/PCSF00007/PSP2/data2.psarc
  (the program checks they are the right ones; they are not modified).

Usage
1. Start the editor:  python3 servidor.py   (Windows: iniciar.bat, Linux: ./iniciar.sh)
   It opens in the browser: http://localhost:8765
   The first run reads your game files (a few seconds) and loads an example campaign (2051-2070).
2. Edit. "Guardar" (Save) writes campana.json (with backups in copias/).
3. "Construir mod" (Build mod) writes to salida/:
     eboot.bin and data2.psarc  -> copy them over the game's files (back up the originals)
     eboot.ips, eboot.xdelta, data2.xdelta -> patches to share your campaign without
                                              distributing game files
   You can also share your campana.json: anyone with the editor can build it.

Save files
- Back up your save (ux0/user/00/savedata/PCSF00007) before trying a campaign.
- If you change the TYPE of an existing event, the editor gives it a new ID: this way saved games
  don't hang (each type stores its data with a different size).
- If you had already finished 2050, replay "2050 - Event 9" to unlock the first new season.

Mouse
- Click an event or banner: edit it in the right-hand panel.
- Drag: move it ("Arrastrar temporada entera" moves the whole season with its banner).
- Right-click an event: next shape.
- Ctrl + wheel or pinch: zoom.
