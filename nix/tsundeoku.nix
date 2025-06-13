{pkgs}: {
  packages = with pkgs; [
    cargo-release
    mdbook
    vhs
  ];
}
