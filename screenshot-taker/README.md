Screenshot Taker takes full-page or viewport screenshots of any list of URLs, letting you pick which **stealth browser engine** drives the page: plain [Playwright](https://playwright.dev/python/), [playwright-stealth](https://github.com/AtuboDad/playwright_stealth), [Patchright](https://github.com/kaliiiiiiiiii-vinyzu/patchright-python) (an undetected Chromium patch), or [Camoufox](https://camoufox.com/) (a hardened Firefox fork). Give it a list of start URLs, pick an engine, and get PNG screenshots back in your dataset - no code required. Runs on the [Apify platform](https://apify.com), so you get scheduling, an API, integrations, and proxy rotation for free.

## Why use Screenshot Taker?

Sites with bot detection (Cloudflare, DataDome, PerimeterX, etc.) block plain headless browsers. Rather than committing to one anti-detection stack, this Actor lets you **A/B test stealth engines per site** - some targets need Camoufox's Firefox fingerprint, others are fine with Patchright's patched Chromium, and some don't need stealth at all. Common uses: visual regression testing, monitoring landing pages, archiving pages, building thumbnail previews, or verifying a page renders correctly behind a proxy.

## How to use Screenshot Taker

1. Open the Actor and go to the **Input** tab.
2. Add one or more **URLs to screenshot**.
3. Pick a **Stealth browser engine** (defaults to Camoufox).
4. Optionally tune the viewport size, full-page capture, a CSS selector to wait for, extra wait time, and proxy settings.
5. Click **Start** and check the **Output** tab once the run finishes.

## Input

| Field | Description |
|---|---|
| `start_urls` | List of URLs to screenshot. |
| `stealth_engine` | One of `playwright`, `playwright_stealth`, `patchright`, `camoufox`. |
| `full_page` | Capture the full scrollable page instead of just the viewport. |
| `viewport_width` / `viewport_height` | Browser viewport size in pixels. |
| `wait_for_selector` | Optional CSS selector to wait for before capturing. |
| `wait_after_load_ms` | Extra delay after page load, for animations/lazy content. |
| `navigation_timeout_secs` | Max time to wait for the page to load. |
| `proxyConfiguration` | Optional Apify Proxy / custom proxy settings. Ignored for Camoufox, which manages its own network stack. |

See the Input tab for the full schema.

## Output

Each screenshot is pushed as one dataset item:

```json
{
    "url": "https://apify.com",
    "stealthEngine": "camoufox",
    "title": "Apify: Full-stack web scraping and data extraction platform",
    "screenshotUrl": "https://api.apify.com/v2/key-value-stores/.../records/screenshot-0000",
    "statusCode": 200,
    "loadedAt": "2026-07-17T12:00:00+00:00",
    "error": null
}
```

The PNG itself is saved to the run's key-value store; `screenshotUrl` is its public URL (full-page screenshots of long pages can be many megabytes, well past the dataset item size limit, so they aren't inlined). You can download the dataset in JSON, HTML, CSV, or Excel format from the Output tab. If a URL fails to load, `error` is populated and the other fields are left `null`.

## Pricing

Screenshot Taker is pay-per-usage-of-your-own compute (Apify's default pricing model) - you pay for the compute units the run consumes. Camoufox and Patchright are heavier than plain Playwright, so expect slightly higher compute usage when using those engines. A single screenshot typically takes a few seconds; check the Apify [pricing page](https://apify.com/pricing) for current compute unit rates and free-tier limits.

## Tips

- Use `playwright` (no stealth) for sites without bot protection - it's the fastest and cheapest option.
- Use `camoufox` or `patchright` for sites that fingerprint headless Chromium.
- Increase `navigation_timeout_secs` for slow-loading pages, and use `wait_for_selector` or `wait_after_load_ms` for pages that render content asynchronously.
- Camoufox ignores `proxyConfiguration` - it manages its own network stack.

## FAQ, disclaimers, and support

Only screenshot pages you have the right to access, respecting each site's Terms of Service and `robots.txt`. If you hit a bug or want a feature, open an issue in the Actor's **Issues** tab. Need a custom scraping or automation solution? Reach out via [Apify Discord](https://discord.com/invite/jyEM2PRvMU) or the Apify [Actor development](https://apify.com/actors/development) services.
