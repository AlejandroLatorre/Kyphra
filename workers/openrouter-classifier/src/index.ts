/**
 * Kyphra classifier edge: Kyphra POST body -> OpenRouter -> { max_score, max_category }.
 * OPENROUTER_API_KEY must be set as a Worker secret.
 */
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

const CATEGORIES = [
  "PII_PERSONAL",
  "PII_SENSITIVE",
  "SECRETS",
  "PROPRIETARY_CODE",
  "CUSTOMER_DATA",
  "FINANCIAL_DATA",
  "STRATEGIC",
  "PROMPT_INJECTION",
  "BENIGN",
] as const;

interface Env {
  OPENROUTER_API_KEY: string;
  OPENROUTER_MODEL?: string;
}

interface KyphraIn {
  prompt?: string;
}

interface KyphraOut {
  max_score: number;
  max_category: string;
}

const SYSTEM = `You are a strict JSON classifier for developer prompts (already redacted).
Return ONLY a JSON object with keys "max_score" (number 0-1) and "max_category" (string).
max_score is the highest risk among triggered categories.
max_category must be exactly one of: ${CATEGORIES.join(", ")}.
No markdown, no prose, no code fences.`;

function parseModelJson(text: string): KyphraOut | null {
  const trimmed = text.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "");
  const parsed = JSON.parse(trimmed) as unknown;
  if (!parsed || typeof parsed !== "object") return null;
  const o = parsed as Record<string, unknown>;
  if (typeof o.max_score !== "number" || typeof o.max_category !== "string") return null;
  if (!CATEGORIES.includes(o.max_category as (typeof CATEGORIES)[number])) return null;
  if (o.max_score < 0 || o.max_score > 1) return null;
  return { max_score: o.max_score, max_category: o.max_category };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }
    if (request.method !== "POST") {
      return new Response("method not allowed", { status: 405 });
    }

    const key = env.OPENROUTER_API_KEY;
    if (!key) {
      return new Response(JSON.stringify({ error: "OPENROUTER_API_KEY missing" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }

    let body: KyphraIn;
    try {
      body = (await request.json()) as KyphraIn;
    } catch {
      return new Response(JSON.stringify({ error: "invalid json" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (typeof body.prompt !== "string") {
      return new Response(JSON.stringify({ error: "missing prompt" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const model = env.OPENROUTER_MODEL ?? "anthropic/claude-3-5-haiku-20241022";

    const orRes = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/AlejandroLatorre/Kyphra",
        "X-OpenRouter-Title": "Kyphra classifier",
      },
      body: JSON.stringify({
        model,
        max_tokens: 256,
        temperature: 0,
        response_format: { type: "json_object" },
        messages: [
          { role: "system", content: SYSTEM },
          { role: "user", content: body.prompt },
        ],
      }),
    });

    if (!orRes.ok) {
      const errText = await orRes.text();
      return new Response(JSON.stringify({ error: "openrouter error", detail: errText.slice(0, 500) }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }

    const orJson = (await orRes.json()) as {
      choices?: Array<{ message?: { content?: string | null } }>;
    };
    const content = orJson.choices?.[0]?.message?.content;
    if (typeof content !== "string" || !content.trim()) {
      return new Response(JSON.stringify({ error: "empty model response" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }

    let out: KyphraOut | null = null;
    try {
      out = parseModelJson(content);
    } catch {
      out = null;
    }
    if (!out) {
      return new Response(JSON.stringify({ error: "invalid classifier json", raw: content.slice(0, 800) }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify(out), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  },
};
