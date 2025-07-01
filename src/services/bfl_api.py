"""
BFL.ai API service for image editing
"""

import asyncio
import base64
import aiohttp
from typing import Optional, Dict, Any, Tuple
from loguru import logger

from ..config import settings, BFL_ENDPOINTS
from ..models import ImageEdit, EditStatus


class BFLAPIError(Exception):
    """Custom exception for BFL.ai API errors"""
    pass


class BFLAPIService:
    """Service for interacting with BFL.ai API"""
    
    def __init__(self):
        self.base_url = settings.bfl_api_base_url
        self.api_key = settings.bfl_api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Start aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "accept": "application/json",
                    "x-key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def create_edit_request(self, 
                                prompt: str, 
                                input_image_base64: str,
                                aspect_ratio: str = "1:1",
                                output_format: str = "jpeg",
                                seed: Optional[int] = None,
                                safety_tolerance: int = 2) -> Tuple[str, str]:
        """
        Create an image edit request with BFL.ai API
        
        Returns:
            Tuple of (request_id, polling_url)
        """
        if not self.session:
            await self.start_session()
        
        url = f"{self.base_url}{BFL_ENDPOINTS['kontext_pro']}"
        
        payload = {
            "prompt": prompt,
            "input_image": input_image_base64,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "safety_tolerance": safety_tolerance
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        try:
            logger.info(f"Creating edit request with prompt: {prompt[:50]}...")
            
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"BFL.ai API error {response.status}: {error_text}")
                    raise BFLAPIError(f"API request failed with status {response.status}: {error_text}")
                
                data = await response.json()
                
                request_id = data.get("id")
                polling_url = data.get("polling_url")
                
                if not request_id or not polling_url:
                    logger.error(f"Invalid API response: {data}")
                    raise BFLAPIError("Invalid response from BFL.ai API")
                
                logger.info(f"Edit request created successfully: {request_id}")
                return request_id, polling_url
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error creating edit request: {e}")
            raise BFLAPIError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating edit request: {e}")
            raise BFLAPIError(f"Unexpected error: {e}")
    
    async def poll_result(self, polling_url: str) -> Dict[str, Any]:
        """
        Poll for edit result
        
        Returns:
            Dictionary with status and result data
        """
        if not self.session:
            await self.start_session()
        
        try:
            async with self.session.get(polling_url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Polling error {response.status}: {error_text}")
                    raise BFLAPIError(f"Polling failed with status {response.status}")
                
                data = await response.json()
                return data
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error polling result: {e}")
            raise BFLAPIError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error polling result: {e}")
            raise BFLAPIError(f"Unexpected error: {e}")
    
    async def wait_for_completion(self, 
                                polling_url: str, 
                                max_attempts: int = None,
                                polling_interval: float = None) -> Dict[str, Any]:
        """
        Wait for edit completion by polling
        
        Returns:
            Final result data
        """
        max_attempts = max_attempts or settings.max_polling_attempts
        polling_interval = polling_interval or settings.polling_interval_seconds
        
        attempt = 0
        
        while attempt < max_attempts:
            try:
                result = await self.poll_result(polling_url)
                status = result.get("status")
                
                logger.debug(f"Polling attempt {attempt + 1}: status = {status}")
                
                if status == "Ready":
                    logger.info("Edit completed successfully")
                    return result
                elif status in ["Error", "Failed"]:
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"Edit failed: {error_msg}")
                    raise BFLAPIError(f"Edit failed: {error_msg}")
                elif status in ["Pending", "Processing"]:
                    # Continue polling
                    await asyncio.sleep(polling_interval)
                    attempt += 1
                else:
                    logger.warning(f"Unexpected status: {status}")
                    await asyncio.sleep(polling_interval)
                    attempt += 1
                    
            except BFLAPIError:
                raise
            except Exception as e:
                logger.error(f"Error during polling: {e}")
                attempt += 1
                await asyncio.sleep(polling_interval)
        
        raise BFLAPIError(f"Edit timed out after {max_attempts} attempts")
    
    async def download_image(self, image_url: str) -> bytes:
        """
        Download image from signed URL
        
        Returns:
            Image bytes
        """
        if not self.session:
            await self.start_session()
        
        try:
            logger.info(f"Downloading image from: {image_url}")
            
            async with self.session.get(image_url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Image download error {response.status}: {error_text}")
                    raise BFLAPIError(f"Failed to download image: {response.status}")
                
                image_data = await response.read()
                logger.info(f"Downloaded image: {len(image_data)} bytes")
                return image_data
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error downloading image: {e}")
            raise BFLAPIError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading image: {e}")
            raise BFLAPIError(f"Unexpected error: {e}")
    
    async def process_edit_request(self, image_edit: ImageEdit, input_image_base64: str) -> str:
        """
        Process complete edit request from start to finish
        
        Returns:
            URL of the edited image
        """
        try:
            # Create edit request
            request_id, polling_url = await self.create_edit_request(
                prompt=image_edit.prompt,
                input_image_base64=input_image_base64,
                aspect_ratio=image_edit.aspect_ratio,
                output_format=image_edit.output_format,
                seed=image_edit.seed,
                safety_tolerance=image_edit.safety_tolerance
            )
            
            # Update image edit with BFL.ai details
            image_edit.start_processing(request_id, polling_url)
            
            # Wait for completion
            result = await self.wait_for_completion(polling_url)
            
            # Extract image URL
            edited_image_url = result.get("result", {}).get("sample")
            if not edited_image_url:
                raise BFLAPIError("No image URL in result")
            
            return edited_image_url
            
        except Exception as e:
            logger.error(f"Error processing edit request: {e}")
            raise
    
    @staticmethod
    def encode_image_to_base64(image_bytes: bytes) -> str:
        """
        Encode image bytes to base64 string
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode("utf-8")
    
    @staticmethod
    def validate_image_size(image_bytes: bytes) -> bool:
        """
        Validate image size against BFL.ai limits

        Args:
            image_bytes: Raw image bytes

        Returns:
            True if valid, False otherwise
        """
        size_mb = len(image_bytes) / (1024 * 1024)
        return size_mb <= settings.max_image_size_mb

    async def health_check(self) -> bool:
        """
        Check if BFL.ai API is accessible

        Returns:
            True if API is healthy, False otherwise
        """
        if not self.session:
            await self.start_session()

        try:
            # Simple test request to check API availability
            url = f"{self.base_url}/health"  # Assuming health endpoint exists
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"BFL.ai API health check failed: {e}")
            return False
