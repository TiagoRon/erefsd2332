# AutoShorts Generator AI 🚀

Generador automático de YouTube Shorts en español, potenciado por Inteligencia Artificial.

## Características
- **Guiones con IA**: Usa Google Gemini para escribir guiones virales de curiosidades, misterio, hechos, etc.
- **Narración Natural**: Usa "Edge TTS" para voces neuronales ultra realistas en español.
- **Edición Automática**: Sincroniza audio, subtítulos animados y música de fondo.
- **Fondos Inteligentes**: Genera animaciones (loop) únicas basadas en el tema del guion (Misterio/Ciencia/Peligro/etc).
- **Interfaz Gráfica**: GUI simple para generar videos con un clic.

## Requisitos
- Python 3.9 o superior (Recomendado 3.9 por compatibilidad de video, pero funciona en 3.13 con ajustes incluidos).
- FFmpeg instalado en el sistema.
- Una API Key de Google Gemini (Gratis).

## Instalación

1. Clona o descarga este repositorio.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Configura tu API Key:
   - Renombra `.env.example` a `.env`.
   - Abre el archivo y pega tu clave: `GOOGLE_API_KEY=tu_clave_aqui`.

## Cómo Usar

### Opción 1: Interfaz Gráfica (Recomendado)
Ejecuta el archivo `gui.py`:
```bash
python gui.py
```
1. Ingresa la cantidad de videos.
2. Pulsa "GENERAR".
3. Mira el progreso y espera a que termine.

### Opción 2: Línea de Comandos
```bash
python main.py
```

## Solución de Problemas
- **Error "Quota exceeded"**: Estás usanda la versión gratuita de Gemini y has hecho muchas peticiones rápido. El programa esperará automáticamente y reintentará.
- **Error de Video/Imágenes**: Asegúrate de tener FFmpeg instalado y agregado al PATH de Windows.

## Salida
Los videos se guardan en la carpeta `output/`, organizados por título.
