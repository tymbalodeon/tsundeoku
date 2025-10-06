#!/usr/bin/env nu

def --wrapped main [...args: string] {
  cargo add ...$args
}
