# Publishing Garden Ops (Vercel + hosted vision AI)

The site is static HTML. The **Diagnose** tool's default provider is **Hosted** — it sends the
photo to a small serverless function (`api/diagnose.js`) so your AI key stays **server-side** and
is never exposed in the page.

> **Why not DeepSeek?** DeepSeek's public API is **text-only** — it can't accept images, so it
> can't do photo diagnosis. The proxy uses a **vision** model instead. It auto-selects based on
> which key you set: **`GEMINI_API_KEY`** (recommended — cheapest, has a free tier),
> else `OPENAI_API_KEY` (gpt-4o-mini), else `ANTHROPIC_API_KEY` (Claude).

## 1. Get a vision API key (Gemini recommended)
- Go to **https://aistudio.google.com/apikey** (Google AI Studio) → **Create API key**.
- Free tier is generous; you can add billing later if you outgrow it.
- *(Alternatives: an OpenAI key from platform.openai.com, or an Anthropic key from console.anthropic.com.)*

## 2. Deploy to Vercel
Already connected to GitHub (`EndaleK/Garden-Ops`), so a `git push` auto-deploys. First time:
**vercel.com → Add New → Project → Import `EndaleK/Garden-Ops` → Deploy.**

## 3. Add your key as an Environment Variable  ← required for Hosted diagnosis
In the **garden-ops** project → **Settings → Environments** (this account labels it
"Environments") → add a variable:

| Name | Value | Environments |
|---|---|---|
| `GEMINI_API_KEY` | your Gemini key | Production (and Preview) |
| `ALLOWED_ORIGIN` *(optional)* | your site URL, e.g. `https://garden-ops.vercel.app` | Production |

Or via CLI (no menu hunting):
```
vercel link
vercel env add GEMINI_API_KEY production
vercel --prod
```

Then **redeploy** (Deployments → ⋯ → Redeploy) so the function picks it up. Env vars only apply
to *new* deployments.

## 4. Test
Open your live URL → **Dashboard → Diagnose** → drop a plant photo → **Diagnose**. With the key
set, it returns an IPM-first diagnosis with no key needed in the browser.

---

## Notes
- **What gets published:** only the HTML pages, favicon assets, and `api/diagnose.js`.
  `.vercelignore` keeps `data/`, `scripts/`, `skills/`, `hardware/`, `docs/`, and `*.md` private.
- **Other providers still work bring-your-own-key:** in the Diagnose tool you can switch the
  provider to Claude, OpenAI, or Gemini and paste your own key (stored only on your device).
- **Local preview:** opening the files directly (`file://`) has no `/api/diagnose` function, so the
  Hosted option won't work locally — use Claude or Gemini with your own key, or run `vercel dev`.
- **Security — this is an open proxy.** Anyone who loads your published page can call
  `/api/diagnose`, which spends your AI credit. Mitigations baked in: image-only requests, capped
  output, origin check. You should also set a **spend/budget limit** on your AI account and set
  **`ALLOWED_ORIGIN`** to your site URL.
- **Model:** defaults to `gemini-2.0-flash`. Override with `GEMINI_MODEL` (or `OPENAI_MODEL` /
  `ANTHROPIC_MODEL`) if you want a different one.
