{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

  outputs = { self, nixpkgs, poetry2nix }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});
      customOverrides = 
          (final: prev: {
            argparse = prev.argparse.overridePythonAttrs
            (
              old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ prev.setuptools ];
              }
            );
          });
    in
    {
      packages = forAllSystems (system: let
        inherit (poetry2nix.lib.mkPoetry2Nix { pkgs = pkgs.${system}; }) mkPoetryApplication defaultPoetryOverrides;
      in {
        default = mkPoetryApplication { 
          projectDir = self; 
          # preferWheels = true;
          overrides = defaultPoetryOverrides.extend customOverrides;
        };
      });

      devShells = forAllSystems (system: let
        inherit (poetry2nix.lib.mkPoetry2Nix { pkgs = pkgs.${system}; }) mkPoetryEnv defaultPoetryOverrides;
      in {
        default = pkgs.${system}.mkShellNoCC {
          packages = with pkgs.${system}; [
            (mkPoetryEnv { 
              projectDir = self; 
              overrides = defaultPoetryOverrides.extend customOverrides;
            })
            poetry
          ];
        };
      });
    };
}
