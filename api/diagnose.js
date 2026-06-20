// api/diagnose.js — secure DeepSeek vision proxy for the Garden Ops "Diagnose" tool.
//
// The DeepSeek API key lives ONLY on the server, as a Vercel Environment Variable
// named DEEPSEEK_API_KEY. It is never sent to the browser. The published page calls
// this function at /api/diagnose; this function calls DeepSeek and returns the text.
//
// Optional hardening:
//   ALLOWED_ORIGIN  — set to your site URL (e.g. https://your-garden.vercel.app) to
//                     reject requests from other origins.
//
// Runs on Vercel's Node.js runtime (global fetch is available).

const ALLOWED_MODELS = new Set(['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-chat']);

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

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') { setCors(res, req); res.status(204).end(); return; }
  setCors(res, req);
  if (req.method !== 'POST') { res.status(405).json({ error: 'POST only' }); return; }

  const allowed = process.env.ALLOWED_ORIGIN;
  if (allowed && req.headers.origin && req.headers.origin !== allowed) {
    res.status(403).json({ error: 'Origin not allowed' });
    return;
  }

  const key = process.env.DEEPSEEK_API_KEY;
  if (!key) {
    res.status(500).json({ error: 'Server not configured: add DEEPSEEK_API_KEY in Vercel → Settings → Environment Variables, then redeploy.' });
    return;
  }

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  body = body || {};

  const b64 = body.b64;
  const mime = (body.mime || 'image/jpeg').toString();
  const notes = (body.notes || '').toString().slice(0, 500);
  let model = (body.model || 'deepseek-v4-flash').toString();
  if (!ALLOWED_MODELS.has(model)) model = 'deepseek-v4-flash';

  if (!b64 || typeof b64 !== 'string') { res.status(400).json({ error: 'Missing image' }); return; }
  if (b64.length > 9000000) { res.status(413).json({ error: 'Image too large — please use one under ~6 MB.' }); return; }

  const userText = notes ? (SYSTEM_PROMPT + '\n\nGardener notes: ' + notes) : SYSTEM_PROMPT;
  const payload = {
    model: model,
    max_tokens: 1200,
    messages: [{
      role: 'user',
      content: [
        { type: 'text', text: userText },
        { type: 'image_url', image_url: { url: 'data:' + mime + ';base64,' + b64 } }
      ]
    }]
  };

  try {
    const r = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      res.status(r.status).json({ error: (j.error && j.error.message) || ('DeepSeek HTTP ' + r.status) });
      return;
    }
    const text = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || '';
    res.status(200).json({ text: text });
  } catch (e) {
    res.status(502).json({ error: 'Proxy error: ' + (e.message || String(e)) });
  }
};
