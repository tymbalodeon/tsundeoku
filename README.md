# Musicbros

A CLI for managing imports from a shared folder (such as in Dropbox) to a
[beets](https://beets.io/) library. When importing, albums in the folder that
have already been imported will be skipped (not possible with beets alone), and
newly added albums will only be imported automatically if all tracks have
finished syncing. This way, the import command can safely be run repeatedly to
catch all new additions to the shared folder without creating any problems in
the beets library.

Track metadata can be changed to suit the user's preferences. For personal use,
I have included a default option to strip bracketed years (in the format:
"[YYYY]") from all album tags, expand the abbreviation "Rec.s" to "Recordings"
in all album tags, and strip bracketed solo instrument indications from all
artist tags (in the format: "[solo {instrument}]").

# Installation

Run `make build` to install the `musicbros` command in your shell.

# Usage

- For information about each command: `musicbros --help`
- To create, update, and view your config file storing the location of your
  shared folder and beets pickle file: `musicbros config` (or `musicbros config --update`)
- To import new audio files from your shared folder to your music library:
  `musicbros import-new` (or `musicbros import-new --as-is` to leave the
  metadata untouched)
- To update metadata for all previously imported tracks: `musicbros remove-nonsense`
