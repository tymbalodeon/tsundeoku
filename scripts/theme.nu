#!/usr/bin/env nu

def main [theme: string] {
  mkdir .helix

  {theme: $theme}
  | save --force .helix/config.toml
}

def "main reset" [] {
  rm --force .helix/config.toml

  if (ls .helix | is-empty) {
    rm .helix
  }
}
