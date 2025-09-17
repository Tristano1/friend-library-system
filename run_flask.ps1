# Activate virtual environment
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    . $venvPath
} else {
    Write-Host "Virtual environment not found. Creating..."
    python -m venv venv
    . .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
}

# Set Flask environment variables
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Run Flask on port 8080
flask run --port=8080
