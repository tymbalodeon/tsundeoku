#!/usr/bin/env nu

# TODO: add sort by options
# NOTE: nushell doesn't seem to allow dynamic values in `sort-by`

# TODO: add help text

# TODO: align indices to the right (and add color?)

def "main open" [
  index: int
  path?: string
] {
  hx (
    get-todos $path
    | get $index
    | get file
    | ansi strip
  )
}

def color [target: string color: string]: string -> string {
  $in
  | str replace $target $"(ansi $color)($target)(ansi reset)"
}

def get-todos [path?: string] {
  let pattern = "# (FIXME|NOTE|TODO)"

  let matches = if ($path | is-empty) {
    rg $pattern --json
  } else {
    rg $pattern --json $path
  }

  $matches
  | lines
  | each {|line| $line | from json}
  | flatten
  | transpose
  | transpose --header-row
  | where {$in.lines | is-not-empty}
  | str trim
  | select line_number path.text lines.text
  | rename line_number file comment
  | sort-by comment
  | update comment {
      |row|

      (
        $row.comment
        | color FIXME red_bold
        | color NOTE blue_bold
        | color TODO cyan_bold
      )
    }
  | update file {
      |row|

      let file = $"(ansi magenta)($row.file)(ansi reset)"
      let line_number = $"(ansi green)($row.line_number)(ansi reset)"

      $"($file):($line_number)"
    }
}

def main [
  path?: string # A path to search for keywords
] {
  get-todos $path
  | enumerate
  | each {|item| $"($item.index) • ($item.item.file) • ($item.item.comment)" }
  | to text
  | column -s • -t
}
