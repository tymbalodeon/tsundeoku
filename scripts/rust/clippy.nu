#!/usr/bin/env nu

# TODO
# try adding this and documenting everything:
# -W clippy::missing_docs_in_private_items

def main [] {
  (
    cargo clippy
      --allow-dirty
      --allow-staged
      --fix
      --
        -A clippy::fn_params_excessive_bools
        -A clippy::module_name_repetitions
        -W clippy::nursery
        -W clippy::pedantic
        -A clippy::too_many_arguments
        -A clippy::too_many_lines
        -W clippy::unwrap_used
  )
}
