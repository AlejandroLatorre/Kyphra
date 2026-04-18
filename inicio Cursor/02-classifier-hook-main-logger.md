# Inicio Cursor — sprint 2 (Semana 1–2: classifier + hook main + logger)

Lee `CLAUDE.md`, `SECURITY.md`, `TAXONOMY.md` y `ROADMAP.md` (semana 1–2) antes de tocar código.

Ya existen `kyphra.taxonomy.categories`, `kyphra.hook.secrets` y `kyphra.hook.redactor` — no los reescribas salvo un bug claro.

Implementa el resto del MVP local de la semana 1–2, en **commits pequeños en inglés** (imperativo), con `mypy --strict`, `pytest` y `ruff check .` en verde antes de cada push.

## Orden sugerido (commits separados)

1. **`kyphra/hook/classifier.py`** — Modo stub (default con env `KYPHRA_STUB=1` o equivalente documentado): clasificación determinista mínima que devuelva categorías alineadas con `Category` y scores plausibles. Modo API: cliente que llama a un endpoint configurable (URL por env) con **solo texto ya redactado**; timeout duro **2 s**; en timeout resultado explícito `UNKNOWN_TIMEOUT` (no confundir con BENIGN). Tests con cliente HTTP mockeado; sin llamadas reales a Anthropic en CI.

2. **`kyphra/hook/logger.py`** — Append-only JSONL local; **nunca** escribir prompt crudo; solo redactado. Niveles: ALLOW resumido, AVISO/ALERTA con detalle permitido por `SECURITY.md` / `CLAUDE.md`. ALERTA: archivo o registro cifrado con **AES-GCM** según lo descrito en `CLAUDE.md` (PBKDF2, iteraciones, salt). Tests con temporales y claves de prueba sintéticas.

3. **`kyphra/hook/main.py`** — Entrada **stdin JSON** compatible con el hook `UserPromptSubmit` de Claude Code: parseo robusto, pipeline redact → classify → log; short-circuit si `find_secrets` detecta riesgo alto según criterio ya definido en el repo; **siempre `sys.exit(0)`** en todos los caminos (errores a stderr, sin excepción no capturada hacia afuera). Tests de integración livianos o prueba de módulo con stdin simulado.

4. **(Si cabe en el mismo sprint)** **`kyphra/taxonomy/system_prompt.py`** — texto mínimo versionable + test de que existe y longitud razonable; sin enviarlo a runtime desde el cliente si contradice `SECURITY.md` T5.

## Invariantes (tests donde aplique)

- No prompt crudo a disco ni al cliente HTTP del clasificador.
- Hook: **exit code 0** siempre.

## Fuera de este sprint

- No implementes aún `kyphra/cli/audit.py` ni dashboard / Worker salvo que el roadmap lo marque explícito para esta iteración.

## Al terminar cada bloque

Resume qué cambió antes del siguiente commit grande.

## Antes de push

```bash
pytest
mypy kyphra
ruff check .
```

Push a `main` cuando todo esté verde.
