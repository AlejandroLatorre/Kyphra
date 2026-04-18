# Inicio Cursor — primer sprint (Semana 1-2: Hook + classifier core)

Dos partes: primero **tú** preparas el entorno en el portátil personal, después **Cursor** empieza a programar con el prompt de abajo.

---

## 1. Setup en el portátil personal (lo haces tú, una sola vez)

Abre una terminal (Git Bash o PowerShell) en la carpeta donde quieras tener el proyecto y ejecuta:

```bash
git clone https://github.com/AlejandroLatorre/Kyphra.git
cd Kyphra
git config user.email latorreotero@gmail.com
git config user.name AlejandroLatorre
python -m venv .venv
source .venv/Scripts/activate   # en PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
mypy kyphra
ruff check .
```

**Si los tres últimos comandos (`pytest`, `mypy`, `ruff`) pasan en verde, el entorno está listo.**
Si alguno falla, párate y arréglalo antes de abrir Cursor.

---

## 2. Primer prompt para Cursor

Abre la carpeta `Kyphra` en Cursor y pega este prompt en el chat tal cual:

---

Lee `CLAUDE.md`, `SECURITY.md`, `TAXONOMY.md` y `ROADMAP.md` antes de tocar código. Seguimos la Semana 1-2 del roadmap: **Hook + classifier core (MVP)**.

Primer entregable, en este orden exacto y en commits separados:

1. `kyphra/taxonomy/categories.py` — enum `Category` con las 9 categorías de `TAXONOMY.md` y enum `Level` (`ALLOW`, `AVISO`, `ALERTA`). Tests: cada categoría tiene un level por defecto correcto.
2. `kyphra/hook/secrets.py` — detector de secretos por regex (API keys, tokens, private keys, connection strings). Función `find_secrets(text: str) -> list[SecretMatch]` con tipos estrictos. Tests con fixtures sintéticos (`sk-ant-***`, `sk-proj-***`, etc., **nunca claves reales**).
3. `kyphra/hook/redactor.py` — `redact(text: str) -> RedactedPrompt` que tokeniza secretos a `<SECRET_{tipo}_{preview10}***>` y PII básica (email, DNI, IBAN) a `<PII_{tipo}>`. Invariante test: `redact(redact(x)) == redact(x)` (idempotencia).

Reglas no negociables:

- `mypy --strict` tiene que pasar en cada commit.
- Ningún test con claves reales. Usa placeholders como en `tests/golden_set.jsonl`.
- Nada de clasificador ni Haiku todavía. Esto es la capa local pura.
- Para al terminar cada paso y resume qué cambió antes de seguir al siguiente.

No toques `kyphra/hook/main.py`, `kyphra/hook/classifier.py`, ni `kyphra/cli/audit.py` en esta iteración — ya vendrán.

---

## 3. Cuando Cursor termine

- Ejecuta `pytest`, `mypy kyphra` y `ruff check .` localmente antes de hacer push.
- Commits pequeños y en inglés, imperativo (`add category enum`, `add secrets detector`, `add redactor`).
- Push a `main` cuando los tres pasos estén verdes.
- Vuelve aquí para el siguiente prompt (classifier + hook main + logger).
