# Job Bot

Bot de automatización para búsqueda y aplicación a ofertas de empleo en LinkedIn. Busca ofertas según un perfil personalizado, las puntúa con IA (Google Gemini) y aplica automáticamente a las que superan el umbral de afinidad. Envía un resumen semanal por email con los resultados.

## Características

- **Easy Apply únicamente** — solo aplica a ofertas con el botón Easy Apply de LinkedIn. Los links externos quedan registrados en el email para revisión manual.
- **Scoring con IA** — Google Gemini analiza cada oferta contra el CV y el perfil del usuario (0-100). Solo aplica si supera el mínimo configurado.
- **Anti-detección** — delays aleatorios entre acciones, límite diario de aplicaciones, user-agent configurable.
- **Sin re-aplicaciones** — historial en SQLite por usuario.
- **Email de resumen** — notificación HTML semanal con aplicaciones enviadas, links externos pendientes y errores.
- **Escalable** — arquitectura multi-usuario y multi-plataforma (interfaz `BasePlatform`).
- **Revisión de CV (formato XYZ)** — herramienta manual (`python cv_review.py`) que sugiere reescribir viñetas de logros en formato "Logré X, medido por Y, mediante Z". Nunca inventa métricas: si el CV no trae un dato medible, lo marca como pendiente en vez de inventarlo. Genera solo un reporte para revisión manual, no modifica el CV ni sube nada a LinkedIn.

## Estructura

```
job-bot/
├── .github/workflows/job_bot.yml   # Ejecución automática cada lunes 9AM (Colombia)
├── config/settings.yaml            # Configuración global
├── users/
│   └── user_001/
│       ├── profile.yaml            # Perfil y filtros de búsqueda (committed)
│       ├── SEARCH_FILTERS.txt      # Guía para definir filtros en texto plano
│       ├── credentials.yaml        # Credenciales (gitignored — NUNCA al repo)
│       └── cv.pdf                  # Hoja de vida PDF (gitignored)
├── src/
│   ├── core/
│   │   ├── orchestrator.py         # Motor principal
│   │   ├── cv_parser.py            # Extracción de texto del PDF
│   │   └── job_matcher.py          # Scoring con Gemini
│   ├── platforms/
│   │   ├── base_platform.py        # Interfaz abstracta
│   │   └── linkedin/               # Login, búsqueda, Easy Apply
│   ├── notifier/email_notifier.py  # Email de resumen
│   └── storage/db.py               # Historial SQLite
├── main.py                         # Punto de entrada
├── ACCOUNTS.txt                    # Cuentas del proyecto (gitignored)
└── requirements.txt
```

## Setup inicial

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/jobbotsa-wq/job-bot.git
cd job-bot
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurar credenciales locales

```bash
cp users/user_001/credentials.yaml.example users/user_001/credentials.yaml
```

Editar `credentials.yaml` con:
- Email y contraseña de LinkedIn (cuenta dedicada al bot)
- Gmail App Password para notificaciones
- API Key de Gemini (gratis en [aistudio.google.com](https://aistudio.google.com))

### 3. Agregar tu CV

Coloca tu hoja de vida en `users/user_001/cv.pdf`.

### 4. Configurar tu perfil

Editar `users/user_001/profile.yaml` con tus datos, palabras clave y filtros. Puedes usar `SEARCH_FILTERS.txt` como guía.

### 5. Ejecución local

```bash
python main.py
```

### 6. (Opcional) Revisar tu CV con el formato XYZ

```bash
python cv_review.py user_001
```

Genera `users/user_001/cv_xyz_review.md` con sugerencias de reescritura de viñetas en formato XYZ (Google). No modifica tu `cv.pdf` ni sube nada a LinkedIn — es solo un reporte para que apliques manualmente lo que te sirva.

## GitHub Actions (ejecución automática semanal)

Configura estos Secrets en **GitHub > Settings > Secrets and variables > Actions**:

| Secret | Descripción |
|--------|-------------|
| `LINKEDIN_EMAIL` | Email de la cuenta LinkedIn del bot |
| `LINKEDIN_PASSWORD` | Contraseña de LinkedIn |
| `GMAIL_SENDER` | Email que envía las notificaciones |
| `GMAIL_APP_PASSWORD` | App Password de 16 caracteres |
| `GEMINI_API_KEY` | API Key de Google Gemini |
| `CV_PDF_BASE64` | CV en base64 (`[Convert]::ToBase64String([IO.File]::ReadAllBytes("cv.pdf"))` en PowerShell) |

El workflow se ejecuta automáticamente cada **lunes a las 9:00 AM (hora Colombia)** y también puede activarse manualmente desde la pestaña Actions.

## Agregar un nuevo usuario

1. Copiar la carpeta `users/user_001/` como `users/user_002/`
2. Editar `profile.yaml` con los datos del nuevo usuario
3. Agregar sus credenciales en `credentials.yaml`
4. Para CI/CD: agregar nuevos Secrets con prefijo `USER_002_*` y actualizar el workflow

## Agregar una nueva plataforma

1. Crear `src/platforms/nueva_plataforma/` implementando `BasePlatform`
2. Registrar la plataforma en `orchestrator.py`
3. Habilitar en `profile.yaml` del usuario

## Stack

- Python 3.11+
- Playwright (automatización de browser)
- Google Gemini 2.5 Flash (scoring IA — tier gratuito)
- pdfplumber (extracción de CV)
- SQLite (historial de aplicaciones)
- GitHub Actions (ejecución programada gratuita)
