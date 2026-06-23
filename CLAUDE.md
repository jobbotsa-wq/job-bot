# Job Bot — Contexto para Claude

Bot de automatización de búsqueda y aplicación a empleos en LinkedIn. Uso personal inicial, escalable a múltiples usuarios y plataformas.

## Reglas de Git (OBLIGATORIO)

- Rama principal: `master`
- Repositorio: `https://github.com/jobbotsa-wq/job-bot`
- **Después de CADA cambio:** hacer commit + push a `master` inmediatamente
- No acumular cambios — un commit por tarea o modificación concreta
- Formato de mensaje: `tipo: descripción breve en español` (feat, fix, docs, chore)

## Stack

- Python 3.11+, sin frameworks web
- Playwright (sync API) — headless Chromium para automatización de LinkedIn
- Google Gemini 1.5 Flash (`google-generativeai`) — scoring de afinidad oferta/perfil (tier gratuito: 15 req/min, 1500 req/día)
- pdfplumber — extracción de texto de CV en PDF
- SQLite (stdlib `sqlite3`) — historial de aplicaciones por usuario
- PyYAML — lectura de configuración y perfiles
- smtplib (stdlib) — email de resumen vía Gmail SMTP SSL
- GitHub Actions — ejecución programada (cron lunes 9AM Colombia = `0 14 * * 1` UTC)

## Arquitectura de archivos

```
job-bot/
├── .github/workflows/job_bot.yml
├── config/settings.yaml              # config global (delays, límites, AI)
├── users/
│   └── user_001/
│       ├── profile.yaml              # perfil y filtros (COMMITTED)
│       ├── SEARCH_FILTERS.txt        # guía de filtros en texto plano
│       ├── credentials.yaml          # credenciales (GITIGNORED)
│       └── cv/cv.pdf                 # hoja de vida (GITIGNORED)
├── src/
│   ├── core/
│   │   ├── orchestrator.py           # itera usuarios → plataformas → aplica
│   │   ├── cv_parser.py              # extrae texto del PDF con pdfplumber
│   │   └── job_matcher.py            # scoring 0-100 con Gemini
│   ├── platforms/
│   │   ├── base_platform.py          # ABC con login/search_jobs/apply/close
│   │   └── linkedin/
│   │       ├── __init__.py
│   │       ├── login.py
│   │       ├── job_search.py         # build_search_url, extract_jobs_from_page, get_job_description
│   │       └── easy_apply.py
│   ├── notifier/email_notifier.py    # HTML email con resumen (aplicadas, externas, errores)
│   └── storage/db.py                 # init_db, already_applied, save_application, get_applications
├── main.py                           # python main.py → run_all_users()
├── ACCOUNTS.txt                      # cuentas del proyecto (GITIGNORED)
├── requirements.txt
├── README.md
└── .gitignore
```

## Archivos NUNCA en el repo (en .gitignore)

- `users/*/credentials.yaml` — LinkedIn password, Gmail App Password, Gemini key
- `users/*/cv/*.pdf` — HV/CV del usuario
- `ACCOUNTS.txt` — resumen de todas las cuentas
- `data/*.db` — base de datos SQLite local

## Flujo principal (orchestrator.py)

```
run_all_users()
  └── por cada carpeta en users/
      run_for_user(user_dir, global_config)
        1. Cargar profile.yaml + credentials.yaml
        2. Extraer texto del CV (pdfplumber)
        3. Inicializar Gemini + SQLite DB
        4. Abrir Playwright browser (headless Chromium)
        5. LinkedIn login
        6. search_jobs() → lista de ofertas (Easy Apply filter activo en URL)
        7. Por cada oferta:
           a. Verificar already_applied() en SQLite
           b. get_job_description() → texto completo
           c. score_job() con Gemini → score 0-100
           d. Si score >= min_score: apply_easy_apply()
           e. save_application() con status
           f. delay aleatorio 10-20s entre aplicaciones
        8. send_summary_email() con resultados
```

## Seguridad LinkedIn / anti-bot

- Delays aleatorios entre acciones: 2-5s, entre aplicaciones: 10-20s
- Max 15 aplicaciones por ejecución (configurable en settings.yaml)
- headless=True en producción (GitHub Actions)
- Easy Apply ÚNICO — las ofertas con link externo se logean como `skipped_external`, no se aplica
- Cuenta LinkedIn dedicada (no cuenta personal)

## Secrets de GitHub Actions

| Secret | Uso |
|--------|-----|
| `LINKEDIN_EMAIL` | login.py |
| `LINKEDIN_PASSWORD` | login.py |
| `GMAIL_SENDER` | email_notifier.py |
| `GMAIL_APP_PASSWORD` | email_notifier.py |
| `GEMINI_API_KEY` | job_matcher.py |
| `CV_PDF_BASE64` | decodificado en el workflow → users/user_001/cv.pdf |

## Configuración por usuario

`profile.yaml` define:
- `personal.name`, `email_notifications`, `cv_path`, `linkedin_profile_url`
- `search.keywords` — lista bilingüe (ES + EN), se itera máx 3 por ejecución
- `search.modality` — `remote` | `hybrid` | `onsite`
- `search.locations` — para modalidades no 100% remotas
- `filters.min_match_score` — sobreescribe el global
- `filters.max_applications_per_run` — sobreescribe el global
- `platforms.linkedin.enabled` — bool

## Convenciones clave

- `score_job()` retorna `{"score": int, "reason": str, "apply": bool}` — siempre parsear con regex para extraer el JSON por si Gemini agrega texto extra
- `save_application(conn, job, status)` — status values: `"applied"`, `"skipped_score"`, `"skipped_external"`, `"error"`
- `already_applied()` chequea por `job_id` único (`"linkedin_{job_id}"`) para evitar re-aplicaciones entre ejecuciones
- El workflow limpia `credentials.yaml` y `cv.pdf` con `rm -f` en el paso `if: always()` al final

## Al agregar una nueva plataforma

1. Crear `src/platforms/nueva/` con clase que extiende `BasePlatform`
2. Implementar `login()`, `search_jobs()`, `apply()`, `close()`
3. Registrar en `orchestrator.py` dentro del loop de plataformas
4. Agregar `enabled: true/false` en `profile.yaml` bajo `platforms`
5. Agregar sus secrets en el workflow

## Al agregar un nuevo usuario

1. Copiar `users/user_001/` → `users/user_002/`
2. Editar `profile.yaml` y `credentials.yaml`
3. En GitHub Actions: agregar secrets con prefijo `USER_002_*` y step adicional en el workflow

## Qué actualizar en este archivo

- Nuevas plataformas soportadas
- Nuevos campos en profile.yaml o credentials.yaml
- Cambios en el flujo del orchestrator
- Nuevas dependencias en requirements.txt
