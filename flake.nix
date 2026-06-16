{
  description = "Thesis LaTeX build environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      tex = pkgs.texlive.combined.scheme-full;
      # Python interpreter with the deps the figure/analysis scripts need.
      pythonEnv = pkgs.python3.withPackages (ps: with ps; [
        numpy
        pandas
        matplotlib
        scipy
      ]);
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [ tex pkgs.gnumake pkgs.ghostscript pythonEnv pkgs.uv ];
        shellHook = ''
          mkdir -p build
          # Keep uv from fetching its own interpreters; reuse the nix Python.
          export UV_PYTHON_DOWNLOADS=never
          export UV_PYTHON=${pythonEnv}/bin/python3
          echo "LaTeX $(pdflatex --version | head -1)"
          echo "Python $(python3 --version)  (uv $(uv --version 2>/dev/null | cut -d' ' -f2))"
          echo "Run: make"
        '';
      };
    };
}
