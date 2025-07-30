#!/usr/bin/env nu

def main [] {
  zellij --layout $"($env.ENVIRONMENTS)/rust/layout.kdl"
}
