{
  description = "Thesis LaTeX build environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      tex = pkgs.texlive.combined.scheme-full;
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [ tex pkgs.gnumake pkgs.ghostscript ];
        shellHook = ''
          mkdir -p build
          echo "LaTeX $(pdflatex --version | head -1)"
          echo "Run: make"
        '';
      };
    };
}
