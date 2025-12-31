# Albert Sound Switcher Plugin

An [Albert](https://albertlauncher.github.io/) plugin to quickly switch audio outputs on Linux systems using PipeWire or PulseAudio.

## Features

- List all available audio outputs
- Filter outputs by name
- Switch default audio sink with a single action
- Automatically moves all active audio streams to the new output
- Smart icons for Bluetooth and USB devices
- Fast response with built-in caching

## Requirements

- [Albert Launcher](https://albertlauncher.github.io/) v0.26+ (uses Python interface 4.0)
- PipeWire or PulseAudio
- `pactl` command-line tool (usually included with PulseAudio/PipeWire)

## Installation

Using [Task](https://taskfile.dev/):

```bash
task install
```

Or manually:

```bash
mkdir -p ~/.local/share/albert/python/plugins
ln -sfn /path/to/this/repo ~/.local/share/albert/python/plugins/switch-sound
```

Then restart Albert and enable the plugin in **Settings > Plugins > Python**.

## Usage

Type `sound` in Albert to list all audio outputs:

```
sound          # List all audio outputs
sound casque   # Filter outputs by name
```

Press Enter to switch to the selected output. All currently playing audio streams will be automatically moved to the new output.

## Uninstallation

```bash
task uninstall
```

Or remove the symlink manually:

```bash
rm ~/.local/share/albert/python/plugins/switch-sound
```

## License

MIT
