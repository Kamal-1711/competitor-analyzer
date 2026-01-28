"""
Screenshot capture and management for Web-Spy.
Handles full-page screenshots, thumbnails, and visual comparisons.
"""

import os
import hashlib
import asyncio
from typing import Optional, Tuple
from datetime import datetime
from pathlib import Path
from io import BytesIO
from uuid import UUID

from PIL import Image
from loguru import logger


class ScreenshotManager:
    """
    Manages screenshot capture, storage, and comparison.
    Features:
    - Full-page and viewport screenshots
    - Thumbnail generation
    - Visual diff detection
    - Cloud storage ready (S3 compatible)
    """
    
    def __init__(self, storage_path: str = "screenshots"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Thumbnail settings
        self.thumbnail_size = (400, 300)
        self.diff_threshold = 0.05  # 5% difference threshold
    
    def _get_storage_path(self, competitor_id: UUID, scan_id: UUID) -> Path:
        """Get storage path for a specific scan."""
        path = self.storage_path / str(competitor_id) / str(scan_id)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _generate_filename(self, url: str, suffix: str = "") -> str:
        """Generate a unique filename for a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{url_hash}_{timestamp}{suffix}.png"
    
    async def capture_full_page(
        self,
        page,
        competitor_id: UUID,
        scan_id: UUID,
        url: str
    ) -> Optional[str]:
        """Capture a full-page screenshot."""
        try:
            storage = self._get_storage_path(competitor_id, scan_id)
            filename = self._generate_filename(url, "_full")
            filepath = storage / filename
            
            # Take full page screenshot
            await page.screenshot(
                path=str(filepath),
                full_page=True,
                type="png"
            )
            
            logger.debug(f"Captured full-page screenshot: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.warning(f"Failed to capture full-page screenshot: {e}")
            return None
    
    async def capture_viewport(
        self,
        page,
        competitor_id: UUID,
        scan_id: UUID,
        url: str
    ) -> Optional[str]:
        """Capture a viewport screenshot."""
        try:
            storage = self._get_storage_path(competitor_id, scan_id)
            filename = self._generate_filename(url, "_viewport")
            filepath = storage / filename
            
            # Take viewport screenshot
            await page.screenshot(
                path=str(filepath),
                full_page=False,
                type="png"
            )
            
            logger.debug(f"Captured viewport screenshot: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.warning(f"Failed to capture viewport screenshot: {e}")
            return None
    
    async def capture_element(
        self,
        page,
        selector: str,
        competitor_id: UUID,
        scan_id: UUID,
        url: str
    ) -> Optional[str]:
        """Capture a screenshot of a specific element."""
        try:
            element = await page.query_selector(selector)
            if not element:
                return None
            
            storage = self._get_storage_path(competitor_id, scan_id)
            filename = self._generate_filename(url, f"_element_{selector[:10]}")
            filepath = storage / filename
            
            await element.screenshot(path=str(filepath))
            
            logger.debug(f"Captured element screenshot: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.warning(f"Failed to capture element screenshot: {e}")
            return None
    
    def generate_thumbnail(
        self,
        source_path: str,
        size: Optional[Tuple[int, int]] = None
    ) -> Optional[str]:
        """Generate a thumbnail from a screenshot."""
        try:
            size = size or self.thumbnail_size
            source = Path(source_path)
            
            if not source.exists():
                return None
            
            thumbnail_path = source.parent / f"{source.stem}_thumb{source.suffix}"
            
            with Image.open(source) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, optimize=True)
            
            return str(thumbnail_path)
            
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")
            return None
    
    def compare_screenshots(
        self,
        path1: str,
        path2: str
    ) -> Tuple[float, Optional[str]]:
        """
        Compare two screenshots and return similarity score.
        Returns: (similarity_score, diff_image_path or None)
        """
        try:
            with Image.open(path1) as img1, Image.open(path2) as img2:
                # Resize to same dimensions
                min_width = min(img1.width, img2.width)
                min_height = min(img1.height, img2.height)
                
                img1 = img1.resize((min_width, min_height))
                img2 = img2.resize((min_width, min_height))
                
                # Convert to RGB
                img1 = img1.convert('RGB')
                img2 = img2.convert('RGB')
                
                # Calculate pixel differences
                pixels1 = list(img1.getdata())
                pixels2 = list(img2.getdata())
                
                if len(pixels1) != len(pixels2):
                    return 0.0, None
                
                total_diff = 0
                diff_pixels = []
                
                for p1, p2 in zip(pixels1, pixels2):
                    r_diff = abs(p1[0] - p2[0])
                    g_diff = abs(p1[1] - p2[1])
                    b_diff = abs(p1[2] - p2[2])
                    
                    pixel_diff = (r_diff + g_diff + b_diff) / 3 / 255
                    total_diff += pixel_diff
                    
                    # Create diff pixel (highlight differences in red)
                    if pixel_diff > 0.1:
                        diff_pixels.append((255, 0, 0))
                    else:
                        diff_pixels.append(p2)
                
                similarity = 1 - (total_diff / len(pixels1))
                
                # Generate diff image if significant changes
                diff_path = None
                if similarity < (1 - self.diff_threshold):
                    diff_img = Image.new('RGB', (min_width, min_height))
                    diff_img.putdata(diff_pixels)
                    diff_path = Path(path2).parent / f"{Path(path2).stem}_diff.png"
                    diff_img.save(diff_path)
                    diff_path = str(diff_path)
                
                return similarity, diff_path
                
        except Exception as e:
            logger.warning(f"Failed to compare screenshots: {e}")
            return 0.0, None
    
    def cleanup_old_screenshots(
        self,
        competitor_id: UUID,
        keep_last_n: int = 5
    ) -> int:
        """Remove old screenshots, keeping only the most recent."""
        comp_path = self.storage_path / str(competitor_id)
        
        if not comp_path.exists():
            return 0
        
        # Get all scan directories
        scan_dirs = sorted(
            [d for d in comp_path.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True
        )
        
        removed = 0
        for scan_dir in scan_dirs[keep_last_n:]:
            try:
                for file in scan_dir.iterdir():
                    file.unlink()
                scan_dir.rmdir()
                removed += 1
            except Exception as e:
                logger.warning(f"Failed to remove {scan_dir}: {e}")
        
        return removed
    
    async def capture_with_scroll(
        self,
        page,
        competitor_id: UUID,
        scan_id: UUID,
        url: str,
        scroll_steps: int = 3
    ) -> Optional[str]:
        """
        Capture screenshots while scrolling (useful for lazy-loaded content).
        Stitches them together into one image.
        """
        try:
            storage = self._get_storage_path(competitor_id, scan_id)
            filename = self._generate_filename(url, "_scrolled")
            filepath = storage / filename
            
            # Get page dimensions
            dimensions = await page.evaluate("""
                () => ({
                    width: Math.max(document.body.scrollWidth, document.body.clientWidth),
                    height: Math.max(document.body.scrollHeight, document.body.clientHeight),
                    viewportHeight: window.innerHeight
                })
            """)
            
            viewport_height = dimensions['viewportHeight']
            scroll_height = dimensions['height']
            
            screenshots = []
            
            # Scroll and capture
            for i in range(scroll_steps):
                scroll_position = int(i * viewport_height * 0.8)
                
                await page.evaluate(f"window.scrollTo(0, {scroll_position})")
                await asyncio.sleep(0.5)  # Wait for lazy content
                
                screenshot_bytes = await page.screenshot(type="png")
                img = Image.open(BytesIO(screenshot_bytes))
                screenshots.append(img)
                
                if scroll_position + viewport_height >= scroll_height:
                    break
            
            if not screenshots:
                return None
            
            # Stitch images vertically
            total_height = sum(img.height for img in screenshots)
            max_width = max(img.width for img in screenshots)
            
            stitched = Image.new('RGB', (max_width, total_height))
            y_offset = 0
            
            for img in screenshots:
                stitched.paste(img, (0, y_offset))
                y_offset += img.height
            
            stitched.save(filepath)
            
            logger.debug(f"Captured scrolled screenshot: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.warning(f"Failed to capture scrolled screenshot: {e}")
            return None


class VisualDiffGenerator:
    """
    Generate visual diffs between page versions.
    Useful for detecting layout and design changes.
    """
    
    @staticmethod
    def generate_heatmap(
        path1: str,
        path2: str,
        output_path: str
    ) -> Optional[str]:
        """Generate a heatmap showing differences between two screenshots."""
        try:
            with Image.open(path1) as img1, Image.open(path2) as img2:
                # Resize to match
                size = (min(img1.width, img2.width), min(img1.height, img2.height))
                img1 = img1.resize(size).convert('RGB')
                img2 = img2.resize(size).convert('RGB')
                
                # Create heatmap
                heatmap = Image.new('RGBA', size)
                pixels1 = img1.load()
                pixels2 = img2.load()
                heatmap_pixels = heatmap.load()
                
                for x in range(size[0]):
                    for y in range(size[1]):
                        p1 = pixels1[x, y]
                        p2 = pixels2[x, y]
                        
                        diff = sum(abs(a - b) for a, b in zip(p1, p2)) / 3 / 255
                        
                        if diff > 0.1:
                            # Red for changes
                            intensity = int(min(255, diff * 512))
                            heatmap_pixels[x, y] = (255, 0, 0, intensity)
                        else:
                            # Semi-transparent original
                            heatmap_pixels[x, y] = (*p2, 128)
                
                heatmap.save(output_path)
                return output_path
                
        except Exception as e:
            logger.warning(f"Failed to generate heatmap: {e}")
            return None
