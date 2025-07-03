# projects/services/screenshot_service.py

import asyncio
from playwright.async_api import async_playwright
from PIL import Image, ImageChops, ImageStat
import numpy as np
from skimage.metrics import structural_similarity as ssim
import io


class ScreenshotService:

    @staticmethod
    async def capture_screenshot(url: str, width: int = 1920, height: int = 1080, timeout: int = 30000):
        """Capture screenshot of a webpage using Playwright"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_viewport_size({"width": width, "height": height})

                # Navigate to the URL with timeout
                await page.goto(url, timeout=timeout, wait_until='networkidle')

                # Take screenshot
                screenshot = await page.screenshot(full_page=True)
                await browser.close()

                return screenshot

        except Exception as e:
            raise Exception(f"Failed to capture screenshot: {str(e)}")

    @staticmethod
    def compare_images(reference_image_path: str, screenshot_bytes: bytes):
        """Compare reference image with screenshot using PIL and SSIM"""
        try:
            # Load reference image using PIL
            reference = Image.open(reference_image_path)
            
            # Convert screenshot bytes to PIL Image
            screenshot = Image.open(io.BytesIO(screenshot_bytes))

            # Convert to RGB if needed (handles different formats)
            if reference.mode != 'RGB':
                reference = reference.convert('RGB')
            if screenshot.mode != 'RGB':
                screenshot = screenshot.convert('RGB')

            # Resize images to same dimensions if needed
            if reference.size != screenshot.size:
                # Resize to match the smaller dimension to avoid quality loss
                target_size = (
                    min(reference.size[0], screenshot.size[0]),
                    min(reference.size[1], screenshot.size[1])
                )
                reference = reference.resize(target_size, Image.Resampling.LANCZOS)
                screenshot = screenshot.resize(target_size, Image.Resampling.LANCZOS)

            # Convert PIL images to numpy arrays for SSIM calculation
            reference_array = np.array(reference)
            screenshot_array = np.array(screenshot)

            # Convert to grayscale for SSIM comparison
            reference_gray = np.dot(reference_array[...,:3], [0.2989, 0.5870, 0.1140])
            screenshot_gray = np.dot(screenshot_array[...,:3], [0.2989, 0.5870, 0.1140])

            # Calculate SSIM
            similarity_score, diff = ssim(reference_gray, screenshot_gray, full=True)

            # Create difference image using PIL
            diff_pil = ScreenshotService._create_difference_image_pil(reference, screenshot)

            # Alternative similarity calculation using PIL (if SSIM fails)
            pil_similarity = ScreenshotService._calculate_pil_similarity(reference, screenshot)

            return {
                'similarity_score': similarity_score,
                'pil_similarity': pil_similarity,
                'difference_image': diff,
                'difference_image_pil': diff_pil,
                'reference_processed': reference,
                'screenshot_processed': screenshot
            }

        except Exception as e:
            raise Exception(f"Failed to compare images: {str(e)}")

    @staticmethod
    def _create_difference_image_pil(img1: Image.Image, img2: Image.Image) -> Image.Image:
        """Create a difference image using PIL"""
        try:
            # Calculate absolute difference
            diff = ImageChops.difference(img1, img2)
            
            # Enhance the difference for better visibility
            # Convert to grayscale and then back to RGB for consistent output
            diff_gray = diff.convert('L')
            diff_enhanced = ImageChops.multiply(diff_gray, diff_gray.point(lambda x: x * 2))
            
            # Convert back to RGB
            diff_rgb = diff_enhanced.convert('RGB')
            
            return diff_rgb
            
        except Exception as e:
            # Return a blank image if difference calculation fails
            return Image.new('RGB', img1.size, (0, 0, 0))

    @staticmethod
    def _calculate_pil_similarity(img1: Image.Image, img2: Image.Image) -> float:
        """Calculate similarity using PIL's built-in methods as fallback"""
        try:
            # Calculate difference using PIL
            diff = ImageChops.difference(img1, img2)
            
            # Calculate statistics
            stat = ImageStat.Stat(diff)
            
            # Get mean difference across all channels
            mean_diff = sum(stat.mean) / len(stat.mean)
            
            # Convert to similarity score (0-1, where 1 is identical)
            # 255 is max possible difference per channel
            similarity = 1 - (mean_diff / 255)
            
            return max(0, min(1, similarity))  # Clamp between 0 and 1
            
        except Exception:
            return 0.0

    @staticmethod
    def compare_images_pil_only(reference_image_path: str, screenshot_bytes: bytes):
        """Compare images using only PIL (no SSIM dependency)"""
        try:
            # Load reference image using PIL
            reference = Image.open(reference_image_path)
            
            # Convert screenshot bytes to PIL Image
            screenshot = Image.open(io.BytesIO(screenshot_bytes))

            # Convert to RGB if needed
            if reference.mode != 'RGB':
                reference = reference.convert('RGB')
            if screenshot.mode != 'RGB':
                screenshot = screenshot.convert('RGB')

            # Resize images to same dimensions if needed
            if reference.size != screenshot.size:
                target_size = (
                    min(reference.size[0], screenshot.size[0]),
                    min(reference.size[1], screenshot.size[1])
                )
                reference = reference.resize(target_size, Image.Resampling.LANCZOS)
                screenshot = screenshot.resize(target_size, Image.Resampling.LANCZOS)

            # Calculate similarity using PIL methods
            similarity_score = ScreenshotService._calculate_pil_similarity(reference, screenshot)
            
            # Create difference image
            diff_image = ScreenshotService._create_difference_image_pil(reference, screenshot)

            # Calculate histogram similarity as additional metric
            hist_similarity = ScreenshotService._calculate_histogram_similarity(reference, screenshot)

            return {
                'similarity_score': similarity_score,
                'histogram_similarity': hist_similarity,
                'difference_image_pil': diff_image,
                'reference_processed': reference,
                'screenshot_processed': screenshot
            }

        except Exception as e:
            raise Exception(f"Failed to compare images with PIL: {str(e)}")

    @staticmethod
    def _calculate_histogram_similarity(img1: Image.Image, img2: Image.Image) -> float:
        """Calculate similarity based on color histograms"""
        try:
            # Get histograms for each channel
            hist1_r = img1.split()[0].histogram()
            hist1_g = img1.split()[1].histogram()
            hist1_b = img1.split()[2].histogram()
            
            hist2_r = img2.split()[0].histogram()
            hist2_g = img2.split()[1].histogram()
            hist2_b = img2.split()[2].histogram()
            
            # Calculate correlation for each channel
            def correlation(h1, h2):
                # Normalize histograms
                h1_norm = [x / sum(h1) for x in h1]
                h2_norm = [x / sum(h2) for x in h2]
                
                # Calculate correlation coefficient
                mean1 = sum(h1_norm) / len(h1_norm)
                mean2 = sum(h2_norm) / len(h2_norm)
                
                numerator = sum((h1_norm[i] - mean1) * (h2_norm[i] - mean2) for i in range(len(h1_norm)))
                
                sum_sq1 = sum((h1_norm[i] - mean1) ** 2 for i in range(len(h1_norm)))
                sum_sq2 = sum((h2_norm[i] - mean2) ** 2 for i in range(len(h2_norm)))
                
                denominator = (sum_sq1 * sum_sq2) ** 0.5
                
                if denominator == 0:
                    return 0
                
                return numerator / denominator
            
            # Average correlation across channels
            corr_r = correlation(hist1_r, hist2_r)
            corr_g = correlation(hist1_g, hist2_g)
            corr_b = correlation(hist1_b, hist2_b)
            
            avg_correlation = (corr_r + corr_g + corr_b) / 3
            
            # Convert to similarity score (0-1)
            return max(0, min(1, (avg_correlation + 1) / 2))
            
        except Exception:
            return 0.0


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