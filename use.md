1. Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
2. py -3.13 -m venv .venv
3. .\.venv\Scripts\Activate.ps1
4. pip install torch --extra-index-url https://download.pytorch.org/whl/cu128

(--default-timeout=1000)