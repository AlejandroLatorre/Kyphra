# Probar Kyphra con Claude Code (UserPromptSubmit)

No hace falta abrir puertos: el hook es un **comando** que Claude Code ejecuta y le pasa el JSON por **stdin**.

## 1. Probar en terminal (sin Claude)

Desde la raíz del repo, con el venv activado o `pip install -e ".[dev]"`:

```bash
echo '{"hook_event_name":"UserPromptSubmit","session_id":"test","cwd":"'$(pwd)'","prompt":"hello"}' | python -m kyphra.hook.main
```

Debe terminar sin error (`echo $?` → `0`). Los eventos van a `~/.kyphra/logs/events.jsonl` salvo que definas `KYPHRA_HOME`.

## 2. Registrar el hook en Claude Code

1. Instala o abre **Claude Code** en tu Mac (aplicación o CLI; no se puede abrir desde Cursor por ti).
2. Edita el fichero de ajustes de Claude Code, por ejemplo **`~/.claude/settings.json`** (si no existe, créalo con `{}` y añade la clave `hooks`).
3. Añade un handler `UserPromptSubmit` que apunte al script del repo (ajusta la ruta a **tu** carpeta Kyphra):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/Users/alejandrolatorreotero/Desktop/Kyphra/scripts/kyphra-claude-hook.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

4. Dale permiso de ejecución al script (una vez):

```bash
chmod +x /Users/alejandrolatorreotero/Desktop/Kyphra/scripts/kyphra-claude-hook.sh
```

5. Reinicia Claude Code. En el chat de Claude Code puedes usar **`/hooks`** para ver que el hook está cargado (según [documentación de hooks](https://code.claude.com/docs/en/hooks)).

## 3. Variables útiles

| Variable | Uso |
|----------|-----|
| `KYPHRA_HOME` | Dónde guardar `logs/` (por defecto `~/.kyphra`) |
| `KYPHRA_STUB=1` | Clasificador local sin llamar al Worker (recomendado hasta tener endpoint) |
| `KYPHRA_ADMIN_PASSWORD` | Si está definida, las líneas ALERTA también se añaden cifradas a `logs/alerta.enc.jsonl` |
| `KYPHRA_PBKDF2_ITERATIONS` | Solo pruebas: bajar iteraciones PBKDF2 (en producción no lo uses) |

## 4. Comportamiento esperado

- El proceso **siempre** termina con código **0** (no bloquea el flujo).
- **AVISO** / **ALERTA**: mensajes breves en **stderr** (en Claude Code pueden verse en el log de depuración del hook).
- Nunca se escribe el **prompt crudo** en disco, solo la versión **redactada**.

Documentación del evento `UserPromptSubmit`: [Hooks reference](https://code.claude.com/docs/en/hooks#userpromptsubmit).
