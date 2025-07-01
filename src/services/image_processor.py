"""
Image processing service for handling image operations
"""

import io
import os
import tempfile
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageFile
import magic
from loguru import logger

from ..config import settings, SUPPORTED_IMAGE_FORMATS, MAX_IMAGE_PIXELS


# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageProcessingError(Exception):
    """Custom exception for image processing errors"""
    pass


class ImageProcessor:
    """Service for image processing operations"""
    
    @staticmethod
    def validate_image(image_bytes: bytes) -> Dict[str, Any]:
        """
        Validate image format, size, and properties
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with validation results and image info
        """
        try:
            # Check file size
            size_mb = len(image_bytes) / (1024 * 1024)
            if size_mb > settings.max_image_size_mb:
                raise ImageProcessingError(
                    f"Image too large: {size_mb:.1f}MB (max: {settings.max_image_size_mb}MB)"
                )
            
            # Detect MIME type
            mime_type = magic.from_buffer(image_bytes, mime=True)
            if not mime_type.startswith('image/'):
                raise ImageProcessingError(f"Invalid file type: {mime_type}")
            
            # Open and validate image with PIL
            try:
                image = Image.open(io.BytesIO(image_bytes))
                image.verify()  # Verify image integrity
                
                # Re-open for getting info (verify() closes the image)
                image = Image.open(io.BytesIO(image_bytes))
                
                # Check image format
                if image.format not in SUPPORTED_IMAGE_FORMATS:
                    raise ImageProcessingError(
                        f"Unsupported format: {image.format} "
                        f"(supported: {', '.join(SUPPORTED_IMAGE_FORMATS)})"
                    )
                
                # Check image dimensions and pixel count
                width, height = image.size
                pixel_count = width * height
                
                if pixel_count > MAX_IMAGE_PIXELS:
                    raise ImageProcessingError(
                        f"Image too large: {pixel_count:,} pixels "
                        f"(max: {MAX_IMAGE_PIXELS:,} pixels)"
                    )
                
                return {
                    "valid": True,
                    "format": image.format,
                    "mode": image.mode,
                    "size": (width, height),
                    "pixel_count": pixel_count,
                    "file_size_mb": size_mb,
                    "mime_type": mime_type
                }
                
            except Exception as e:
                raise ImageProcessingError(f"Invalid image file: {e}")
                
        except ImageProcessingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating image: {e}")
            raise ImageProcessingError(f"Image validation failed: {e}")
    
    @staticmethod
    def optimize_image(image_bytes: bytes, 
                      max_size_mb: Optional[float] = None,
                      target_format: str = "JPEG") -> bytes:
        """
        Optimize image for processing
        
        Args:
            image_bytes: Raw image bytes
            max_size_mb: Maximum file size in MB
            target_format: Target image format
            
        Returns:
            Optimized image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary (for JPEG)
            if target_format.upper() == "JPEG" and image.mode in ("RGBA", "P", "LA"):
                # Create white background for transparency
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background
            
            # Start with high quality
            quality = 95
            max_size_bytes = (max_size_mb or settings.max_image_size_mb) * 1024 * 1024
            
            while quality > 10:
                output = io.BytesIO()
                
                # Save with current quality
                save_kwargs = {"format": target_format, "optimize": True}
                if target_format.upper() == "JPEG":
                    save_kwargs["quality"] = quality
                
                image.save(output, **save_kwargs)
                output_bytes = output.getvalue()
                
                # Check if size is acceptable
                if len(output_bytes) <= max_size_bytes:
                    logger.info(f"Image optimized: {len(output_bytes)} bytes at quality {quality}")
                    return output_bytes
                
                # Reduce quality and try again
                quality -= 10
            
            # If still too large, resize the image
            logger.warning("Image still too large after quality reduction, resizing...")
            return ImageProcessor._resize_and_optimize(image, max_size_bytes, target_format)
            
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            raise ImageProcessingError(f"Image optimization failed: {e}")
    
    @staticmethod
    def _resize_and_optimize(image: Image.Image, 
                           max_size_bytes: int, 
                           target_format: str) -> bytes:
        """
        Resize image to fit size constraints
        
        Args:
            image: PIL Image object
            max_size_bytes: Maximum file size in bytes
            target_format: Target image format
            
        Returns:
            Resized and optimized image bytes
        """
        original_size = image.size
        scale_factor = 0.9
        
        while scale_factor > 0.1:
            # Calculate new size
            new_width = int(original_size[0] * scale_factor)
            new_height = int(original_size[1] * scale_factor)
            
            # Resize image
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Try to save with good quality
            output = io.BytesIO()
            save_kwargs = {"format": target_format, "optimize": True}
            if target_format.upper() == "JPEG":
                save_kwargs["quality"] = 85
            
            resized_image.save(output, **save_kwargs)
            output_bytes = output.getvalue()
            
            if len(output_bytes) <= max_size_bytes:
                logger.info(f"Image resized to {new_width}x{new_height}: {len(output_bytes)} bytes")
                return output_bytes
            
            scale_factor -= 0.1
        
        raise ImageProcessingError("Unable to optimize image to required size")
    
    @staticmethod
    def get_image_info(image_bytes: bytes) -> Dict[str, Any]:
        """
        Get detailed image information
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with image information
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.size[0],
                "height": image.size[1],
                "pixel_count": image.size[0] * image.size[1],
                "file_size_bytes": len(image_bytes),
                "file_size_mb": len(image_bytes) / (1024 * 1024),
                "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info,
                "color_mode": image.mode,
                "aspect_ratio": image.size[0] / image.size[1]
            }
            
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            raise ImageProcessingError(f"Failed to get image info: {e}")
    
    @staticmethod
    def save_temp_image(image_bytes: bytes, suffix: str = ".jpg") -> str:
        """
        Save image to temporary file
        
        Args:
            image_bytes: Raw image bytes
            suffix: File extension
            
        Returns:
            Path to temporary file
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            logger.debug(f"Saved temporary image: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error saving temporary image: {e}")
            raise ImageProcessingError(f"Failed to save temporary image: {e}")
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """
        Clean up temporary file
        
        Args:
            file_path: Path to temporary file
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")
    
    @staticmethod
    def convert_format(image_bytes: bytes, target_format: str) -> bytes:
        """
        Convert image to different format
        
        Args:
            image_bytes: Raw image bytes
            target_format: Target format (JPEG, PNG, WEBP)
            
        Returns:
            Converted image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Handle transparency for JPEG
            if target_format.upper() == "JPEG" and image.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background
            
            output = io.BytesIO()
            save_kwargs = {"format": target_format, "optimize": True}
            
            if target_format.upper() == "JPEG":
                save_kwargs["quality"] = 95
            elif target_format.upper() == "PNG":
                save_kwargs["compress_level"] = 6
            
            image.save(output, **save_kwargs)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting image format: {e}")
            raise ImageProcessingError(f"Format conversion failed: {e}")
