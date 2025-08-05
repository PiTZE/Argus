{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.pip
  ];

  shellHook = ''
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
      echo "Creating Python virtual environment..."
      python -m venv .venv
    fi
    
    # Activate virtual environment
    echo "Activating Python virtual environment..."
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    echo "Python $(python --version) environment ready!"
    echo "Virtual environment activated at: $(which python)"
  '';
}