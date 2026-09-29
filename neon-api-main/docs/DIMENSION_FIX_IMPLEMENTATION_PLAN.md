# Dimension Fix — Exact Implementation Plan

**Project:** `neon-api` (`C:\Users\adx\Documents\GitHub\neon-api`)  
**Goal:** Shop configurator dimensions must match LightBurn for the same text + font + height, for **all** fonts. Client also needs the same calculation logic for DXF automation.  
**Scope:** Backend only for dimension correctness.  
**Rule:** Do **not** change unrelated features (variants, Shopify auth, product create, cart, pricing UI).

---

## 1. Problem summary (client)

| Observation | Evidence |
|-------------|----------|
| Changing font does not change width | Bonn / Duisburg / Essen / München all show **78.5 × 10 cm** for `Hallo wie gehts?` at height M (10 cm) |
| Dimensions ≠ LightBurn | Bonn LB ≈ **1160 × 100 mm**; shop **785 × 100 mm**. Duisburg LB ≈ **710 × 100 mm**; shop still **785 × 100 mm** |
| Client ask | Recheck all fonts; send calculation code for DXF automation |

Frontend already posts `font` (display name, e.g. `"Bonn"`) and `height`/`width` in cm to `POST /api/measurements`, then divides API `Width`/`Height` by 10.  
**Root cause is backend**, not the theme size buttons.

---

## 2. Current code behavior (what exists today)

### Entry point
- File: `api/views.py` → `get_measurements`
- Inputs (form): `font`, `text`, `height` **or** `width` (cm)
- Converts cm → internal units: `value * 10`
- Calls helpers, returns JSON:
  ```json
  { "Width": <number>, "Height": <number>, "frequent_sizes": [ {"height": 80, "width": ...}, ... ] }
  ```
- Frequent heights (mm-ish): `[80, 100, 120, 150, 180, 200]` → S…2XL

### Font resolution
- File: `api/helpers.py` → `get_font_path(font)`
- Maps **15** names only (Aachen…Stuttgart)
- Unknown names → `static/fonts/Aachen/arial.ttf` (**this causes identical 78.5 cm for Bonn/Duisburg/…**)

### Measurement
- File: `api/helpers.py` → `calculate_text_width` / `calculate_text_height`
- Pillow `ImageFont.truetype` + `textbbox`
- Binary-ish loop font size 1…1500 until bbox height/width ≥ target
- Returns bbox width/height in the same unit space as the `* 10` input

### Known wrong files on disk today
| Font name | Current file | Issue |
|-----------|--------------|--------|
| Aachen | `Aachen/arial.ttf` | Not real neon font |
| Kiel | `Kiel/timesbd.ttf` | Not real neon font |
| Bonn, Duisburg, Essen, Freiburg, Paderborn, Wuppertal, München | *(missing)* | Fallback to Arial |

---

## 3. Issues to fix (exactly 3)

1. **Missing font mapping** for 7 frontend fonts → Arial fallback → same width always  
2. **Wrong font files** for at least Aachen and Kiel  
3. **Measurement method** may still disagree with LightBurn even with correct files (Pillow screen bbox ≠ LB object box)

Do these in **phases** so existing API contract and other endpoints stay safe.

---

## 4. Hard safety boundaries (do not touch)

| Area | Files / endpoints | Action |
|------|-------------------|--------|
| Variant create/update | `api/views.py` `get_variant`, `update_variant`; helpers `createVariant`, `create_product` | **No changes** |
| Shopify auth / install | `shopify_app/*` | **No changes** |
| Products / orders / image upload | other `api/views.py` routes | **No changes** |
| URL routes | `api/urls.py`, project `urls.py` | **No changes** (keep path `measurements`) |
| Response JSON keys | `Width`, `Height`, `frequent_sizes` | **Keep exact names** (frontend depends on them) |
| Unit contract | API returns values that frontend divides by **10** to get cm | **Keep** unless you deliberately update frontend too (out of scope) |
| Frontend theme / React | `niko`, Desktop theme | **No changes** for this fix |
| Env / Heroku config | `.env`, Shopify keys | **No changes** for dimension math |

Allowed touch set for the fix:

- `api/helpers.py` — **only** `get_font_path`, `calculate_text_width`, `calculate_text_height`, `calculate_widths_for_heights` (and optionally extract shared measure helpers)
- `api/views.py` — **only** inside `get_measurements` if needed (validation / clearer errors); prefer zero changes here in Phase A
- `static/fonts/**` — add/replace font files
- New optional: `docs/` test notes, small unit/script under e.g. `scripts/measure_check.py` (local only)
- New optional: `docs/DIMENSION_CALCULATION_FOR_DXF.md` (client handoff after math is verified)

---

## 5. Font names contract (must match frontend)

Frontend sends **`Fonts[i].name`** from `niko/src/Assets.js` (not CSS family):

| # | `font` POST value | CSS family (preview only) |
|---|-------------------|---------------------------|
| 0 | `Aachen` | `aachen-neon-icons` |
| 1 | `Berlin` | `berlin-neon-icons` |
| 2 | `Bremen` | `bremen-neon-icons` |
| 3 | `Dortmund` | `dortmund-neon-icons` |
| 4 | `Frankfurt` | `frankfurt-neon-icons` |
| 5 | `Hamburg` | `hamburg-neon-icons` |
| 6 | `Hannover` | `hannover-neon-icons` |
| 7 | `Kiel` | `kiel-neon-icons` |
| 8 | `Koeln` | `koeln-neon-icons` |
| 9 | `Leipzig` | `leipzig-neon-icons` |
| 10 | `Mainz` | `mainz-neon-icons` |
| 11 | `Osnabrueck` | `osnabrueck-neon-icons` |
| 12 | `Potsdam` | `potsdam-neon-icons` |
| 13 | `Regensburg` | `regensburg-neon-icons` |
| 14 | `Stuttgart` | `stuttgart-neon-icons` |
| 15 | `Bonn` | `Bonn-neon-icons` |
| 16 | `Duisburg` | `Duisburg-neon-icons` |
| 17 | `Essen` | `Essen-neon-icons` |
| 18 | `Freiburg` | `Freiburg-neon-icons` |
| 19 | `Paderborn` | `Paderborn-neon-icons` |
| 20 | `Wuppertal` | `Wuppertal-neon-icons` |
| 21 | `München` | `München-neon-icons` |

CDN sources (prefer **`.otf`** for measuring when `.ttf` on CDN is mislabeled WOFF — verify file is real OpenType/TrueType before use):

- Shopify Files under shop `76513018186`, e.g. `Bonn.otf`, `Duisburg.otf`, … (see `niko/assets/neon-customizer.css`)

**Unicode note:** map exact string `München` (with ü). Optionally also accept `Munchen` if ever sent.

---

## 6. Phase A — Fix font files + mapping (safe, highest priority)

**Purpose:** Stop identical widths for new fonts. Minimal risk to other features.

### A1. Obtain correct font files
For each of the 22 names, place files under:

```text
static/fonts/<FontName>/<FontName>.otf   # preferred if valid
# or
static/fonts/<FontName>/<FontName>.ttf   # if valid TrueType
```

Sources (in order):
1. Same files client uses in LightBurn (best)
2. Valid `.otf` from Shopify CDN / `Neon Client` handoff `fonts/` packs
3. Never use system `arial.ttf` / `timesbd.ttf` as stand-ins

Verify each file opens with Pillow (`ImageFont.truetype`) before committing.

### A2. Rewrite `get_font_path` carefully

**Recommended shape (dict map, same behavior, easier to audit):**

```python
FONT_FILES = {
    "Aachen": ("Aachen", "Aachen.otf"),       # replace arial.ttf
    "Berlin": ("Berlin", "Berlin.ttf"),       # keep if valid; prefer .otf if better
    # ... all 22 ...
    "München": ("München", "München.otf"),
}

def get_font_path(font):
    entry = FONT_FILES.get(font)
    if not entry:
        # DO NOT silently use Arial
        raise ValueError(f"Unknown font: {font}")
    folder, filename = entry
    path = os.path.join(settings.BASE_DIR, "static", "fonts", folder, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Font file missing: {path}")
    return path
```

**In `get_measurements` only** (narrow change): catch missing/unknown font and return `400` JSON error instead of crashing or falling back to Arial. Do not change other views.

### A3. What success looks like after Phase A
Same text `Hallo wie gehts?`, height `10`:

| Font | Expectation |
|------|-------------|
| Bonn | Width **≠** 78.5; closer to LB ~116 cm |
| Duisburg | Width **≠** 78.5; closer to LB ~71 cm |
| Essen / München | Widths **differ from each other** |

If Phase A alone is “close enough” to LightBurn for client, ship Phase A first. If still off, continue Phase B.

---

## 7. Phase B — Align measurement with LightBurn (only if needed)

**Purpose:** Same numbers as LightBurn green Width/Height (object box), lock ON, set height only.

### B1. Keep API contract
- Still accept cm from client
- Still return `Width`/`Height` in the same scale (÷10 = cm on frontend)
- Still return `frequent_sizes` with same height list

### B2. Change only the inner measure functions
Candidate approach (pick one after spike; document chosen method in DXF handoff):

1. **Preferred spike:** FreeType / `fontTools` glyph advances + tight bounding box scaled so **text bbox height == target height (mm)**, then width scales linearly.  
2. **Alternative:** Keep Pillow but measure with larger canvas, use ascent/descent consistently, and calibrate scale against LightBurn reference cases.  
3. **Avoid:** Changing variant/pricing logic; avoid frontend-only hacks.

### B3. Calibration fixtures (must pass before deploy)

Use LightBurn as source of truth (metric, lock aspect, set height):

| text | font | height cm | Expected width cm (from LB) |
|------|------|-----------|-----------------------------|
| `Hallo wie gehts?` | Bonn | 10 | ≈ 116.0 |
| `Hallo wie gehts?` | Duisburg | 10 | ≈ 71.0 |
| `hlo` | Berlin | 17.6 | ≈ 29.8 (from earlier LB ~298 mm) |

Tolerance: agree with client (suggest ±1–2 mm or ±0.2 cm for DXF).

### B4. Dependency rule
If adding `fonttools` / `freetype-py`:
- Add to `requirements.txt`
- Test locally on Windows + ensure Heroku build packs still work
- Do **not** remove Pillow if still used elsewhere

---

## 8. Phase C — Client DXF handoff (after A/B verified)

Deliver a short doc + the **exact** Python functions used in production:

- Inputs: `text`, `font_name`, `height_cm` (or `width_cm`)
- Outputs: `width_cm`, `height_cm`
- List of font file paths / names
- Unit rules (cm ↔ internal)
- Note: must use **same font files** as API

Do **not** send broken Arial-fallback code.

Optional later: thin `POST /api/measurements` stays the shop interface; DXF tool can call API or copy the function.

---

## 9. Exact file change checklist

### Phase A
- [ ] Add/replace files under `static/fonts/` for all 22 fonts  
- [ ] Update `get_font_path` in `api/helpers.py` (map + no Arial fallback)  
- [ ] Optional: unknown font → 400 in `get_measurements` only  
- [ ] Local tests for Bonn/Duisburg/Essen/München vs 78.5 bug  
- [ ] Commit to `neon-api` (fonts + helpers); **never** commit `.env`  
- [ ] Deploy Heroku only after local OK (needs Heroku access)

### Phase B (if A insufficient)
- [ ] Spike measure method vs LightBurn fixtures  
- [ ] Replace only `calculate_text_width` / `calculate_text_height` / `calculate_widths_for_heights`  
- [ ] Re-run all fixtures + smoke `/api/variant` still works (no code change expected)  
- [ ] Update `requirements.txt` only if new lib required  

### Phase C
- [ ] Write `docs/DIMENSION_CALCULATION_FOR_DXF.md` + exportable function  
- [ ] Send to client after numbers match  

---

## 10. Local test commands (do not change production)

```powershell
cd "C:\Users\adx\Documents\GitHub\neon-api"
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

```powershell
# Same text/height, different fonts — widths must differ
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/measurements" -Body @{ font = "Bonn"; text = "Hallo wie gehts?"; height = "10" }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/measurements" -Body @{ font = "Duisburg"; text = "Hallo wie gehts?"; height = "10" }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/measurements" -Body @{ font = "Essen"; text = "Hallo wie gehts?"; height = "10" }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/measurements" -Body @{ font = "München"; text = "Hallo wie gehts?"; height = "10" }
```

Compare `Width/10` to LightBurn width (cm).

**Regression smoke (must still work after changes):**
- `GET /api/drinks/` → 200  
- Existing mapped font e.g. Berlin still returns sizes  
- Do not redeploy until smoke + LB checks pass  

---

## 11. Deploy notes (later — out of coding Phase A local)

- Live app: `deinlieblingswerk-9faf1bdc5cb1.herokuapp.com`  
- Requires Heroku account access (not available until client grants it)  
- Prefer staging app first, then live  
- Pushing GitHub alone does **not** update live sizes  

---

## 12. Implementation order (recommended)

1. Phase A fonts + mapping → fixes “same 78.5 for every new font”  
2. Compare to LightBurn screenshots  
3. Phase B only if still wrong  
4. Phase C DXF doc for client  
5. Deploy  

---

## 13. Out of scope / non-goals

- Redesigning configurator UI  
- Changing price formula in frontend  
- TeeInBlue / other Shopify apps  
- Renaming `sample_django_app` package  
- Editing live theme until API is fixed and deployed  

---

## 14. Acceptance criteria

- [ ] Changing font changes width for all 22 fonts  
- [ ] Bonn / Duisburg / Essen / München no longer share one width for same text+height  
- [ ] Agreed tolerance vs LightBurn for client reference cases  
- [ ] `/api/measurements` response shape unchanged  
- [ ] Variant / auth / other API routes untouched and still working  
- [ ] Client receives calculation code matching production API  

---

*Document created for implementation guidance only. No code changes applied by this document.*
