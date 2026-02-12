import os
import requests

def download_font():
    font_dir = os.path.join("assets", "fonts")
    os.makedirs(font_dir, exist_ok=True)
    
    font_url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-ExtraBold.ttf"
    output_path = os.path.join(font_dir, "Montserrat-ExtraBold.ttf")
    
    if os.path.exists(output_path):
        print(f"✅ Font already exists at: {output_path}")
        return

    print(f"⬇️ Downloading font from {font_url}...")
    try:
        response = requests.get(font_url)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Font saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error downloading font: {e}")

if __name__ == "__main__":
    download_font()
