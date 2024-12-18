beets_config_values := """
directory: ~/Music
library: ~/.config/beets/library.db
import:
  incremental: yes
  autotag: no
"""

_beets:
    #!/usr/bin/env nu

    let beets_config_folder = $"($env.HOME)/.config/beets"
    mkdir $beets_config_folder
    echo "{{beets_config_values}}" | save --raw $"($beets_config_folder)/config.yaml"

setup: _beets build
