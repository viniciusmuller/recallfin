{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:
    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python-packages = ps: with ps; [
          numpy
          mss
          pytesseract
          # TODO: remove GTK2 support if cv.imshow is not being used
          (opencv4.override { enableGtk2 = true; })
        ];
      in
      {
        devShell = with pkgs; mkShell rec {
          buildInputs = [ 
            (python310.withPackages python-packages)
            sqlite
          ];
          nativeBuildInputs = [
            xorg.libX11
            xorg.libXrandr
          ];
          shellHook = ''
            export LD_LIBRARY_PATH="${lib.makeLibraryPath nativeBuildInputs}";
          '';
        };
      });
}