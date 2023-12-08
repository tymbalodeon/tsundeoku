# Tsundeoku

> 積んでおく ("tsundeoku"), "to pile up for later"

Tsundeoku is a CLI tool that helps you take audio files from a shared folder and
"pile them up for later" by importing them to a [beets](https://beets.io/)
library. When importing, albums in the folder that have already been imported
will be skipped (not possible with beets alone), and newly added albums will
only be imported automatically if all tracks have finished syncing. This way,
the import command can safely be run repeatedly to catch all new additions to
the shared folder without creating any problems in the beets library.

Metadata can also be changed to suit the user's preferences. For example, there
are rules to alter common metadata formats that may not be to every user's
liking--to strip bracketed years (in the format: "[YYYY]") from album fields, to
expand abbreviations (such as "Rec.s" to "Recordings"), and to strip bracketed
instrument indications (in the format: "[solo \<instrument\>]") from artist
fields. Run `tsundeoku reformat --help` to see all reformat rules.

## Installation

- Install [pdm](https://pdm.fming.dev/latest/)
- Run `just build` to install the `tsundeoku` command in your shell.

You will need to [configure beets](https://beets.readthedocs.io/en/stable/guides/main.html#configuring).
A default beets config (using "~/Music" as the "directory") can be generated by
running `just beets`. To provide a different directory, or to set other options,
follow the instructions in the beets documentation. You will also need to
[import your library](https://beets.readthedocs.io/en/stable/guides/main.html#importing-your-library)
in order to get started and generate the pickle file.

If your local library is on an external drive, you will need to give "Full Disk
Access" to `/bin/zsh` in System Preferences > Security & Privacy > Privacy >
Full Disk Access.

## Usage

- To import new audio files from your shared folder to your music library:
  `tsundeoku import` (or `tsundeoku import --as-is` to leave the metadata untouched)
- To reformat metadata for all previously imported tracks: `tsundeoku reformat`
- Tsundeoku uses a config file that can be viewed and edited with:
`tsundeoku config` and `tsundeoku config --edit`
- For more information: `tsundeoku --help` or `tsundeoku <command> --help`
