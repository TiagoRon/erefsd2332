# 🚀 Automatización con GitHub Actions (Gratis y Sin Tarjeta)

Esta guía te explica cómo configurar tu repositorio para que genere un video automáticamente todos los días.

## 1. Subir tu Código a GitHub

Si aún no lo has hecho, sube tu carpeta a un repositorio de GitHub (puede ser privado).

```bash
git init
git add .
git commit -m "Initial commit"
# (Sigue las instrucciones de GitHub para conectar el repo remoto)
```

## 2. Configurar las Claves Secretas (Secrets)

Para que el script funcione en la nube sin exponer tus claves, debes guardarlas en GitHub:

1.  Ve a la página de tu repositorio en GitHub.
2.  Entra en **Settings** (Configuración) > **Secrets and variables** > **Actions**.
3.  Haz clic en **New repository secret**.
4.  Agrega las siguientes claves una por una:

    | Nombre (Name) | Valor (Secret) |
    | :--- | :--- |
    | `GOOGLE_API_KEY` | *Tu clave de Google AI (Gemini)* |
    | `PEXELS_API_KEY` | *Tu clave de Pexels* |

## 3. ¡Listo! ¿Cómo Funciona?

*   **Automático:** El script se ejecutará todos los días a las **10:00 AM (Hora Argentina/Brasil)**.
*   **Manual:** Puedes ir a la pestaña **Actions** en GitHub, seleccionar "Daily AutoShorts Generator" y darle al botón **Run workflow** para probarlo ahora mismo.

## 4. ¿Dónde están mis videos?

Cuando el proceso termine (tarda unos 2-5 minutos):
1.  Ve a la pestaña **Actions**.
2.  Entra en la ejecución más reciente (tendrá un check verde ✅).
3.  Baja hasta la sección **Artifacts**.
4.  Descarga el archivo `daily-shorts.zip`. ¡Ahí está tu video mp4!
