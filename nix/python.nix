{pkgs}: {
  packages = with pkgs; [
    nodePackages.pnpm
    # TODO
    # fix me
    # py-spy
    python311
    ruff
    uv
  ];
}
