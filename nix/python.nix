{pkgs}: {
  packages = with pkgs; [
    nodePackages.pnpm
    python313
    uv
  ];
}
