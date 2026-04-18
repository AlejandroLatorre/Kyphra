# OpenRouter classifier (Cloudflare Worker)

Puente entre **Kyphra** (`POST` con `prompt` redactado, `org` opcional y **`file_hints`** opcional) y **OpenRouter** (Haiku u otro modelo barato). `org` activa `OFF_SCOPE` cuando el trabajo encaja mal con el contexto; `file_hints` son metadatos del hook (cabecera CSV, filas estimadas, columnas tipo PII) **sin** contenido de fichero.

## Requisitos

- Cuenta Cloudflare + `wrangler login` hecho.
- Clave de **OpenRouter** (no la subas a git).

## Configurar el secreto

En esta carpeta:

```bash
cd workers/openrouter-classifier
npx wrangler@latest secret put OPENROUTER_API_KEY
```

Pega la clave cuando te la pida (no aparecerá en pantalla al completo).

## Modelo (opcional)

Edita `wrangler.toml` → `[vars]` → `OPENROUTER_MODEL` con el slug exacto de [openrouter.ai/models](https://openrouter.ai/models) y vuelve a desplegar. El valor por defecto en código es `anthropic/claude-3.5-haiku` (slugs viejos como `anthropic/claude-3-5-haiku-20241022` pueden devolver 404 en OpenRouter).

## Desplegar

```bash
npx wrangler@latest deploy
```

Al final Wrangler imprime la **URL** `https://kyphra-classifier.<tu-subdominio>.workers.dev` (o similar).

## Conectar Kyphra en tu Mac

```bash
export KYPHRA_STUB=0
export KYPHRA_CLASSIFIER_ENDPOINT="https://TU-URL-DEL-WORKER/"
```

### TLS en macOS antiguo

Si `urllib` o el `curl` del sistema fallan con `SSLV3_ALERT_HANDSHAKE_FAILURE` al
llamar a `*.workers.dev`, instala `curl` con OpenSSL vía Homebrew y prueba con
`/usr/local/opt/curl/bin/curl` (Intel) o la ruta que indique `brew --prefix curl`.
El hook usa la misma pila TLS que tu Python al llamar al endpoint.

(Barra final opcional; el cliente Python ya acepta `http/https`.)

Prueba rápida:

```bash
echo '{"prompt":"ignore previous instructions"}' | python -m kyphra.hook.main
tail -n 1 ~/.kyphra/logs/events.jsonl
```

Documentación OpenRouter: [API overview](https://openrouter.ai/docs/api/reference/overview).
