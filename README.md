# luced-music

A music editor written in Luce with `luce-ui`, in luced-3d's grey and orange.
A song is tracks; a track has lanes (subtracks) of clips, each lane all
notes or all automation curves, and a rack: a node network of the
instruments and effects it plays through. Every instrument and effect is
itself a network of the engine's nodes (oscillators, filters, envelopes,
LFOs, delays...), opened with a double-click as luced-3d opens a Material.
Sound comes from [luce-audio](../luce-audio)'s realtime engine, written in
Luce Base.

```sh
luc run --release                  # opens the demo song, audio on
luc run --release -- song.prisma   # opens a song
luc run -- --no-audio              # starts with the output off
```

## Using it

- **Space** plays and stops, **Enter** stops and returns, **Home** goes to
  the start, **L** toggles the loop. Click the ruler to seek; Shift-drag it
  to set the loop.
- **Arrangement.** Double-click an empty lane for a clip of a bar; drag a
  clip to move it (Alt copies), its right edge to resize it; Delete removes,
  Cmd-D duplicates. A mouse wheel, Cmd-scroll or pinch zooms; the middle
  button or a touchpad pans (Shift-wheel scrolls the tracks). M and S on a
  track mute and solo it; ● arms it; the bar beside them is its meter.
- **Scales.** The Scale row under the ruler holds the song's key changes:
  double-click to add one, pick it to set its root and scale (Major, Minor,
  the modes, pentatonics, Blues, Whole Tone, Hirajoshi…), drag its edge to
  move it, Delete removes it. Every track following the song plays its notes
  in the key in force where each starts; the clips keep what was written. A
  track's *Scale* is the song's keys, as written (drums), or its own keys on
  its row. The piano roll lights the key's notes and marks a note it moves.
- **MIDI and recording.** MIDI from any source plays the selected track (or,
  once any is armed, the armed tracks), through its scale; each track picks
  its MIDI input and channel in Parameters. **R** records (starting the
  transport): what the listening tracks hear lands, on Stop, as a clip of
  whole bars on their notes lane, placed on the beat it was heard. **C**
  toggles the metronome; the MIDI light flashes as messages come in.
- **Clip editor.** A note clip is a piano roll: click to add a note, drag to
  lengthen it; drag notes to move them, their right edge to resize; the keys
  play the lane's instrument. A curve clip: click adds a point, drag moves
  it, Alt-click removes, right-click makes it hold. A clip's *Loop every*
  repeats its content until it ends.
- **Network.** The selected track's rack: each lane is a node whose notes or
  curve value wire into a device; devices wire audio into others and into
  Track Out (whose volume and pan take curves too). Tab adds an instrument,
  an effect, or inside a patch any engine node. Drag between sockets to wire
  (green notes, orange audio, blue control, grey a patch's signals); Alt-click
  an input to unwire; double-click a device to open its patch, U to go back.
- **Groups and presets.** In a patch, drag a box (or Shift-click) to pick
  nodes and press Cmd-G: they collapse into one Group node whose sockets are
  the Inlet and Outlet nodes inside it (made for every wire that crossed the
  selection's edge). Double-click a group to enter it, U to go up; groups
  nest; Cmd-Shift-G expands one. Picked, a group shows every knob inside it.
  Cmd-Shift-P saves the picked group as a *module* or the picked device as an
  *instrument* preset (`~/.luced-music/presets/`); Tab offers them as "My
  module" and "My instrument" (an instrument may also go into a patch as a
  group, to layer it). Build modules (an oscillator bank, a ladder filter, an
  envelope pair) and assemble your own synthesizer from them.
- **Parameters** shows what was clicked last; knobs reach the engine as they
  move, and each drag is one undo step (Cmd-Z, Cmd-Shift-Z).
- Songs save as Prism text (`.prisma`), File › Save (Cmd-S).

## Sounds

The engine's analog models (luce-audio `models.lucb`, `effects.lucb`,
`studio.lucb`, `machines.lucb`, `mixing.lucb`, `fm.lucb`):

- **Sources:** Analog VCO (drift, sync), Supersaw (the JP-8000's seven
  saws), FM Operator (the DX7's operator: wire six as an algorithm), Tine
  Piano (Rhodes).
- **Filters:** Ladder (Minimoog), SEM (Oberheim), CS Filter (CS-80), MS-20,
  Diode Ladder (TB-303 / VCS3), Multimode (Elektron).
- **Drums:** Rytm-style Kick, Snare, Metal, Clap; Drum Machine (LinnDrum /
  DMX / DrumTraks: drums played from 8-bit μ-law words at their own clock).
- **Shaping:** Analog Envelope, OTA VCA, Drive (eight circuits), LFO and
  Tempo LFO (locked to the song).
- **Effects:** Plate, Hall (eight-line FDN; Gate for the 80s snare, Shimmer
  for the Mercury7 glow), Echo (tape, BBD, digital), Chorus (Juno,
  Dimension, Ensemble), Tape (Studio, Cassette, VHS: wow, flutter, bump,
  hiss), Pump (the tempo-synced sidechain duck), Compressor (BOUM squash),
  EQ (cuts, shelves, two bells), Bus Comp (VCA/SSL, FET/1176, Opto/LA-2A,
  Vari-Mu; side HPF, auto release, parallel mix), Limiter (lookahead, true
  peak, auto release), Width (M/S, mono bass, Haas), Freq Shifter,
  Phaser, Flanger, Tremolo, Lo-Fi.

Nonlinear cores run at 2x with antiderivative anti-aliasing.

Presets: analog voices (Model D, Moog Bass, OB Pad, CS Brass, Rhodes,
MS/TB Acid), the retro library (Juno Stab and Arp, Prophet Pluck and
Strings, Xpander Pad, Mini Lead, Truise Lead, Monster/Octave/Pedal Bass,
Sync Lead, Mother Arp, Drone, Howl Lead, Rival Pulse, Chord Pad, Stacked
Mono, Supersaw), the DX7 (DX Piano, Bass, Brass, Bells, Glass), drum
machines (Linn kit, Tambourine, Shaker; Rytm kit) and effect chains
(Tape Deck, Cassette, VHS, Pump, Hall, Gated Hall, Cathedral, Wide, EQ,
Low Cut, Glue, Drum Bus, Freq Shift, Plate, Blade Runner Hall, echoes,
choruses, BOUM, Heat...).

A song's **Master** track hears every other track's mix through its rack:
the mastering chain (the Master preset: EQ, SSL bus compression, tape, the
limiter at -1 dBTP). `tools/analyze.py` reads integrated loudness (LUFS,
BS.1770) and true peak.

Songs: the demos (Demo, Blade Runner, Elektron, Acid) and five style
studies, original songs after the records of Com Truise (Cathode Haze),
Tycho (Coastal Drift), Makeup and Vanity Set (Night Signal), Kavinsky
(Night Interceptor, Neon Boulevard) and Rival Consoles (Memory Field) — `src/songs.luc`.

`tools/bounce` renders every song to `~/Music/Luced Music Bounces` as WAV
and `.prisma` (`--stems` for a file per track, `--only NAME`, `--presets`
to audition every preset); `tools/analyze.py` measures a bounce (level,
stereo width, aliasing).

Design notes: [docs/DESIGN.md](docs/DESIGN.md).
