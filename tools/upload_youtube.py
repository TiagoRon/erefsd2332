import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# CONFIGURATION
# ----------------
# ⚠️ CAMBIA ESTO CON TU RUTA DE PERFIL DE CHROME/BRAVE
# Default: Try to guess standard Chrome path
# Para Chrome: C:\Users\TU_USUARIO\AppData\Local\Google\Chrome\User Data
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Google", "Chrome", "User Data")
PROFILE_DIR = "Default" # O "Profile 1", "Profile 2", etc.

def get_videos_to_upload(source_dir):
    videos = []
    # Recursively find .mp4 files and associated metadata
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".mp4"):
                vid_path = os.path.join(root, file)
                meta_path = os.path.join(root, "metadata.txt")
                
                title = "Video Automático #Shorts"
                desc = "Suscríbete para más curiosidades! #shorts"
                
                if os.path.exists(meta_path):
                    with open(meta_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith("Título:"):
                                title = line.replace("Título:", "").strip()
                            if line.startswith("Hashtags:"):
                                desc += "\n" + line.replace("Hashtags:", "").strip()
                
                videos.append({
                    "path": os.path.abspath(vid_path),
                    "title": title[:100], # YouTube Title Limit
                    "description": desc
                })
    return videos

def upload_video(driver, video):
    print(f"🎬 Subiendo: {video['title']}")
    
    driver.get("https://studio.youtube.com")
    time.sleep(3)
    
    # 1. Click Create -> Upload Video
    try:
        create_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "create-icon"))
        )
        create_btn.click()
        
        upload_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//ytcp-text-menu-item[.//div[text()='Upload videos']]"))
        )
        upload_btn.click()
    except Exception as e:
        print("⚠️ No se pudo iniciar subida. ¿Estás logueado?")
        return False

    # 2. Send File
    time.sleep(2)
    file_input = driver.find_element(By.XPATH, "//input[@type='file']")
    file_input.send_keys(video['path'])
    
    # 3. Fill Details (Wait for upload processing)
    # This part is tricky because YouTube changes IDs frequently.
    # Basically we wait until the title box appears.
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "textbox"))
        )
        print("✨ Archivo cargado. Llenando detalles...")
        
        # Title (Defaults to filename, we assume good enough or edit manually)
        # Description is clearer relative to ID 'description-textarea'
        
        # Click Next (Kids content check often required)
        # Assuming channel default is "Not for kids"
        
        # Click Next x3 to Visibility
        for i in range(3):
            next_btn = driver.find_element(By.ID, "next-button")
            next_btn.click()
            time.sleep(2)
            
        # Select "Public" or "Unlisted"
        # privacy_radios = driver.find_elements(By.NAME, "privacy-radios")
        # privacy_radios[2].click() # Public usually
        
        # Click Publish
        # publish_btn = driver.find_element(By.ID, "done-button")
        # publish_btn.click()
        
        print("✅ ¡Video subido! (O casi, revisa la ventana del navegador)")
        time.sleep(5)
        
    except Exception as e:
         print(f"❌ Error en el flujo de subida: {e}")
         return False

    return True

def main():
    print("🚀 Iniciando Uploader Automático...")
    
    # Setup Browser
    chrome_options = Options()
    # Point to user profile to reuse login!
    chrome_options.add_argument(f"user-data-dir={USER_DATA_DIR}")
    chrome_options.add_argument(f"profile-directory={PROFILE_DIR}")
    chrome_options.add_argument("--start-maximized")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"❌ Error al abrir Chrome: {e}")
        print("💡 CONSEJO: Cierra todas las ventanas de Chrome antes de ejecutar esto.")
        return

    # Find Videos
    # You would download the ZIPs to a folder like "downloads_from_github"
    source_folder = "downloads_from_github" 
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)
        print(f"⚠️ Carpeta '{source_folder}' creada. Pon tus videos descomprimidos ahí y vuelve a ejecutar.")
        return

    videos = get_videos_to_upload(source_folder)
    
    if not videos:
        print("⚠️ No encontré videos .mp4 en la carpeta.")
        return
        
    print(f"📜 Encontrados {len(videos)} videos para subir.")
    
    for vid in videos:
        upload_video(driver, vid)
        input("⏸️ Presiona Enter para subir el siguiente (Revisa que el anterior terminó)...")

if __name__ == "__main__":
    main()
