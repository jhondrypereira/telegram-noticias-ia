# Noticias IA · Canal de Telegram 100% automático

Publica en tu canal de Telegram noticias de **IA, tecnología y buenas noticias** de portales reconocidos, cada 30 minutos, sin servidor y sin tu PC encendida (corre en **GitHub Actions**, gratis).

- Traduce titular + resumen al **español**, con enlace al artículo **original**.
- Publica con **imagen** (si la hay) o solo texto.
- No repite noticias (guarda el estado en `posted.json`).
- Evita noticias negativas (lista `BLOCK` en `feeds.py`).

## Puesta en marcha (una sola vez, ~10 min)

### 1) Crea el canal
- En Telegram: **Nuevo canal** → nombre y descripción → hazlo **Público** y ponle un **@usuario** (ej. `@NoticiasIA_mundo`). Ese `@usuario` es tu `CHANNEL_ID`.

### 2) Crea el bot y agrégalo como admin
- En **@BotFather** → `/newbot` → copia el **token**.
- En tu canal → **Administradores** → **Agregar admin** → busca tu bot → dale permiso de **Publicar mensajes**.

### 3) Sube este proyecto a GitHub
- Crea un repo (recomendado **público**: los minutos de Actions son gratis e ilimitados).
- Sube estos archivos (el token NO va en el código, va en “Secrets”).

### 4) Pon los secretos en GitHub
Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:
- `BOT_TOKEN` = el token de tu bot
- `CHANNEL_ID` = `@tuusuario` (o el ID numérico si el canal es privado)

### 5) ¡Listo!
- Repo → pestaña **Actions** → workflow **“Noticias IA (auto)”** → **Run workflow** para probar ya.
- A partir de ahí publica **solo cada 30 min**.

## Ajustes fáciles
- **Fuentes**: edita `feeds.py` (agrega/quita portales).
- **Frecuencia**: cambia el `cron` en `.github/workflows/noticias.yml` (`*/30` = 30 min; `*/15` = 15 min).
- **Cantidad por tanda**: `MAX_PER_RUN` en el workflow (por defecto 6).
- **Filtro positivo/limpio**: lista `BLOCK` en `feeds.py`.
- **Solo ciertos temas**: rellena `REQUIRE_ANY` en `feeds.py` (ej. `["ia","tecnolog","robot"]`).

## Probar en tu PC (opcional)
```bash
pip install -r requirements.txt
set BOT_TOKEN=xxxxx   &&  set CHANNEL_ID=@tuusuario   &&  python bot.py   # Windows CMD
```
