"""
Albert plugin to switch audio output (PipeWire/PulseAudio).

Usage:
    sound          -> list all audio outputs
    sound casque   -> filter outputs by name
"""

import subprocess
import threading
import time
from albert import (
    Action,
    PluginInstance,
    StandardItem,
    TriggerQueryHandler,
    Query,
    makeThemeIcon,
)

md_iid = "4.0"
md_version = "1.0"
md_name = "Switch Sound Output"
md_description = "Switch audio output and move active streams"
md_license = "MIT"
md_url = "https://github.com/valentin/albert-plugin-xfce-switch-sound"
md_authors = ["@valentin"]

# Cache for sinks data
_cache = {"sinks": [], "default": "", "timestamp": 0}
CACHE_TTL = 2  # seconds


def _refresh_cache():
    """Refresh the sinks cache."""
    now = time.time()
    if now - _cache["timestamp"] < CACHE_TTL:
        return

    # Get sinks with descriptions
    result = subprocess.run(
        ["pactl", "list", "sinks"],
        capture_output=True,
        text=True,
        timeout=2,
    )
    sinks = []
    current_sink = {}
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line.startswith("Sink #"):
            if current_sink:
                sinks.append(current_sink)
            current_sink = {"id": line.split("#")[1]}
        elif line.startswith("Name:"):
            current_sink["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Description:"):
            current_sink["description"] = line.split(":", 1)[1].strip()
    if current_sink:
        sinks.append(current_sink)

    # Get default sink
    result = subprocess.run(
        ["pactl", "get-default-sink"],
        capture_output=True,
        text=True,
        timeout=1,
    )
    default = result.stdout.strip()

    _cache["sinks"] = sinks
    _cache["default"] = default
    _cache["timestamp"] = now


def get_sinks():
    """Get list of available audio sinks (cached)."""
    _refresh_cache()
    return _cache["sinks"]


def get_default_sink():
    """Get the current default sink name (cached)."""
    _refresh_cache()
    return _cache["default"]


def switch_to_sink(sink_name):
    """Switch to the specified sink and move all active streams (in background)."""
    def _do_switch():
        subprocess.run(["pactl", "set-default-sink", sink_name], timeout=2)
        result = subprocess.run(
            ["pactl", "list", "sink-inputs", "short"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split()
                if parts:
                    subprocess.run(
                        ["pactl", "move-sink-input", parts[0], sink_name],
                        timeout=1,
                    )
        # Invalidate cache
        _cache["timestamp"] = 0

    thread = threading.Thread(target=_do_switch, daemon=True)
    thread.start()


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

    def id(self):
        return "switch-sound"

    def name(self):
        return md_name

    def description(self):
        return md_description

    def defaultTrigger(self):
        return "sound "

    def synopsis(self, query):
        return "<output name>"

    def handleTriggerQuery(self, query: Query):
        query_str = query.string.strip().lower()

        try:
            sinks = get_sinks()
            default_sink = get_default_sink()
        except Exception:
            query.add(
                StandardItem(
                    id="switch-sound-error",
                    text="Error loading audio outputs",
                    subtext="Check if PulseAudio/PipeWire is running",
                    icon_factory=lambda: makeThemeIcon("dialog-error"),
                )
            )
            return

        if not sinks:
            query.add(
                StandardItem(
                    id="switch-sound-error",
                    text="No audio outputs found",
                    subtext="Make sure PulseAudio/PipeWire is running",
                    icon_factory=lambda: makeThemeIcon("dialog-error"),
                )
            )
            return

        for sink in sinks:
            sink_name = sink.get("name", "")
            description = sink.get("description", sink_name)
            is_default = sink_name == default_sink

            if query_str:
                if query_str not in description.lower() and query_str not in sink_name.lower():
                    continue

            if is_default:
                text = f"{description} (active)"
                icon_name = "audio-volume-high"
            else:
                text = description
                icon_name = "audio-card"

            if "bluez" in sink_name.lower():
                icon_name = "bluetooth-active" if is_default else "bluetooth"
            elif "usb" in sink_name.lower():
                icon_name = "audio-headphones"

            query.add(
                StandardItem(
                    id=f"switch-sound-{sink['id']}",
                    text=text,
                    subtext=sink_name,
                    icon_factory=lambda icon=icon_name: makeThemeIcon(icon),
                    actions=[
                        Action(
                            id="switch",
                            text=f"Switch to {description}",
                            callable=lambda s=sink_name: switch_to_sink(s),
                        ),
                    ],
                )
            )
