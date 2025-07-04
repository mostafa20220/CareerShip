import asyncio
import traceback
import uuid
import os

from playwright.async_api import async_playwright
from PIL import Image, ImageChops, ImageStat
import numpy as np
import requests
import json
import base64
import io

# Try to import SSIM, fall back gracefully if not available
try:
    from skimage.metrics import structural_similarity as ssim

    HAS_SSIM = True
except ImportError:
    HAS_SSIM = False

import logging
from django.conf import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreenshotService:
    @staticmethod
    async def capture_screenshot(
            url: str,
            width: int = 1920,
            height: int = 1080,
            timeout: int = 60000
    ) -> bytes:
        """
        Capture screenshot using Playwright (local or remote browser).
        Returns screenshot bytes.
        """
        # Try remote browser first (if configured)
        try:
            return await ScreenshotService._capture_remote_browser(url, width, height, timeout)
        except Exception as e:
            logger.error(f"Remote browser failed: {str(e)}")

        # Fallback to local Playwright
        try:
            return await ScreenshotService._capture_local_playwright(url, width, height, timeout)
        except Exception as e:
            logger.error(f"Local Playwright failed: {str(e)}")
            raise Exception(f"All screenshot methods failed. Last error: {str(e)}")

    @staticmethod
    async def _capture_remote_browser(
            url: str,
            width: int,
            height: int,
            timeout: int
    ) -> bytes:
        """Use remote browser service (browserless/chrome)"""
        browser_host = os.getenv('BROWSER_HOST', 'browser_service')
        browser_port = os.getenv('BROWSER_PORT', '3000')

        # Try HTTP API first (more reliable)
        try:
            browserless_url = f"http://{browser_host}:{browser_port}/screenshot"

            payload = {
                "url": url,
                "options": {
                    "fullPage": True,
                    "type": "png",

                },
                "viewport": {
                    "width": width,
                    "height": height
                },
                "gotoOptions": {
                    "waitUntil": "networkidle0",
                    "timeout": timeout
                }
            }

            logger.info(f"Sending request to {browserless_url} with payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                browserless_url,
                json=payload,
                timeout=timeout / 1000 + 10,  # Add extra time for HTTP request
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info("Successfully captured screenshot via HTTP API")
                return response.content
            else:
                logger.error(f"HTTP API returned status {response.status_code}: {response.text}")
                raise Exception(f"HTTP API failed with status {response.status_code}")

        except Exception as e:
            logger.error(f"HTTP API failed: {str(e)}")

        # Try CDP as fallback
        try:
            logger.info("Trying CDP connection as fallback")
            async with async_playwright() as p:
                browser = None
                try:
                    # Try to connect via CDP
                    browser = await p.chromium.connect_over_cdp(f"ws://{browser_host}:9222")
                    page = await browser.new_page()
                    await page.set_viewport_size({"width": width, "height": height})
                    await page.goto(url, timeout=timeout, wait_until='networkidle')
                    screenshot = await page.screenshot(full_page=True)
                    logger.info("Successfully captured screenshot via CDP")
                    return screenshot
                finally:
                    if browser:
                        await browser.close()
        except Exception as e:
            logger.error(f"CDP connection failed: {str(e)}")
            raise

    @staticmethod
    async def _capture_local_playwright(
            url: str,
            width: int = 1920,
            height: int = 1080,
            timeout: int = 60000
    ) -> bytes:
        """Use local Playwright browser"""
        logger.info("Attempting local Playwright screenshot")
        async with async_playwright() as p:
            browser = None
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding'
                    ]
                )
                page = await browser.new_page()
                await page.set_viewport_size({"width": width, "height": height})

                # Add user agent to avoid blocking
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })

                await page.goto(url, timeout=timeout, wait_until='domcontentloaded')

                # Wait a bit more for dynamic content
                await page.wait_for_timeout(2000)

                screenshot = await page.screenshot(full_page=True)

                # Save to disk temporarily if needed
                if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
                    screenshot_path = os.path.join(settings.MEDIA_ROOT, f"screenshot_{uuid.uuid4()}.png")
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot)

                logger.info("Successfully captured screenshot with local Playwright")
                return screenshot
            finally:
                if browser:
                    await browser.close()

    @staticmethod
    def compare_images(reference_image_path: str, screenshot_bytes: bytes) -> dict:
        """Compare images using multiple methods"""
        try:
            # Load reference image
            reference_image = Image.open(reference_image_path)

            # Load screenshot from bytes
            screenshot_image = Image.open(io.BytesIO(screenshot_bytes))

            # Ensure both images have the same size
            if reference_image.size != screenshot_image.size:
                screenshot_image = screenshot_image.resize(reference_image.size, Image.LANCZOS)

            # Convert to numpy arrays for SSIM if available
            if HAS_SSIM:
                ref_array = np.array(reference_image.convert('RGB'))
                screen_array = np.array(screenshot_image.convert('RGB'))

                # Calculate SSIM
                similarity_score = ssim(ref_array, screen_array, channel_axis=-1, data_range=255)
            else:
                similarity_score = None

            # Calculate histogram similarity
            ref_hist = reference_image.histogram()
            screen_hist = screenshot_image.histogram()

            # Calculate correlation coefficient
            hist_similarity = np.corrcoef(ref_hist, screen_hist)[0, 1]

            # PIL-based comparison (pixel difference)
            diff = ImageChops.difference(reference_image.convert('RGB'), screenshot_image.convert('RGB'))
            stat = ImageStat.Stat(diff)
            pil_similarity = 1 - (sum(stat.mean) / (255 * 3))

            logger.info(f"Similarity score: {similarity_score}, Histogram similarity: {hist_similarity}, PIL similarity: {pil_similarity}")

            return {
                'similarity_score': similarity_score,
                'histogram_similarity': hist_similarity,
                'pil_similarity': pil_similarity
            }

        except Exception as e:
            logger.error(f"Error comparing images: {str(e)}")
            return {'similarity_score': 0, 'histogram_similarity': 0, 'pil_similarity': 0}

    @staticmethod
    def compare_images_pil_only(reference_image_path: str, screenshot_bytes: bytes) -> dict:
        """Compare images using PIL only (fallback method)"""
        try:
            # Load reference image
            reference_image = Image.open(reference_image_path)

            # Load screenshot from bytes
            screenshot_image = Image.open(io.BytesIO(screenshot_bytes))

            # Ensure both images have the same size
            if reference_image.size != screenshot_image.size:
                screenshot_image = screenshot_image.resize(reference_image.size, Image.LANCZOS)

            # PIL-based comparison (pixel difference)
            diff = ImageChops.difference(reference_image.convert('RGB'), screenshot_image.convert('RGB'))
            stat = ImageStat.Stat(diff)
            pil_similarity = 1 - (sum(stat.mean) / (255 * 3))

            return {
                'pil_similarity': pil_similarity,
                'similarity_score': pil_similarity
            }

        except Exception as e:
            logger.error(f"Error comparing images with PIL: {str(e)}")
            return {'pil_similarity': 0, 'similarity_score': 0}


class FeedbackService:

    @staticmethod
    def generate_feedback(similarity_score: float) -> str:
        """Generate feedback based on similarity score"""
        if similarity_score >= 0.95:
            return "Excellent! Your implementation matches the design perfectly."
        elif similarity_score >= 0.85:
            return "Great work! Your implementation is very close to the design with minor differences."
        elif similarity_score >= 0.70:
            return "Good progress! There are some noticeable differences from the expected design. Please review the layout and styling."
        elif similarity_score >= 0.50:
            return "Your implementation has significant differences from the expected design. Please check the structure, layout, and styling carefully."
        else:
            return "Your implementation differs substantially from the expected design. Please review the requirements and reference design closely."

    @staticmethod
    def generate_detailed_feedback(comparison_result: dict) -> str:
        """Generate more detailed feedback using multiple similarity metrics"""
        similarity_score = comparison_result.get('similarity_score', 0)
        hist_similarity = comparison_result.get('histogram_similarity', 0)
        pil_similarity = comparison_result.get('pil_similarity', 0)

        # Use the highest similarity score for feedback
        best_score = max(similarity_score, hist_similarity or 0, pil_similarity or 0)

        base_feedback = FeedbackService.generate_feedback(best_score)

        print(base_feedback)

        # Add specific insights
        insights = []

        if hist_similarity and hist_similarity < similarity_score:
            insights.append("The color scheme differs from the expected design.")
        elif hist_similarity and hist_similarity > similarity_score:
            insights.append("The color scheme is accurate, but layout differs.")

        if pil_similarity and pil_similarity < 0.7:
            insights.append("There are significant visual differences in the overall appearance.")

        if insights:
            return f"{base_feedback}\n\nSpecific insights: {' '.join(insights)}"

        return base_feedback