#!/usr/bin/env nu

use find-script.nu

export def display-just-help [
  recipe?: string
  subcommands?: list<string>
  --environment: string
  --justfile: string
] {
  let args = [
    --color always
    --list
  ]

  if ($recipe | is-empty) {
    let args = (
      $args
      | append (
          match $justfile {
            null => [--list-submodules]
            _ => [--justfile $justfile]
          }
        )
    )

    return (^just ...$args)
  }

  let recipe = match $environment {
    null => $recipe
    _ => $"($environment)/($recipe)"
  }

  let script = (find-script $recipe)
  mut recipe_is_module = false

  let script = if ($script | is-empty) {
    let args = ([$recipe] ++ $subcommands)

    if ($args | length) > 1 {
      $recipe_is_module = true

      find-script (
        $args
        | window 2
        | first
        | str join "/"
      )
    } else {
      try {
        return (^just ...$args $recipe --quiet err> /dev/null)
      } catch {
        return
      }
    }
  } else {
    $script
  }

  let subcommands = if $recipe_is_module {
    $subcommands
    | drop nth 0
  } else {
    $subcommands
  }

  if (rg "^def main --wrapped" $script | is-not-empty) {
    if ($subcommands | is-empty) {
      nu $script "--self-help"
    } else {
      nu $script ...$subcommands "--self-help"
    }
  } else {
    if ($subcommands | is-empty) {
      nu $script --help
    } else {
      nu $script ...$subcommands --help
    }
  }
}

def get-sortable-environment [
  alias: record<
    alias: string,
    environment: string,
    recipe: string
  >
] {
  if ($alias.environment == •) {
    null
  } else {
    $alias.environment
  }
}

export def display-aliases [
  no_submodule_aliases: bool # Don't include submodule aliases
  sort_by_environment: bool # Sort aliases by environment name
  sort_by_recipe: bool # Sort recipe by original recipe name
  --environment: string # View aliases for $environment only
  --justfile: string # Which Justfile to use
] {
  # TODO: add color always/never feature
  # TODO: remove space when no environment name present
  let justfile = if ($justfile | is-empty) {
    "Justfile"
  } else {
    $justfile
  }

  let aliases = (
    open $justfile
    | lines
    | where {str starts-with  alias}
    | str replace "alias " ""
    | each {
        |alias|

        let parts = (
          $alias
          | split row ":="
          | str trim
        )

        let recipe_parts = ($parts | last | split row "::")

        {
          alias: ($parts | first)

          environment: (
            if ($recipe_parts | length) > 1 {
              ($recipe_parts | first)
            } else {
              "•"
            }
          )

          recipe: ($recipe_parts | last)
        }
      }
  )

  let aliases = if $no_submodule_aliases {
    $aliases
    | where {$in.alias == $in.recipe}
  } else {
    $aliases
  }

  let aliases = if ($environment | is-not-empty) {
    $aliases
    | where environment =~ $environment
  } else {
    $aliases
  }

  if ($aliases | is-empty) {
    return
  }

  let aliases = if ($environment | is-empty) and $sort_by_environment {
    $aliases
    | sort-by --custom {
        |a, b|

        (get-sortable-environment $a) < (get-sortable-environment $b)
      }
  } else if $sort_by_recipe {
    $aliases
    | sort-by recipe
  } else {
    $aliases
    | sort-by alias
  }

  print (
    $aliases
    | each {
        |alias|

        let alias_name = $"(ansi magenta_bold)($alias.alias)(ansi reset)"
        let environment = $"(ansi cyan_bold)($alias.environment)(ansi reset)"

        $"($alias_name) => ($environment) ($alias.recipe)"
      }
    | to text
    | column -t
    | str replace --all "•" " "
  )
}

# View module aliases
def "main aliases" [
  environment?: string # View aliases for $environment only
  --justfile: string # Which Justfile to use
  --sort-by-environment # Sort aliases by environment name
  --sort-by-recipe # Sort recipe by original recipe name
  --no-submodule-aliases # Don't include submodule aliases
] {
  (
    display-aliases
      $no_submodule_aliases
      $sort_by_environment
      $sort_by_recipe
      --environment $environment
      --justfile $justfile
  )
}

# View help text
def main [
  recipe?: string # View help text for recipe
  ...subcommands: string  # View help for a recipe subcommand
  --default
] {
  display-just-help $recipe $subcommands
}
