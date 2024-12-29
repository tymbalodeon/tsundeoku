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
      then
        with pkgs; [
          zlib.dev
          (with darwin.apple_sdk.frameworks; [
            CoreFoundation
            CoreServices
            SystemConfiguration
          ])
          darwin.IOKit
        ]
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
