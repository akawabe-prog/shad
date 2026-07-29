# SHAD Fitment Integration Notes

Date: 2026-06-15

## Purpose

Add two fitment flows to the static SHAD brand site:

- Vehicle-first search on `index.html` and `products.html`
- Product-first compatibility check on every `product-*.html` page

The implementation intentionally uses a shared generated JSON index and a shared browser-side script so parallel work can adjust UI or data without touching every page by hand.

## Source Data

Initial source supplied by the user:

- `/Users/cjmac002/Downloads/shad-fitting.zip`

The zip was inspected and extracted to:

- `/private/tmp/shad-fitting-inspect`

The source zip generates product-specific demo HTML and JSON under `dist/`. The current site integration uses the generated `dist/*.json` files, not the demo HTML UI.

## Generated Site Data

Generated file:

- `site/data/fitment/fitment_index.json`
- `site/data/fitment/fitment_index.js`

Generator:

- `tools/build_fitment_index.js`

Regenerate after rebuilding or re-extracting the zip:

```bash
node tools/build_fitment_index.js /private/tmp/shad-fitting-inspect/dist
```

If the zip is extracted somewhere else, pass that `dist` directory as the first argument.

`fitment_index.js` is a script fallback that sets `window.SHAD_FITMENT_INDEX`. Keep it in sync with `fitment_index.json`; it allows the finder to work in environments where `fetch()` cannot read local JSON, such as some direct `file://` previews.

Current generated summary:

- Vehicle rows: 483
- Site products covered: 14
- Site products unsupported: 12

Covered current site products:

`SH23, SH33, SH34, SH38X, SH44, SH47, SH48, SH51, SH58X, TR37, TR41, TR46, TR48, TR55`

Unsupported current site products:

`E48, LOCK, SEAT, SL18, SW80, TR10, TR27, TR30, TR36, TR40, TR47, TR50`

Products present in the source fitment zip but not in the current site catalog:

`SH26, SH29, SH35, SH36, SH39, SH40, SH40CG, SH45, SH59X`

## Frontend Files

Shared script:

- `site/js/fitment.js`

Shared styles:

- `site/css/custom.css`

Vehicle-first finder is wired to:

- `site/index.html`
- `site/products.html`

Product compatibility checker was inserted into all:

- `site/product-*.html`

Each product page checker is identified by:

```html
<section data-product-fitment-checker data-product-code="TR41">
```

Unsupported products show a "fitment data is preparing" message and disable the controls.

Vehicle search result cards append `?fitment={vehicleId}` to product detail URLs. Product detail pages read that parameter, preselect the matching maker/model/year, and immediately render the compatible state.

Product detail pages also preserve the same `fitment` query parameter on related product links such as `Same Series`. If the target product is compatible with that vehicle, it renders the compatible state immediately. If the target product has fitment data but is not compatible with that vehicle, it renders a non-compatible message instead of staying blank.

## Data Model Notes

`fitment_index.json` contains:

- `coverage`: coverage and unsupported product lists
- `products`: existing `site/products_data.json` copied into the index
- `vehicles`: normalized vehicle rows

Each vehicle row has:

- `maker`
- `displayModel`
- `modelKey`
- `yearLabel`
- `fitments[]`

Each fitment has:

- `productCode`
- `productName`
- `productUrl`
- `category`: `topcase` or `sidecase`
- `baseplateCode` / `baseplateName` for top cases
- `system` for side cases
- `fittingUrl`
- `fittingProductCode` when downloaded API data is available

Downloaded fitting products are stored once in the top-level `fittingProducts` array rather than
duplicated across every fitment row. Each product contains `cjCode`, `title`, `priceTaxIn`,
`status`, and the local downloaded `image` path.

## Fitting Product API Download

The fitting-kit cards use the same CustomJapan batch item API pattern as the eXs implementation.

```bash
node tools/enrich_fitment_products.js
node tools/build_fitment_index.js
```

`enrich_fitment_products.js` first opens one public Moto CustomJapan item page to receive the
`authorization` and `xGuId` cookies, then calls:

```text
POST https://api-e.customjapan.net/api/v1/items
```

IDs are sent in batches of 50. Product images are downloaded from
`https://img.customjapan.net` into `site/img/fitment/`, and normalized metadata is written to
`site/data/fitment/fitting_products.json`. Existing records and images are reused unless
`--refresh` is supplied.

API item IDs that cannot be returned, such as discontinued or unregistered legacy records, are
written to `site/data/fitment/fitting_products_missing.json`. Their UI keeps the original external
text link as a fallback.

Useful options:

```bash
node tools/enrich_fitment_products.js --limit=10
node tools/enrich_fitment_products.js --batch-size=25 --concurrency=4
node tools/enrich_fitment_products.js --refresh
```

Current download result on June 15, 2026:

- 574 unique fitting product URLs
- 541 API product records saved
- 541 local product images saved (about 34 MB)
- 33 legacy/unregistered API IDs retained as external-link fallbacks

Year extraction is intentionally conservative. It extracts text from parentheses or brackets and keeps the original vehicle label available as `displayModel`.

## Verification Performed

Local server:

```bash
cd site
python3 -m http.server 8087
```

Browser checks:

- `index.html#finder`: selected Honda / NC750S-NC750X / 16-19 / 16-25 and got 7 product cards
- `products.html`: finder rendered and loaded 50 maker options
- `product-tr41.html`: product checker returned "装着できます" and one fitting link for Honda NC750
- `product-tr47.html`: unsupported state rendered and controls were disabled
- Browser console: no errors observed

Static checks:

```bash
node --check site/js/fitment.js
node --check tools/build_fitment_index.js
node -e "const d=require('./site/data/fitment/fitment_index.json'); console.log({schema:d.schemaVersion, vehicles:d.vehicles.length, covered:d.coverage.siteProductsCovered.length, unsupported:d.coverage.siteProductsUnsupported.length});"
```

Additional check after adding the script fallback:

- `index.html#finder` over HTTP loaded 50 maker options with no console errors.

Additional check after adding search-result carryover:

- `index.html#finder` Honda / NC750 search returned 7 product cards.
- The first product link included `?fitment=...`.
- Opening that link on `product-sh44.html` preselected Honda / `NC750S/NC750X` / `16-19 / 16-25` and rendered `装着できます`.

Additional check after adding related-product carryover:

- `product-tr41.html?fitment=...` rewrote `Same Series` links to include the same `fitment` parameter.
- Opening `product-tr46.html?fitment=...` preselected the same Honda / `NC750S/NC750X` vehicle and rendered `装着できます`.

## Follow-up Candidates

- Add source CSVs or the zip contents into the repository if future rebuilds must not depend on `/Users/cjmac002/Downloads/shad-fitting.zip`.
- Extend the source sidecase mapping for `TR47`, `TR36`, and `TR27` if those should be fitment-searchable.
- Improve vehicle/year normalization if the UI needs separate model families instead of source labels such as `NC750S/NC750X`.
- Add keyword search UI to vehicle-first finder if selecting from long model lists becomes too heavy.
