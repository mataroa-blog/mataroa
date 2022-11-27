with (import <nixpkgs> {});
mkShell {
  buildInputs = [
    postgresql_12
  ];
}
