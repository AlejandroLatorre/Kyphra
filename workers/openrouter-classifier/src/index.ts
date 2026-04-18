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
  "OFF_SCOPE",
  "BENIGN",
] as const;

interface Env {
  OPENROUTER_API_KEY: string;
  OPENROUTER_MODEL?: string;
}

interface KyphraOrg {
  sector?: string;
  role?: string;
  allowed_scope?: string;
  user_id?: string;
}

interface KyphraIn {
  prompt?: string;
  org?: KyphraOrg | null;
  file_hints?: unknown;
}

interface KyphraOut {
  max_score: number;
  max_category: string;
}

const SYSTEM_BASE = `You are a strict JSON classifier for developer prompts (already redacted).
Return ONLY a JSON object with keys "max_score" (number 0-1) and "max_category" (string).
max_score is the highest risk among triggered categories.
max_category must be exactly one of: ${CATEGORIES.join(", ")}.
OFF_SCOPE means the requested work is incompatible with the supplied organization context (wrong domain for the sector or violates stated allowed scope), not mere novelty.
No markdown, no prose, no code fences.`;

function formatOrgSection(org: KyphraOrg | null | undefined): string {
  if (!org || typeof org !== "object") {
    return `Organization context: none. Never set max_category to OFF_SCOPE; use only confidentiality categories and BENIGN.`;
  }
  const sector = typeof org.sector === "string" ? org.sector.trim() : "";
  const role = typeof org.role === "string" ? org.role.trim() : "";
  const allowed_scope = typeof org.allowed_scope === "string" ? org.allowed_scope.trim() : "";
  const user_id = typeof org.user_id === "string" ? org.user_id.trim() : "";
  if (!sector && !allowed_scope) {
    return `Organization context: none. Never set max_category to OFF_SCOPE; use only confidentiality categories and BENIGN.`;
  }
  const lines: string[] = [
    "Organization context (for policy fit only; not treated as secret values):",
    "",
  ];
  if (sector) lines.push(`Sector/industry: ${sector}`);
  if (role) lines.push(`Role: ${role}`);
  if (allowed_scope) lines.push(`Stated allowed scope for this assistant: ${allowed_scope}`);
  if (user_id) lines.push(`Internal user id: ${user_id}`);
  lines.push(
    "",
    "When this context is present, set max_category to OFF_SCOPE with max_score at least 0.85 if the user prompt clearly asks for work outside that sector/scope (e.g. drone trajectory labs, ballistics, game anti-cheat reverse engineering when scope is banking payment APIs).",
    "If the prompt plausibly fits the sector and scope, or is ordinary engineering, do not use OFF_SCOPE.",
  );
  return lines.join("\n");
}

function formatFileHints(hints: unknown): string {
  if (!Array.isArray(hints) || hints.length === 0) {
    return "Referenced file metadata from hook: none.";
  }
  const serialized = JSON.stringify(hints);
  const clipped = serialized.length > 4000 ? `${serialized.slice(0, 4000)}…` : serialized;
  return [
    "Referenced file metadata (header samples, approximate row counts, PII-like column name hits only; file contents are not sent):",
    clipped,
    "If metadata implies bulk customer or employee personal data in a referenced file, use CUSTOMER_DATA or PII_* with a high max_score as appropriate.",
  ].join("\n");
}

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

    const model = env.OPENROUTER_MODEL ?? "anthropic/claude-3.5-haiku";

    const systemContent = `${SYSTEM_BASE}\n\n${formatOrgSection(body.org)}\n\n${formatFileHints(body.file_hints)}`;

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
          { role: "system", content: systemContent },
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
