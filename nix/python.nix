{pkgs}: {
  packages = with pkgs; [
    nodePackages.pnpm
    py-spy
    python311
    ruff
    uv
  ];
}
