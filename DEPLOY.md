# Publishing Garden Ops (Vercel + DeepSeek)

The site is static HTML. The **Diagnose** tool's default provider, **DeepSeek**, runs through a
small serverless function (`api/diagnose.js`) so your DeepSeek API key stays **server-side** and
is never exposed in the page.

## 1. Get a DeepSeek API key
- Sign in at **https://platform.deepseek.com** → **API keys** → create a key (starts with `sk-`).
- Add a little credit, and set a **spend limit** (see security note below).

## 2. Deploy to Vercel
You can deploy this folder either of these ways:

**A. Vercel dashboard (easiest)**
1. Go to **vercel.com → Add New → Project**.
2. Import this folder (or its Git repo). Framework preset: **Other** (it's static + an `api/` function).
3. Click **Deploy**.

**B. Vercel CLI**
```bash
npm i -g vercel
cd "Garden Management"
vercel          # first deploy (follow prompts)
vercel --prod   # promote to production
```

## 3. Add your key as an Environment Variable  ← required for DeepSeek
In the Vercel project: **Settings → Environment Variables → Add**
| Name | Value | Environments |
|---|---|---|
| `DEEPSEEK_API_KEY` | your `sk-...` key | Production (and Preview) |
| `ALLOWED_ORIGIN` *(optional)* | your site URL, e.g. `https://your-garden.vercel.app` | Production |

Then **redeploy** (Deployments → ⋯ → Redeploy) so the function picks up the variable.

## 4. Test
Open your live URL → **Dashboard → Diagnose** → drop a plant photo → **Diagnose**.
With `DEEPSEEK_API_KEY` set, it returns an IPM-first diagnosis with no key needed in the browser.

---

## Notes
- **What gets published:** only the HTML pages, favicon assets, and `api/diagnose.js`.
  `.vercelignore` keeps `data/`, `scripts/`, `skills/`, `hardware/`, `docs/`, and `*.md` private.
- **Other providers still work bring-your-own-key:** Claude, OpenAI, and Gemini are selectable in
  the Diagnose tool and call their APIs directly from the browser with a key you paste (stored only
  on your device). DeepSeek is the only one routed through the proxy.
- **Local preview:** opening the files directly (`file://`) won't have the `/api/diagnose` function,
  so DeepSeek won't work locally — use Claude or Gemini with your own key, or run `vercel dev`.
- **Security — this is an open proxy.** Anyone who can load your published page can call
  `/api/diagnose`, which spends your DeepSeek credit. Mitigations baked in: image-only requests,
  capped output, model allow-list. You should also:
  - set a **monthly spend limit** on your DeepSeek account, and
  - set **`ALLOWED_ORIGIN`** to your site URL to block other websites from using your endpoint.
- **Model:** the proxy uses `deepseek-v4-flash` (cheapest vision) by default; allow-list also permits
  `deepseek-v4-pro` for higher accuracy. Change the model field in the Diagnose tool.
