from __future__ import annotations

import base64
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

from apify import Actor


@asynccontextmanager
async def playwright_browser(*, headless: bool, proxy: dict | None):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, proxy=proxy)
        try:
            yield browser
        finally:
            await browser.close()


@asynccontextmanager
async def playwright_stealth_browser(*, headless: bool, proxy: dict | None):
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=headless, proxy=proxy)
        try:
            yield browser
        finally:
            await browser.close()


@asynccontextmanager
async def patchright_browser(*, headless: bool, proxy: dict | None):
    from patchright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, proxy=proxy)
        try:
            yield browser
        finally:
            await browser.close()


@asynccontextmanager
async def camoufox_browser(*, headless: bool, proxy: dict | None):
    # Camoufox (Firefox-based) manages its own fingerprinting/network stack;
    # proxy is passed through in the same {'server', 'username', 'password'} shape.
    from camoufox.async_api import AsyncCamoufox

    async with AsyncCamoufox(headless=headless, proxy=proxy) as browser:
        yield browser


ENGINE_FACTORIES = {
    'playwright': playwright_browser,
    'playwright_stealth': playwright_stealth_browser,
    'patchright': patchright_browser,
    'camoufox': camoufox_browser,
}


def build_proxy_config(proxy_url: str | None) -> dict | None:
    """Convert an Apify proxy URL into the {'server', 'username', 'password'} shape Playwright/Camoufox expect."""
    if not proxy_url:
        return None

    parsed = urlparse(proxy_url)
    proxy: dict = {'server': f'{parsed.scheme}://{parsed.hostname}:{parsed.port}'}
    if parsed.username:
        proxy['username'] = parsed.username
    if parsed.password:
        proxy['password'] = parsed.password
    return proxy


async def main() -> None:
    """Define a main entry point for the Apify Actor.

    This coroutine is executed using `asyncio.run()`, so it must remain an asynchronous function for proper execution.
    Asynchronous execution is required for communication with Apify platform, and it also enhances performance in
    the field of web scraping significantly.
    """
    async with Actor:
        actor_input = await Actor.get_input() or {}

        start_urls = [item.get('url') for item in actor_input.get('start_urls', []) if item.get('url')]
        if not start_urls:
            Actor.log.info('No start URLs specified in Actor input, exiting...')
            await Actor.exit()
            return

        stealth_engine = actor_input.get('stealth_engine', 'camoufox')
        if stealth_engine not in ENGINE_FACTORIES:
            raise ValueError(f'Unknown stealth_engine: {stealth_engine!r}, expected one of {list(ENGINE_FACTORIES)}')

        full_page = actor_input.get('full_page', True)
        viewport = {
            'width': actor_input.get('viewport_width', 1920),
            'height': actor_input.get('viewport_height', 1080),
        }
        wait_for_selector = actor_input.get('wait_for_selector') or None
        wait_after_load_ms = actor_input.get('wait_after_load_ms', 0)
        navigation_timeout_ms = actor_input.get('navigation_timeout_secs', 60) * 1000

        proxy_url = None
        proxy_config_input = actor_input.get('proxyConfiguration')
        if proxy_config_input and proxy_config_input.get('useApifyProxy'):
            if stealth_engine == 'camoufox':
                Actor.log.warning('Camoufox handles its own network stack; proxyConfiguration is ignored for it.')
            else:
                proxy_configuration = await Actor.create_proxy_configuration(actor_proxy_input=proxy_config_input)
                if proxy_configuration:
                    proxy_url = await proxy_configuration.new_url()
        proxy = build_proxy_config(proxy_url) if stealth_engine != 'camoufox' else None

        Actor.log.info(f'Using stealth engine: {stealth_engine}')

        browser_factory = ENGINE_FACTORIES[stealth_engine]
        async with browser_factory(headless=True, proxy=proxy) as browser:
            for url in start_urls:
                Actor.log.info(f'Screenshotting {url}...')
                result = {
                    'url': url,
                    'stealthEngine': stealth_engine,
                    'title': None,
                    'screenshotUrl': None,
                    'statusCode': None,
                    'loadedAt': datetime.now(timezone.utc).isoformat(),
                    'error': None,
                }

                context = await browser.new_context(viewport=viewport)
                try:
                    page = await context.new_page()
                    response = await page.goto(url, timeout=navigation_timeout_ms, wait_until='load')
                    result['statusCode'] = response.status if response else None

                    if wait_for_selector:
                        await page.wait_for_selector(wait_for_selector, timeout=navigation_timeout_ms)

                    if wait_after_load_ms:
                        await page.wait_for_timeout(wait_after_load_ms)

                    result['title'] = await page.title()
                    screenshot_bytes = await page.screenshot(full_page=full_page)
                    result['screenshotUrl'] = f'data:image/png;base64,{base64.b64encode(screenshot_bytes).decode()}'
                except Exception as exc:  # noqa: BLE001 - keep going with the next URL, record the failure
                    Actor.log.exception(f'Failed to screenshot {url}')
                    result['error'] = str(exc)
                finally:
                    await context.close()

                await Actor.push_data(result)
