{
  description = "tsundeoku";

  inputs = {
    flake-schemas.url =
      "https://flakehub.com/f/DeterminateSystems/flake-schemas/*.tar.gz";
    nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/0.1.*.tar.gz";
  };

  outputs = { self, flake-schemas, nixpkgs }:
    let
      supportedSystems = [ "x86_64-darwin" ];

      forEachSupportedSystem = f:
        nixpkgs.lib.genAttrs supportedSystems
          (system: f { pkgs = import nixpkgs { inherit system; }; });
    in
    {
      schemas = flake-schemas.schemas;

      devShells = forEachSupportedSystem
        ({ pkgs }: {
          default = pkgs.mkShell
            {
              packages = with pkgs; [
                bat
                fzf
                gh
                git-cliff
                just
                nixpkgs-fmt
                nushell
                onefetch
                pdm
                nodePackages.pnpm
                python311
                (with python311Packages; [
                  pip
                  pre-commit-hooks
                ])
                tokei
              ];
            };
        });
    };
}
