# WishList Flask App

Simple Flask app that loads `WishList.json` and displays it as an HTML table.

Quick start (Windows / PowerShell):

1. Create a virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install requirements:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
python main.py
```

Open http://127.0.0.1:5000/ to view the table.

API endpoint: `/api/wishlist` returns the JSON array.
