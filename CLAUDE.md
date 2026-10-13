# Stolperbeats bank editor

Lokale editor voor de pattern banks van de Stolperbeats (Making Sound Machines, Eurorack drum trigger sequencer). Bestand openen, patronen bewerken, beluisteren, en terugschrijven naar de SD-kaart.

Eerst voor eigen gebruik. Delen of een platform komt later, misschien.

## Uitgangspunten

- **Eén zelfstandig HTML-bestand** (`stolperbeats-bank-editor.html`). Geen build-stap en geen framework, zolang dat volstaat.
- **Geen externe bronnen.** Geen CDN's, Google Fonts of analytics. Ook geen hosting op Amerikaanse infrastructuur (Cloudflare, Vercel, Netlify, Supabase, AWS en dergelijke). GitHub voor code is oké.
  - Hosting later: Bunny.net (SI) voor statisch, of Hetzner (DE/FI) met Caddy en PocketBase als er een backend nodig is.
- UI-teksten in het Nederlands. Moduletermen blijven Engels zoals op het paneel (Kick, Shuffle, Feeling, Linear).
- Communicatie: nuchter, direct en kort. Geen marketingtaal.

## Bestandsformaat (PatternBankNNN.txt)

Platte tekst op de root van de SD-kaart (FAT32). Voorbeeld uit een door Making Sound Machines gepubliceerde bank:

```
KICK > PTN0: 1110000000000000, 1110000000000000, 1110000000000000, 1110000000000111;
...
KICK > PTN23: ...;

SNARE > PTN0: ...;
...

HIHAT1 > PTN0: 0100000001000000;
```

- **Tracks, in deze volgorde:** KICK, SNARE, HIHAT1, HIHAT2, PERC1, PERC2.
- **Patronen:** 24 per track (PTN0–PTN23).
- **Steps:**
  - KICK en SNARE: 4 groepen van 16 steps (4 bars).
  - Overige tracks: 1 groep van 16 steps (1 bar, loopt).
- **Opmaak:** groepen gescheiden door `, `, regel eindigt op `;`, een lege regel tussen tracks.
- **Banknummering:** `PatternBank004.txt` is bank 5 op de module (nul-geïndexeerd, 3 cijfers). Er zijn 64 banken; 4 fabrieksbanken (000–003).
- **`MachineConfig.txt`:** bevat onder meer `PATTERNBANK_ACTIVE: 1111000000000000, 0000000000000000, 0000000000000000, 0000000000000000;`. Dat zijn 4 × 16 bits, bit 1 = bank 1. Een bank is alleen bereikbaar met de Bank-knoppen als zijn bit 1 is.
- De module schrijft zelf naar de kaart zodra je de sequencer stopt (patronen, instellingen, MIDI-banken). Verwissel de kaart alleen met de module uit.

Bronnen:
- https://patchstorage.com/pattern-bank-120bpm-halftime-beats/ (installatie en voorbeeldbank)
- https://kittenvillage.gumroad.com/l/fwysrl (voorbeeld van `PATTERNBANK_ACTIVE`)

## Gedrag van de module (uit de quickstart)

- **Tempo:** 30–300 bpm. Een step is een 1/16 in 4/4, vóór shuffle.
- **Shuffle:** 7 stuks. De handleiding toont per tel (4 steps) het aantal onderverdelingen en op welke posities de steps vallen. De handleiding noemt dit zelf een visuele benadering.

  | # | n | posities |
  |---|---|----------|
  | 1 | 4 | 0,1,2,3 |
  | 2 | 7 | 0,2,4,6 |
  | 3 | 9 | 0,2,5,7 |
  | 4 | 5 | 0,1,3,4 |
  | 5 | 6 | 0,1,4,5 |
  | 6 | 8 | 0,1,5,7 |
  | 7 | 9 | 0,1,6,8 |

- **Timing:**
  - Trip: n-tuplets.
  - Shake: 8th-note swing.
  - Push: ruimte voor de downbeats.
  - Clave: 3:3:2 blijft vast.

  De werking is niet gedocumenteerd en zit niet in de preview.
- **Feeling:**
  - Tight: alles samen.
  - Rolls: Hihat 2 wordt een trigger-burst.
  - Flam: kick en snare iets later.
  - Slop: als Flam, en de hihats volgen kick en snare.
- **Linear:** snare wint van kick, beide winnen van de hihats (dempt steps).
- **MIDI out:** 7 tracks (6 instrumenten en Subdiv), per track kanaal, noot, velocity en duur. 32 MIDI-banken, ook op SD. Het formaat daarvan is onbekend.
- **MIDI in:**
  - Kanaal 1–6: noten 0–127 lopen door de 24 patronen van de actieve bank.
  - Kanaal 7: Subdiv.
  - Kanaal 8: shuffle.
  - Kanaal 9: feeling, en per 4 noten de timing.
- **MIDI clock:** 24 ppqn in en uit.

## Code

- **Bestand:** `stolperbeats-bank-editor.html`, met in volgorde CSS, markup en script.
- **Core:** `// @core-start` … `// @core-end` bevat pure functies zonder DOM: `TRACKS`, `parseBank`, `serializeBank`, `bankNumFromName`, `nameFromBankNum`, `SHUFFLES`, `hitsAt`. De tests laden dit blok los in Node. Houd het DOM-vrij.
- **Parser:**
  - Accepteert ook kleine letters, ontbrekende spaties of `;`, en een BOM.
  - Rapporteert onbekende regels en afwijkende lengtes. Onbekende regels worden niet teruggeschreven.
  - Regeleinde (LF/CRLF) blijft behouden.
- **Audio:** Web Audio, synthese per track (`VOICES`). De open hat wordt gechoked door een gesloten hat of een nieuwe open hat. Lookahead-scheduler (25 ms tick, 120 ms vooruit). Shuffle wordt per tel berekend in `stepTime()`.
- **Bestanden:** File System Access API (Chrome/Edge desktop) voor direct opslaan. Anders een `<input type=file>` en download. Drag & drop werkt met `getAsFileSystemHandle` waar dat beschikbaar is.

## Tests

```
node tests/make_fixture.mjs     # genereert tests/fixtures/PatternBank004.txt
node tests/core_test.mjs        # parse/serialize round-trip (LF/CRLF), tolerantie, linear
python3 tests/ui_test.py        # Playwright/Chromium: laden, bewerken, afspelen, download, volumes, mobiel; screenshots in tests/out/
```

## Open punten

- De rest van `MachineConfig.txt` en het formaat van de MIDI-bankbestanden. Vraag Bart om de inhoud van zijn SD-kaart, of mail Making Sound Machines.
- Er is nog niet getest met echte bestanden van de kaart.

## Backlog (globaal, op volgorde)

1. SD-kaartmap openen (`showDirectoryPicker`): banken tonen en wisselen, en `PATTERNBANK_ACTIVE` aan- en uitzetten. Altijd eerst een back-up (ZIP) van de map maken voordat er iets wordt geschreven.
2. Exacte shuffle-preview: de MIDI-out van de module opnemen via Web MIDI. Gebruik een bank met alle steps aan en neem alle 7 × 4 × 4 combinaties op. Sla de offsets op als tabel.
3. Web MIDI-bediening: patronen, shuffle en feeling op de module kiezen via MIDI in.
4. Importeren: MIDI-bestand naar patroon.
5. Delen via een URL zonder backend (een bank is 576 bytes, ongeveer 770 tekens base64url).
