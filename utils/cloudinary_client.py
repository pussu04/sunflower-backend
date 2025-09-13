import cloudinary
import cloudinary.uploader
import cloudinary.api
import cv2
import numpy as np
from PIL import Image
import io
import base64
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=getenv("CLOUD_NAME"),
    api_key=getenv("CLOUD_API_KEY"),
    api_secret=getenv("CLOUD_API_SECRET"),
    secure=True
)

class CloudinaryClient:
    def __init__(self):
        self.folder_name = "uploaded_ml_images"
        
    def upload_image(self, image_data, filename="image.png", image_type="analysis"):
        """
        Upload image to Cloudinary with compression if needed
        
        Args:
            image_data: Image data (numpy array, PIL Image, or bytes)
            filename: Name for the uploaded file (without extension)
            image_type: Type of image (original, cropped, threshold, processed)
            
        Returns:
            dict: Upload response with URL and file info
        """
        try:
            # Convert and compress image data to bytes if needed
            if isinstance(image_data, np.ndarray):
                # Convert numpy array to bytes
                _, buffer = cv2.imencode('.png', image_data)
                image_bytes = buffer.tobytes()
            elif isinstance(image_data, Image.Image):
                # Compress PIL Image if too large
                img = image_data.copy()
                
                # Resize if image is too large (reduce dimensions)
                max_dimension = 2048
                if img.width > max_dimension or img.height > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    print(f"🔄 Resized image from {image_data.size} to {img.size}")
                
                # Try different quality levels to stay under 10MB
                for quality in [85, 70, 60, 50, 40]:
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=quality, optimize=True)
                    image_bytes = buffer.getvalue()
                    
                    # Check if under 10MB (10485760 bytes)
                    if len(image_bytes) <= 10485760:
                        print(f"✅ Compressed image to {len(image_bytes)} bytes at quality {quality}")
                        break
                else:
                    # If still too large, use PNG with maximum compression
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG', optimize=True)
                    image_bytes = buffer.getvalue()
                    print(f"⚠️ Using PNG compression: {len(image_bytes)} bytes")
                    
            elif isinstance(image_data, bytes):
                image_bytes = image_data
            else:
                raise ValueError("Unsupported image data type")
            
            # Create a unique public_id (fix double folder issue)
            public_id = f"{filename}_{image_type}"
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_bytes,
                public_id=public_id,
                folder=self.folder_name,
                resource_type="image",
                format="png",
                overwrite=True,
                transformation=[
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            
            result = {
                "url": upload_result.get("secure_url", ""),
                "public_id": upload_result.get("public_id", ""),
                "name": filename,
                "size": len(image_bytes),
                "format": upload_result.get("format", "png"),
                "width": upload_result.get("width", 0),
                "height": upload_result.get("height", 0)
            }
            
            print(f"✅ Image uploaded to Cloudinary: {result['url']}")
            return result
            
        except Exception as e:
            print(f"❌ Cloudinary upload error: {e}")
            return None
    
    
    def upload_sunflower_analysis_image(self, original_image, user_id):
        """
        Upload sunflower analysis image
        
        Args:
            original_image: Original sunflower leaf image
            user_id: User ID for unique naming
            
        Returns:
            dict: URL for uploaded image
        """
        import time
        timestamp = int(time.time())
        base_filename = f"sunflower_{user_id}_{timestamp}"
        
        # Upload original image
        original_result = self.upload_image(
            original_image, 
            base_filename, 
            "original"
        )
        
        return {
            'original_image_url': original_result['url'] if original_result else None,
            'image_info': original_result if original_result else None
        }
    
    def delete_image(self, public_id):
        """
        Delete image from Cloudinary
        
        Args:
            public_id: Public ID of the image to delete
            
        Returns:
            bool: Success status
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"❌ Error deleting image: {e}")
            return False
    
    def get_image_info(self, public_id):
        """
        Get information about an uploaded image
        
        Args:
            public_id: Public ID of the image
            
        Returns:
            dict: Image information
        """
        try:
            result = cloudinary.api.resource(public_id)
            return {
                "url": result.get("secure_url", ""),
                "format": result.get("format", ""),
                "width": result.get("width", 0),
                "height": result.get("height", 0),
                "size": result.get("bytes", 0),
                "created_at": result.get("created_at", "")
            }
        except Exception as e:
            print(f"❌ Error getting image info: {e}")
            return None

# Global instance
cloudinary_client = CloudinaryClient()