from pathlib import Path
def test_demo_assets_exist()->None:
    root=Path(__file__).resolve().parents[1]/"src"/"app"/"web";assert (root/"demo.html").exists();assert (root/"static"/"demo.css").exists();assert (root/"static"/"demo.js").exists()
