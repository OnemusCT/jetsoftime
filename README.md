# Temporal Redux
Temporal Redux is a remake of Geiger's Temporal Flux, an editor used to create Chrono Trigger mods. It has been implemented using a significant amount of code from the Jets of Time Chrono Trigger randomizer.

## Installation
1. Create virtual environment:
```bash
python -m venv env
source env/bin/activate  # Unix
env\Scripts\activate     # Windows

pip install .

python -m sourcefiles.temporalredux
```

Requires Python 3.7+ and PyQt6.

## Known Issues
1. Strings can't be edited
1. Conditionals menus accept a number of bytes to jump, this should be inferred instead
1. Menus not implemented: Mode7, Draw Geometery, Color Math, Copy Tiles, Scroll Layers (both versions), Sound, Wait for Silence, Color Crash
1. Sometimes crashes happen when editing the same command twice, or the subcommand menu won't change

In addition to these known issues there has not been extensive testing of the various commands and their menus.

## Jets of Time
Jets of Time is the open world Chrono Trigger randomizer that Temporal Redux is based on.

Online Seed Generator: https://www.ctjot.com  
Discord: https://discord.gg/cKYjHwj  
Wiki: https://wiki.ctjot.com/ 

### Jets of Time Credits
Most contributions can be seen in the Jets of Time commit history, but special thanks go:
* Mauron, Myself086, and Lagolunatic for general technical assistance; 
* Abyssonym for initial work on Chrono Trigger randomization (Eternal Nightmare, Wings of Time); and 
* Anskiy for originally inventing Jets of Time and developing the initial set of open world event scripts.
