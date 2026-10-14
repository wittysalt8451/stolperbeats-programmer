# Stolperbeats editor

Lokale editor voor de SD-kaart van de Stolperbeats (Making Sound Machines, Eurorack drum trigger sequencer): pattern banks, `MachineConfig.txt`, `EnvelopeSettings.txt` en `MachineState.txt`. Bestanden openen, bewerken, patronen beluisteren, en terugschrijven naar de kaart.

Eerst voor eigen gebruik. Delen of een platform komt later, misschien.

## Uitgangspunten

- **Eén zelfstandig HTML-bestand** (`index.html`). Geen build-stap en geen framework, zolang dat volstaat.
- **Geen externe bronnen.** Geen CDN's, Google Fonts of analytics. De pagina laadt niets van internet. Gewone links naar de handleiding mogen.
- **Hosting:** GitHub Pages vanaf `main`, uit de root van de repo. Bart heeft daar in oktober 2026 bewust voor gekozen. `.nojekyll` zorgt dat Pages de bestanden ongewijzigd serveert.
  - Mocht er ooit een backend nodig zijn, dan liever geen Amerikaanse infrastructuur (Cloudflare, Vercel, Netlify, Supabase, AWS en dergelijke), maar Hetzner (DE/FI) met Caddy en PocketBase. Bunny.net (SI) is het alternatief voor statische hosting.
- **De frontend is altijd in het Engels.** Dat geldt voor alle UI-teksten, meldingen, de uitleg op de startpagina en het codecommentaar in het HTML-bestand. Gebruik de termen van het paneel en de handleiding (Kick, Shuffle, Feeling, Linear). Met Bart communiceer je in het Nederlands.
- Communicatie: nuchter, direct en kort. Geen marketingtaal.

## Bestanden op de SD-kaart

Platte tekst op de root van de kaart (FAT32). De module schrijft alles met CRLF. `default_settings/` bevat kopieën van Barts kaart (firmware 163). De tests gebruiken ze.

De module leest de kaart bij het opstarten. Zodra je de sequencer stopt, schrijft hij patronen, instellingen en MIDI-maps terug. Verwissel de kaart dus alleen met de module uit. Als je alle bestanden wist, schrijft de module bij de volgende start de fabrieksbestanden.

### PatternBankNNN.txt

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
- **Banknummering:** `PatternBank004.txt` is bank 5 op de module (nul-geïndexeerd, 3 cijfers). Er zijn 64 banken. Fabrieksbanken: 1–4, plus 5 (firmware 157) en 6 (firmware 160).

### Instellingenbestanden

Eén `KEY: value;` per regel, met lege regels als scheiding. `MachineConfig.txt` zet een spatie na de dubbele punt, de andere twee niet. De editor bewaart elke regel zoals hij is en vervangt alleen waarden.

**`MachineConfig.txt`** (gedocumenteerd in de handleiding, tenzij anders vermeld)
- `PATTERNBANK_ACTIVE: 1111111000000000, 0000000000000000, 0000000000000000, 0000000000000000;` bestaat uit 4 × 16 bits. Het eerste bit is bank 1. Alleen actieve banken zijn bereikbaar met de Bank-knoppen.
- `HIGHLIGHT_PLAY_POSITION`, `FIRST_PULSE_CLOCK_STARTS_SEQ`, `LAST_PULSE_CLOCK_STOPS_SEQ`, `RESET_TOGGLES_PLAY_STOP`, `MIDI_ENABLE_CLOCK_OUT`, `MIDI_ENABLE_TRANSPORT_OUT`, `MIDI_ENABLE_CLOCK_IN`, `MIDI_ENABLE_TRANSPORT_IN` en `MIDI_ENABLE_INPUT` zijn 0/1. Transport werkt alleen als clock aan staat.
- `WRITE_MACHINE_STATE` en `WRAP_PATTERN_ENCODER` zijn 0/1 en niet gedocumenteerd. De betekenis is afgeleid van de naam.
- `FIRMWARE_BUILD: 163;` wordt door de module geschreven.

**`EnvelopeSettings.txt`**, voor ENV1 en ENV2:
- `ENVn_WAVEFORM` is een van 9 golfvormen in de volgorde van de handleiding: Ramp down, Ramp up, Triangle up, Triangle down, Sine, Cosine, Pulse high, Pulse low, Stepped.
- `ENVn_CLOCKDIV` is een van 17 waarden: x4, x2, x1, .5, 1, dan bd, Sd, H1, H2, P1, P2, dan :bd … :P2.
- `ENVn_LFO_VEL` en `ENVn_LFO_LOW_VEL` zijn de bovenste en onderste grens voor x4–P2.
- `ENVn_<TRACK>_VEL` en `ENVn_<TRACK>_LOW_VEL` zijn de accent- en non-accent-velocity voor :bd–:P2, per instrument. Bereik 0–127.

**`MachineState.txt`**
- `TEMPO`, `TIMING`, `SHUFFLE`, `FEEL`, `LINEAR` en `BANK`.
- Het patroon per track: `KICK` … `PERC2`, 0–23.
- `SUBDIV`, `SYNCIN` en `SYNCOUT`.
- Mutes per track: `KICKMUTE` … `SUBDIVMUTE`.
- `MIDIBANK`.

**`MIDIMapNNN.txt`** (000–031, nog niet in de editor)

```
KICK >
CH:9, NOTE:36, VEL:127, LOW_VEL:95, DUR:10;

SNARE >
...
SUBDIV >
CH:9, NOTE:50, VEL:47, LOW_VEL:8, DUR:10;
```

`CH` is nul-geïndexeerd: `CH:9` is kanaal 10 (GM-drums bij MIDIMap003, de Arturia Drumbrute).

**Indexen.** Patroonnummers en MIDI-kanalen tellen bevestigd vanaf 0. De editor neemt aan dat `TIMING`, `SHUFFLE`, `FEEL`, `BANK`, `SUBDIV`, `SYNCIN`, `MIDIBANK`, `ENVn_WAVEFORM` en `ENVn_CLOCKDIV` ook vanaf 0 tellen, in de volgorde van de handleiding. In de UI staan die velden als *inferred*. De volgorde van `SYNCOUT` is onbekend: de UI toont de ruwe waarde.

Bronnen:
- https://makingsoundmachines.com/stolperbeats/manual/ (webhandleiding, bijgewerkt september 2025: SD-kaart, ENV, Sync, changelog)
- https://patchstorage.com/pattern-bank-120bpm-halftime-beats/ (installatie en voorbeeldbank)
- https://kittenvillage.gumroad.com/l/fwysrl (voorbeeld van `PATTERNBANK_ACTIVE`)

## Gedrag van de module (quickstart en webhandleiding)

- **Tempo:** 15–250 bpm volgens de webhandleiding (de quickstart noemde 30–300). Een step is een 1/16 in 4/4, vóór shuffle.
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
- **Linear:** dempt steps. Sinds firmware 157 geldt Snare > Kick > HH2 > HH1 en Snare > Kick > Perc 2 > Perc 1. De preview (`hitsAt`) volgt nog de oude regel: snare wint van kick, beide winnen van de hihats.
- **ENV 1/2:** tempo-synced 10 V CV. Op de module stel je ze in via ENV options (Subdiv-encoder 2 s indrukken). De bovenste encoderrij is ENV 1, de onderste ENV 2.
- **Sync:**
  - In: 1, 2, 3, 4, 6, 8, 12, 16 of 24 ppqn.
  - Out: 1–10, 12, 16 of 24 ppqn, of x1/x2/x4 bars.
- **MIDI out:** 7 tracks (6 instrumenten en Subdiv), per track kanaal, noot, velocity en duur. 32 MIDI-banken (`MIDIMapNNN.txt`).
- **MIDI in:**
  - Kanaal 1–6: noten 0–127 lopen door de 24 patronen van de actieve bank.
  - Kanaal 7: Subdiv.
  - Kanaal 8: shuffle.
  - Kanaal 9: feeling, en per 4 noten de timing.
  - Kanaal 11: mutes. Noot 124–127 zijn Play, Pause, Stop en Reset.
- **MIDI clock:** 24 ppqn in en uit.

## Code

- **Bestand:** `index.html`, met in volgorde CSS, markup en script.
- **Startpagina:** zonder hash in de URL kom je op de startpagina (`#panel-home`). Je komt er ook terug door op het logo te klikken. De pagina heeft een hero met een foto van de module, een Open-knop en links naar de tabs, met daaronder de volledige uitleg. `buildGuide()` vult de tabellen daarin vanuit de schema's.
  - De foto staat als base64-JPEG in het laatste `<script>`-blok. Lees het bestand daarom met offset/limit, want die regel is ongeveer 225 KB lang. Het bronbestand is `images/stolperbeats.png`. Na een wijziging maak je opnieuw een JPEG: `sips -Z 760 -s format jpeg -s formatOptions 70`, daarna base64.
- **Tabs, in deze volgorde:** Patterns, Envelopes, Config en Default state. Intern heten ze `patterns`, `env`, `config` en `state`. De hash in de URL kiest de tab (`#env`).
  - Elk bestand heeft een eigen tab met Open, Save en Download.
  - Open en drag & drop accepteren meerdere bestanden. `fileKind()` stuurt elk bestand naar de juiste tab.
  - Ctrl/Cmd+S slaat het bestand van de huidige tab op. Space en Ctrl/Cmd+Z werken alleen op de Patterns-tab.
- **Core:** `// @core-start` … `// @core-end` bevat pure functies zonder DOM. De tests laden dit blok los in Node, dus houd het DOM-vrij. Het blok bevat:
  - `TRACKS`, `parseBank`, `serializeBank`, `bankNumFromName`, `nameFromBankNum`, `SHUFFLES` en `hitsAt`.
  - `parseSettings`, `serializeSettings`, `getSetting`, `setSetting`, `parseBits`, `formatBits` en `fileKind`.
- **Bankparser:**
  - Accepteert ook kleine letters, ontbrekende spaties of `;`, en een BOM.
  - Rapporteert onbekende regels en afwijkende lengtes. Onbekende regels worden niet teruggeschreven.
  - Regeleinde (LF/CRLF) blijft behouden. Een nieuwe bank krijgt CRLF.
- **Instellingen:**
  - `SET.config`, `SET.env` en `SET.state` bevatten elk een geparst document, een file handle, een dirty-vlag en een `build()`.
  - De formulieren worden gebouwd uit kleine controls (`row`, `switchCtl`, `segCtl`, `selectCtl`, `numCtl`). Die schrijven via `put()`, waarna `syncSettings()` afgeleide weergaven bijwerkt: waarschuwingen, de envelope-schets en de controle of de bank actief is.
  - Onbekende sleutels blijven staan. Ontbrekende sleutels worden niet toegevoegd.
- **Audio:** Web Audio, synthese per track (`VOICES`). De open hat wordt gechoked door een gesloten hat of een nieuwe open hat. Lookahead-scheduler (25 ms tick, 120 ms vooruit). Shuffle wordt per tel berekend in `stepTime()`.
- **Bestanden:**
  - Opslaan gaat direct via de File System Access API (Chrome/Edge desktop). Anders via een `<input type=file>` en een download.
  - Drag & drop gebruikt `getAsFileSystemHandle` waar dat beschikbaar is.
  - Pickers gebruiken `id: 'stolperbeats'`, zodat de browser de map onthoudt.

## Tests

```
node tests/make_fixture.mjs     # genereert tests/fixtures/PatternBank004.txt
node tests/core_test.mjs        # round-trips (LF/CRLF, echte bestanden uit default_settings/), tolerantie, linear, instellingen, fileKind
python3 tests/ui_test.py        # Playwright/Chromium: startpagina, patronen, afspelen, download, volumes, de drie instellingentabs, mobiel; screenshots in tests/out/
```

Playwright staat niet globaal geïnstalleerd. Installeer het in een venv: `pip install playwright` en daarna `python -m playwright install chromium`.

## Open punten

- De volgorde van de waarden is niet bevestigd voor de velden die als *inferred* gemarkeerd zijn, met `SYNCOUT` als onbekendste. Controleer ze op de module, of vraag het Making Sound Machines (post@makingsoundmachines.com).
- `WRITE_MACHINE_STATE` en `WRAP_PATTERN_ENCODER` zijn niet gedocumenteerd.
- `PatternBank006.txt` op Barts kaart is met de oude editor gemaakt en heeft LF-regeleinden. De andere bestanden hebben CRLF. Nog niet bekend of de module LF leest.

## Backlog (globaal, op volgorde)

1. SD-kaartmap openen (`showDirectoryPicker`): banken tonen en wisselen. Altijd eerst een back-up (ZIP) van de map maken voordat er iets wordt geschreven.
2. Linear in de preview bijwerken naar het gedrag van firmware 157+.
3. MIDI-maps bewerken (`MIDIMapNNN.txt`).
4. Exacte shuffle-preview: de MIDI-out van de module opnemen via Web MIDI. Gebruik een bank met alle steps aan en neem alle 7 × 4 × 4 combinaties op. Sla de offsets op als tabel.
5. Web MIDI-bediening: patronen, shuffle en feeling op de module kiezen via MIDI in.
6. Importeren: MIDI-bestand naar patroon.
7. Delen via een URL zonder backend (een bank is 576 bytes, ongeveer 770 tekens base64url).
