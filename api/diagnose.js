// api/diagnose.js — secure, vision-capable proxy for the Garden Ops "Diagnose" tool.
//
// NOTE: DeepSeek's public API is TEXT-ONLY (no image input), so it can't do photo
// diagnosis. This proxy uses a vision model instead, chosen by whichever API key you
// set in Vercel → Settings → Environment Variables (the key never reaches the browser):
//
//   GEMINI_API_KEY      → Google Gemini (recommended: cheapest, has a free tier)
//   OPENAI_API_KEY      → OpenAI (gpt-4o-mini)
//   ANTHROPIC_API_KEY   → Anthropic Claude
//
// Optional overrides: GEMINI_MODEL / OPENAI_MODEL / ANTHROPIC_MODEL, and ALLOWED_ORIGIN
// (set to your site URL to stop other sites from using your endpoint).
//
// Runs on Vercel's Node.js runtime (global fetch is available).

const SYSTEM_PROMPT =
  "You are an expert horticulturist and IPM (integrated pest management) advisor. " +
  "Examine the plant photo and reply in plain language, brief and specific:\n" +
  "1. PLANT ID — best guess; if unsure, list the top 2-3 candidates and the feature to check.\n" +
  "2. DIAGNOSIS — pest, disease, nutrient deficiency, water stress, or environmental. Name it if you can; say if you can't tell.\n" +
  "3. TREATMENT — an IPM-first ladder: start with the least-toxic control (hand-pick, water blast, row cover, " +
  "insecticidal soap, BTK, iron phosphate) and escalate to spinosad or pyrethrin only as a last resort. " +
  "Note pollinator safety and any pre-harvest interval for edibles.\n" +
  "4. PREVENTION — one or two practical tips.\n" +
  "If the image is not a plant, say so.";

function setCors(res, req) {
  const allowed = process.env.ALLOWED_ORIGIN;
  res.setHeader('Access-Control-Allow-Origin', allowed || (req.headers.origin || '*'));
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'content-type');
}

async function callGemini(key, mime, b64, text) {
  const model = process.env.GEMINI_MODEL || 'gemini-flash-latest';
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model +
    ':generateContent?key=' + encodeURIComponent(key);
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: text }, { inline_data: { mime_type: mime, data: b64 } }] }]
    })
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j.error && j.error.message) || ('Gemini HTTP ' + r.status));
  const c = j.candidates && j.candidates[0];
  return ((c && c.content && c.content.parts) || []).map(p => p.text || '').join('\n').trim();
}

async function callOpenAI(key, mime, b64, text) {
  const model = process.env.OPENAI_MODEL || 'gpt-4o-mini';
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: model, max_tokens: 1200,
      messages: [{ role: 'user', content: [
        { type: 'text', text: text },
        { type: 'image_url', image_url: { url: 'data:' + mime + ';base64,' + b64 } }
      ] }]
    })
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j.error && j.error.message) || ('OpenAI HTTP ' + r.status));
  return ((j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || '').trim();
}

async function callAnthropic(key, mime, b64, text) {
  const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-6';
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: model, max_tokens: 1200,
      messages: [{ role: 'user', content: [
        { type: 'image', source: { type: 'base64', media_type: mime, data: b64 } },
        { type: 'text', text: text }
      ] }]
    })
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j.error && j.error.message) || ('Anthropic HTTP ' + r.status));
  return (j.content || []).map(c => c.text || '').join('\n').trim();
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') { setCors(res, req); res.status(204).end(); return; }
  setCors(res, req);
  if (req.method !== 'POST') { res.status(405).json({ error: 'POST only' }); return; }

  const allowed = process.env.ALLOWED_ORIGIN;
  if (allowed && req.headers.origin && req.headers.origin !== allowed) {
    res.status(403).json({ error: 'Origin not allowed' });
    return;
  }

  // Pick the provider by whichever key is configured.
  let provider, key;
  if (process.env.GEMINI_API_KEY) { provider = 'gemini'; key = process.env.GEMINI_API_KEY; }
  else if (process.env.OPENAI_API_KEY) { provider = 'openai'; key = process.env.OPENAI_API_KEY; }
  else if (process.env.ANTHROPIC_API_KEY) { provider = 'anthropic'; key = process.env.ANTHROPIC_API_KEY; }
  else {
    res.status(500).json({ error: 'Server not configured: add a vision API key in Vercel → Settings → Environment Variables. Recommended: GEMINI_API_KEY (cheapest). Then redeploy.' });
    return;
  }

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  body = body || {};

  const b64 = body.b64;
  const mime = (body.mime || 'image/jpeg').toString();
  const notes = (body.notes || '').toString().slice(0, 500);
  if (!b64 || typeof b64 !== 'string') { res.status(400).json({ error: 'Missing image' }); return; }
  if (b64.length > 9000000) { res.status(413).json({ error: 'Image too large — please use one under ~6 MB.' }); return; }

  const text = notes ? (SYSTEM_PROMPT + '\n\nGardener notes: ' + notes) : SYSTEM_PROMPT;

  try {
    let out;
    if (provider === 'gemini') out = await callGemini(key, mime, b64, text);
    else if (provider === 'openai') out = await callOpenAI(key, mime, b64, text);
    else out = await callAnthropic(key, mime, b64, text);
    res.status(200).json({ text: out || '(no response)', provider: provider });
  } catch (e) {
    res.status(502).json({ error: 'Proxy error (' + provider + '): ' + (e.message || String(e)) });
  }
};
