{pkgs}: {
  packages = with pkgs;
    [
      libiconv
      cargo-bloat
      cargo-edit
      cargo-outdated
      cargo-udeps
      cargo-watch
      rust-analyzer
      zellij
    ]
    ++ (
      if stdenv.isDarwin
      then [pkgs.zlib.dev]
      else
        (
          if stdenv.isLinux
          then
            with pkgs; [
              pkg-config
              openssl
            ]
          else []
        )
    );

  RUST_BACKTRACE = 1;
}
