#!/usr/bin/env nu

def main [] {
  (
    cargo clippy
      --allow-dirty
      --allow-staged
      --fix
      --
        -W clippy::pedantic
        -A clippy::too_many_lines
        -A clippy::fn_params_excessive_bools
        -A clippy::module_name_repetitions
        -A clippy::too_many_arguments
        -W clippy::nursery
        -W clippy::unwrap_used
  )
}
