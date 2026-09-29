# Dimension calculation (for DXF automation)

Use the **same** logic and **same** font files as `neon-api` so DXF matches the shop.

## API contract (shop)

`POST /api/measurements`  
Form fields: `font` (display name), `text`, and either `height` or `width` in **cm**.

Response:

```json
{ "Width": <number>, "Height": <number>, "frequent_sizes": [...] }
```

Shop UI shows cm as `Width / 10` and `Height / 10`.  
Internal units: cm × 10 (same as millimetres for the height target).

## Core idea

1. Resolve `font` → file under `static/fonts/...` (see `FONT_FILES` in `api/helpers.py`).
2. Scale font size until the **ink bounding box height** equals the target height (e.g. 100 for 10 cm).
3. Return that box’s **width** (and height).

Implementation: Pillow `textbbox` + binary search over font size — see:

- `api/helpers.py` → `get_font_path`, `calculate_text_width`, `calculate_text_height`

## Reference check (local)

Text: `Hallo wie gehts?`, height: 10 cm  

| Font | API width÷10 | LightBurn (client) |
|------|--------------|--------------------|
| Bonn | ~119.1 cm | ~116.0 cm |
| Duisburg | ~71.8 cm | ~71.0 cm |

Small remaining differences can come from LB vs Pillow metrics; use the **same font files** as this repo.

## Do not

- Fall back unknown fonts to Arial (that caused all new fonts to show 78.5 cm).
- Use mislabeled WOFF files renamed as `.ttf`.
