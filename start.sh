set -eu

export PYTHONUNBUFFERED=true
VIRTUALENV=.data/venv

# Buat virtual environment jika belum ada
if [ ! -d $VIRTUALENV ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VIRTUALENV
fi

# Pastikan pip sudah tersedia
if [ ! -f $VIRTUALENV/bin/pip ]; then
    curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | $VIRTUALENV/bin/python3
fi

# Instal dependensi dari requirements.txt
echo "Installing dependencies..."
$VIRTUALENV/bin/pip install -r requirements.txt

# Jalankan aplikasi
if [ -f app.py ]; then
    echo "Starting Flask app..."
    $VIRTUALENV/bin/python3 app.py
else
    echo "Error: app.py not found in the project root!"
    exit 1
fi
