#!/usr/bin/env nu

# Check for leaked secrets
def main [] {
  gitleaks git
}
