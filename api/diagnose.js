// api/diagnose.js — secure, vision-capable proxy for Garden Ops.
//
// Two modes (body.mode):
//   "diagnose" (default) → IPM-first plant diagnosis (single image), prose in {text}.
//   "scan"              → garden inventory from one OR MORE photos, JSON in {text}:
//                         {"beds":[{"name":"...","plants":[{"name":"Tomato","qty":2}]}]}
//
// Images: send body.images = [{mime,b64}, ...] (preferred), or a single body.b64/body.mime.
//
// DeepSeek's public API is TEXT-ONLY, so this uses a vision model chosen by whichever
// key is set in Vercel → Settings → Environment Variables (never sent to the browser):
//   GEMINI_API_KEY (recommended) → OPENAI_API_KEY → ANTHROPIC_API_KEY
// Optional: GEMINI_MODEL / OPENAI_MODEL / ANTHROPIC_MODEL, ALLOWED_ORIGIN.

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

const SCAN_PROMPT =
  "You are helping a gardener inventory their garden from one or more photos. The photos may show the " +
  "SAME garden from different angles, or different beds — merge them into a single inventory and do NOT " +
  "double-count a bed or plant that appears in more than one photo. Identify the distinct garden beds, " +
  "raised beds, rows, or containers, and the plants growing in each. " +
  "Respond with ONLY a JSON object in exactly this shape, no prose and no code fences:\n" +
  '{"beds":[{"name":"short label, e.g. Raised bed (left)","plants":[{"name":"common plant name, e.g. Tomato","qty":1}]}]}\n' +
  "Use common single plant names (Tomato, Kale, Basil, Strawberry, Pepper, Rose, etc.). Estimate qty as a small integer. " +
  "If you cannot identify a plant, give your best one-word guess. If no garden or plants are visible, return {\"beds\":[]}.";

function setCors(res, req) {
  const allowed = process.env.ALLOWED_ORIGIN;
  res.setHeader('Access-Control-Allow-Origin', allowed || (req.headers.origin || '*'));
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'content-type');
}

async function callGemini(key, imgs, text, json) {
  const model = process.env.GEMINI_MODEL || 'gemini-flash-latest';
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + model +
    ':generateContent?key=' + encodeURIComponent(key);
  const parts = [{ text: text }].concat(imgs.map(function (im) { return { inline_data: { mime_type: im.mime, data: im.b64 } }; }));
  const payload = { contents: [{ parts: parts }] };
  if (json) payload.generationConfig = { responseMimeType: 'application/json' };
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j.error && j.error.message) || ('Gemini HTTP ' + r.status));
  const c = j.candidates && j.candidates[0];
  return ((c && c.content && c.content.parts) || []).map(p => p.text || '').join('\n').trim();
}

async function callOpenAI(key, imgs, text, json) {
  const model = process.env.OPENAI_MODEL || 'gpt-4o-mini';
  const content = [{ type: 'text', text: text }].concat(imgs.map(function (im) {
    return { type: 'image_url', image_url: { url: 'data:' + im.mime + ';base64,' + im.b64 } };
  }));
  const reqBody = { model: model, max_tokens: 1500, messages: [{ role: 'user', content: content }] };
  if (json) reqBody.response_format = { type: 'json_object' };
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST', headers: { 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json' }, body: JSON.stringify(reqBody)
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j.error && j.error.message) || ('OpenAI HTTP ' + r.status));
  return ((j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || '').trim();
}

async function callAnthropic(key, imgs, text, json) {
  const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-6';
  const content = imgs.map(function (im) {
    return { type: 'image', source: { type: 'base64', media_type: im.mime, data: im.b64 } };
  }).concat([{ type: 'text', text: text }]);
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: model, max_tokens: 1500, messages: [{ role: 'user', content: content }] })
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

  // Accept an images array, or a single b64/mime.
  let imgs = Array.isArray(body.images) ? body.images : (body.b64 ? [{ mime: body.mime, b64: body.b64 }] : []);
  imgs = imgs
    .filter(function (x) { return x && typeof x.b64 === 'string' && x.b64; })
    .slice(0, 6)
    .map(function (x) { return { mime: (x.mime || 'image/jpeg').toString(), b64: x.b64 }; });
  if (!imgs.length) { res.status(400).json({ error: 'Missing image' }); return; }
  const total = imgs.reduce(function (s, x) { return s + x.b64.length; }, 0);
  if (total > 18000000) { res.status(413).json({ error: 'Photos too large — use fewer or smaller images (under ~12 MB total).' }); return; }

  const isScan = (body.mode || 'diagnose').toString() === 'scan';
  const notes = (body.notes || '').toString().slice(0, 500);
  const text = isScan ? SCAN_PROMPT : (notes ? (SYSTEM_PROMPT + '\n\nGardener notes: ' + notes) : SYSTEM_PROMPT);

  try {
    let out;
    if (provider === 'gemini') out = await callGemini(key, imgs, text, isScan);
    else if (provider === 'openai') out = await callOpenAI(key, imgs, text, isScan);
    else out = await callAnthropic(key, imgs, text, isScan);
    res.status(200).json({ text: out || (isScan ? '{"beds":[]}' : '(no response)'), provider: provider });
  } catch (e) {
    res.status(502).json({ error: 'Proxy error (' + provider + '): ' + (e.message || String(e)) });
  }
};
