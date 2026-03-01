/**
 * Remix Pipeline — Bitwig Controller Extension
 *
 * Targets: Bitwig Studio 5.3.13+ (Controller API v18)
 * Compatible: Bitwig 6.0 beta (NoteInput, Track, Transport, Application APIs are stable)
 *
 * Integration:
 *  - Listens on OSC port 8000 for commands from the Python pipeline
 *  - Creates instrument tracks per stem, routes IAC MIDI channels to each
 *  - Arms all tracks, starts recording, then stops/rewinds/plays on /remix/done
 *
 * NoteInput channel filter masks (OSC 1.0 hex notation):
 *   "9?????" = channel 10 (drums, 0-indexed ch 9)
 *   "1?????" = channel 2  (bass,   0-indexed ch 1)
 *   "2?????" = channel 3  (guitar, 0-indexed ch 2)
 *   "3?????" = channel 4  (piano,  0-indexed ch 3)
 *   "4?????" = channel 5  (other,  0-indexed ch 4)
 *   "0?????" = channel 1  (vocals, 0-indexed ch 0)
 */

loadAPI(18);

host.defineController(
    "Remix Pipeline",
    "Remix Pipeline",
    "1.0.0",
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
);

// 1 MIDI in (IAC Driver Bus 1), 0 MIDI out
host.defineMidiPorts(1, 0);
host.addDeviceNameBasedDiscoveryPair(["IAC Driver Bus 1"], []);

// ── Stem definitions ──────────────────────────────────────────
// Ordered: each stem maps to its MIDI channel (0-indexed) and NoteInput filter mask
var STEMS = [
    { name: "Vocals", channel: 0,  mask: "0?????" },
    { name: "Bass",   channel: 1,  mask: "1?????" },
    { name: "Guitar", channel: 2,  mask: "2?????" },
    { name: "Piano",  channel: 3,  mask: "3?????" },
    { name: "Other",  channel: 4,  mask: "4?????" },
    { name: "Drums",  channel: 9,  mask: "9?????" },
];

// ── Globals ───────────────────────────────────────────────────
var transport;
var application;
var trackBank;
var midiInPort;
var oscServer;
var stemTracks = [];  // Track objects indexed by stem position

function init() {
    transport   = host.createTransport();
    application = host.createApplication();
    trackBank   = host.createMainTrackBank(16, 2, 8);
    midiInPort  = host.getMidiInPort(0);

    // Set up NoteInput per stem — each routes only the matching MIDI channel
    for (var i = 0; i < STEMS.length; i++) {
        var stem = STEMS[i];
        var noteInput = midiInPort.createNoteInput(stem.name, stem.mask);
        noteInput.setShouldConsumeEvents(false);  // don't block other routing
    }

    // OSC server on port 8000
    var oscModule = host.getOscModule();
    oscServer = oscModule.serverBuildAndRegister(function(builder) {
        builder.setPort(8000);
        builder.build();
    });

    // Register OSC handlers
    oscServer.registerAddressCallback("/remix/build",  function(source, msg) { handleBuild(source, msg); });
    oscServer.registerAddressCallback("/remix/done",   function(source, msg) { handleDone(); });
    oscServer.registerAddressCallback("/remix/play",   function(source, msg) { transport.play(); });
    oscServer.registerAddressCallback("/remix/stop",   function(source, msg) { transport.stop(); });
    oscServer.registerAddressCallback("/remix/bpm",    function(source, msg) { handleBpm(msg); });
    oscServer.registerAddressCallback("/remix/mute",   function(source, msg) { handleMute(msg); });
    oscServer.registerAddressCallback("/remix/solo",   function(source, msg) { handleSolo(msg); });
    oscServer.registerAddressCallback("/remix/volume", function(source, msg) { handleVolume(msg); });

    host.println("Remix Pipeline controller ready — OSC port 8000");
}

// ── OSC Handlers ──────────────────────────────────────────────

function handleBuild(source, msg) {
    // /remix/build <manifest_path_string>
    host.println("Remix Pipeline: /remix/build received");

    // Create one instrument track per stem
    stemTracks = [];
    for (var i = 0; i < STEMS.length; i++) {
        application.createInstrumentTrack(-1);
    }

    // Wait one scheduler cycle for tracks to be created, then name + arm them
    host.scheduleTask(function() {
        var count = trackBank.getSizeOfBank();
        var trackCount = Math.min(STEMS.length, count);

        // Tracks are added at the end — work backwards from the bank end
        // to find the newly created tracks
        var baseIndex = count - STEMS.length;
        if (baseIndex < 0) baseIndex = 0;

        for (var i = 0; i < STEMS.length; i++) {
            var track = trackBank.getItemAt(baseIndex + i);
            if (track != null) {
                track.name().set(STEMS[i].name);
                track.arm().set(true);
                stemTracks.push(track);
            }
        }

        // Start recording
        transport.record();
        host.println("Remix Pipeline: tracks armed, recording started");
    }, null, 500);  // 500ms delay
}

function handleDone() {
    // /remix/done — stop recording, disarm, rewind, play
    host.println("Remix Pipeline: /remix/done — stopping recording");

    transport.stop();

    // Disarm all tracks
    for (var i = 0; i < stemTracks.length; i++) {
        if (stemTracks[i] != null) {
            stemTracks[i].arm().set(false);
        }
    }

    // Rewind to bar 1 and play
    host.scheduleTask(function() {
        transport.position().set(0);
        host.scheduleTask(function() {
            transport.play();
            host.println("Remix Pipeline: playback started");
        }, null, 200);
    }, null, 300);
}

function handleBpm(msg) {
    // /remix/bpm <float>
    if (msg.getArgumentCount() > 0) {
        var bpm = msg.getArgument(0).getFloat();
        transport.tempo().rawValue().set(bpm);
        host.println("Remix Pipeline: BPM set to " + bpm);
    }
}

function handleMute(msg) {
    // /remix/mute <stem_name_string> <bool>
    if (msg.getArgumentCount() < 2) return;
    var stemName = msg.getArgument(0).getString().toLowerCase();
    var muted    = msg.getArgument(1).getBoolean();
    var track    = findTrackByName(stemName);
    if (track != null) {
        track.mute().set(muted);
    }
}

function handleSolo(msg) {
    // /remix/solo <stem_name_string> <bool>
    if (msg.getArgumentCount() < 2) return;
    var stemName = msg.getArgument(0).getString().toLowerCase();
    var soloed   = msg.getArgument(1).getBoolean();
    var track    = findTrackByName(stemName);
    if (track != null) {
        track.solo().set(soloed);
    }
}

function handleVolume(msg) {
    // /remix/volume <stem_name_string> <float 0.0-1.0>
    if (msg.getArgumentCount() < 2) return;
    var stemName = msg.getArgument(0).getString().toLowerCase();
    var volume   = msg.getArgument(1).getFloat();
    var track    = findTrackByName(stemName);
    if (track != null) {
        track.volume().value().set(volume);
    }
}

// ── Helpers ───────────────────────────────────────────────────

function findTrackByName(name) {
    for (var i = 0; i < stemTracks.length; i++) {
        var track = stemTracks[i];
        if (track != null) {
            var trackName = track.name().get().toLowerCase();
            if (trackName.indexOf(name) !== -1) {
                return track;
            }
        }
    }
    return null;
}

// ── Lifecycle ─────────────────────────────────────────────────

function flush() {
    // Called periodically — nothing to flush
}

function exit() {
    host.println("Remix Pipeline controller exiting");
}
