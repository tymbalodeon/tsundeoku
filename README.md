# Musicbros

Musicbros is a CLI for managing imports from a shared folder to a
[beets](https://beets.io/) library. When importing, albums in the folder that
have already been imported will be skipped (not possible with beets alone), and
newly added albums will only be imported automatically if all tracks have
finished syncing. This way, the import command can safely be run repeatedly to
catch all new additions to the shared folder without creating any problems in
the beets library.

Metadata can also be changed to suit the user's preferences. For example, there
are options to strip bracketed years (in the format: "[YYYY]") from album
fields, to expand abbreviations (such as "Rec.s" to "Recordings"), and to strip
bracketed instrument indications (in the format: "[solo \<instrument\>]"). Run
`musicbros update-metadata --help` to see all update rules.

# Installation

Run `make build` to install the `musicbros` command in your shell. You will need
to [configure beets](https://beets.readthedocs.io/en/stable/guides/main.html#configuring).
A default beets config (using "~/Music" as the "directory") can be generated by
running `make beets`. To provide a different directory, or to set other options,
follow the instructions in the beets documentation. You will also need to
[import your library](https://beets.readthedocs.io/en/stable/guides/main.html#importing-your-library)
in order to get started and generate the pickle file.

# Usage

- To create, update, and view your config file storing the location of your
  shared folder and beets pickle file: `musicbros config` (or `musicbros config --update`)
- To import new audio files from your shared folder to your music library:
  `musicbros` (or `musicbros import-new --as-is` to leave the metadata untouched)
- To update metadata for all previously imported tracks: `musicbros update-metadata`
- For information about each command: `musicbros --help` or `musicbros <command> --help`
