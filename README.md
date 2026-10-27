# WipEout 2048 Campaign Editor

*[Español](README.es.md)*

A web-based editor for adding new seasons to the 2048 campaign map of **WipEout 2048** (PS Vita, EU version PCSF00007 v1.04), beyond 2050. It builds a mod ready for Vita3K, or patches you can share without distributing any game files.

## Features

- Add and remove seasons (up to 24) and events.
- Choose each event's type (race, time trial, zone, eliminator) using any of the 60 original events as a template.
- Change track, speed class (C, B, A, A+), laps, AI skill, weapons, and pass/elite objectives.
- Custom target times for time trials (m:ss.cc), zone targets for Zone events and points for Eliminators.
- Ship restrictions per event: allowed classes (speed, agility, combat, prototype) or a forced ship (any of the 20).
- Drag events and banners anywhere on the map, and change tile shapes and unlock order. Banners are drawn with the exact triangles they cover in game.
- Recolor the season banners or draw your own (brush, text, shapes or an imported image).
- Overlaps and anything outside the area the game supports are highlighted in red.

The executable is patched to lift the game's limits: progress buffer, string heap, banner table, and unlocking the next event when you replay one. The details are in [`construir.py`](construir.py).

## How to install the 2051–2070 campaign (patches)

You only need your own copy of the game and a web browser. No game files are shared: the patches only contain the changes.

**1. What you need**
- WipEout 2048 **EU** (PCSF00007) with the **1.04** update, installed in Vita3K.
- The patches from [Releases](../../releases): `eboot.xdelta` and `data2.xdelta` (you need both).

**2. Find the game files**
- In Vita3K: *File → Open Pref Path*. Then go to `ux0/app/PCSF00007/`.
- You need two files: `eboot.bin` (in that folder) and `PSP2/data2.psarc`.
- **Copy both somewhere safe as a backup** before doing anything else.

**3. Patch them in the browser with [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/)**
1. *ROM file*: choose your `eboot.bin`. *Patch file*: choose `eboot.xdelta`. Click **Apply patch**. It downloads `eboot (patched).bin`.
2. Reload the page. *ROM file*: choose your `data2.psarc` (110 MB, it takes a few seconds; the "file is too big" checksum message is normal). *Patch file*: `data2.xdelta`. Click **Apply patch**. It downloads `data2 (patched).psarc`.
3. Rename the downloads to `eboot.bin` and `data2.psarc`.

If a patch fails, your files are not the EU 1.04 ones. The MD5 checksums to compare are in `README.txt` inside the release.

**4. Put them back**
- `eboot.bin` → `ux0/app/PCSF00007/eboot.bin`
- `data2.psarc` → `ux0/app/PCSF00007/PSP2/data2.psarc`

**5. Play**
- Back up your save (`ux0/user/00/savedata/PCSF00007`) first.
- Your progress is kept. The new seasons appear on the campaign map after 2050. If you had already finished 2050, replay **2050 – Event 9** once to unlock 2051.

**Command line alternative** (xdelta3):
```sh
xdelta3 -d -s eboot.bin eboot.xdelta eboot_new.bin
xdelta3 -d -B 134217728 -s data2.psarc data2.xdelta data2_new.psarc
```

**Real PS Vita / PSTV** (not tested yet): the patched files should work with rePatch in `ux0:rePatch/PCSF00007/` (`eboot.bin` and `PSP2/data2.psarc`). The patches are made against the decrypted `eboot.bin` that Vita3K installs, so a dump from a console may have a different MD5.

## Editor: requirements

- Python 3 with Pillow and NumPy: `pip install pillow numpy`
- ImageMagick (the `magick` command).
- Optional: `xdelta3` to build `.xdelta` patches.
- Your own copy of WipEout 2048 EU 1.04 installed in Vita3K. Copy these into `juego/`:
  - `ux0/app/PCSF00007/eboot.bin`
  - `ux0/app/PCSF00007/PSP2/data2.psarc`

  The editor checks their MD5 and never modifies them.

## Editor: usage

```sh
python3 servidor.py      # or ./iniciar.sh  /  iniciar.bat on Windows
```

It opens http://localhost:8765. The first run reads your game files (a few seconds) and loads the example campaign (2051–2070).

- **Guardar** (Save) writes `campana.json`, with backups in `copias/`.
- **Construir mod** (Build mod) writes to `salida/`:
  - `eboot.bin` and `data2.psarc`: copy them over the game's files (back up the originals first).
  - `eboot.ips`, `eboot.xdelta`, `data2.xdelta`: patches for sharing your campaign.
- You can also share your `campana.json`: anyone with the editor can build it.

The interface is in Spanish for now. Limits and save-file notes are in [`README.txt`](README.txt).

## Save files

- Back up your save (`ux0/user/00/savedata/PCSF00007`) before trying a campaign.
- Old saves keep their progress. If you had already finished 2050, replay *2050 – Event 9* to unlock the first new season.
- If you change the **type** of an existing event, the editor gives it a new ID, so older saves don't hang on load (each type stores its data with a different size).

## The 2051–2070 campaign

The example campaign (`campana.ejemplo.json`) has 20 seasons and 210 events, A and A+ class, hard AI, a time trial, a zone and an eliminator per season, and 30 events with ship restrictions. Patches to play it without the editor are in [Releases](../../releases).

Tested on Vita3K (PC and ROG Ally). Not yet tested on a real Vita.

The time-trial targets are still the original game's: if you set good times, share them so the campaign can get proper targets!
