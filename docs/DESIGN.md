# Design

    luced-music → luce-ui, luce-prism        (the window, files)
                → luce-audio (engine)        (all sound: Base, realtime)

## The song and its graphs

`song.luc` is the document: `Song` → `Track` → `Lane` → `Clip` (notes or curve
points, in beats from the clip's start, repeated every `loop` beats), and per
track a rack `Graph`. A graph's nodes are lanes (`catalog.lane_kind`), devices
(`device_kind`, holding a patch `Graph` and a voice count) and the track's
output; a patch's nodes are the engine's kinds, read from luce-audio's table
(`catalog.luc`), so a kind added there appears in the Tab menu, the inspector
and files with no change here. Ports have a fixed `slot`: a device shows only
the ports its patch reads (notes for a Note In, audio for an Audio In, a
control per Control In) while wires keep their indices (`rack.luc`).

Every playing thing has an id from the song's counter, never reused. The
engine matches units, nodes and lanes by these ids between programs, so an
edit or an undo while playing keeps voices, filter states and sounding notes.

## Groups and presets

`groups.luc`: a Group node (`catalog.group_kind`) holds a patch; its Inlet and
Outlet nodes are its sockets, numbered by `GraphNode.port`. The engine never
sees a group: `flatten` lists every engine node at any depth and resolves
each wire through Inlets (out to the wire into the group) and groups (in to
the wire into the Outlet). `collapse` makes one Inlet per distinct outside
source and one Outlet per distinct inside output; `expand` reverses it.
Presets (`library.luc`) are one-node Prism documents under
`~/.luced-music/presets/{instruments,modules}`, written by the song file's
graph writer; `GraphNode.fresh` gives each placed copy new ids, so the engine
never matches it to the original.

## The engine bridge

`bridge.luc` describes the song to the engine (`begin` … `commit`): a track
each, a unit per device with its patch's nodes and wires, feeds between
devices, lanes with their notes and points flattened onto the timeline and
their targets (a unit's notes, a unit's control, the track's volume or pan).
Structural edits mark the bridge dirty and the panels republish once a frame;
a parameter, a track's mix, tempo and transport go to the playing program
directly. Compiling the demo song takes well under a millisecond.

## Edits and history

`workspace.luc` holds the song, selection and history. Every edit is a
transaction: `perform(label, change)` or `begin`/`commit` around a drag. The
song before it is kept whole (`Song.copy`), undo swaps it back (100 steps).
`edits.luc` holds the edits; views call them or bracket their own drags.

## Views

All custom views draw with luce-ui's Painter, as luced-3d's network does: a
mounted tree is limited to 1024 widgets, so clips, notes and nodes are drawn,
not widgets. `arrangement.luc` (tracks, lanes, clips, ruler, playhead, meters),
`clip_editor.luc` (piano roll and curve editor), `graph_view.luc` (rack and
patch networks, shader-node style), `inspector.luc` (one ParameterPanel for
what was clicked last), `panels.luc` (composition and the frame's poll).

## Checking it

`luc test` runs `tests/engine` (the demo song rendered offline: every track
sounds, mutes silence) and `tests/smoke` (the window draws three frames).
`tools/preview.py --scene rack|patch|clip|curve` captures a real Metal frame
without the screen. `tools/bench` (`luc build --release` there) measures the
engine on the demo song: about 56× realtime, 1.8% of one core.
