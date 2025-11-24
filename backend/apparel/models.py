from django.db import models
from django.core.validators import MinValueValidator
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import os


def apparel_image_upload_path(instance, filename):
    """Generate upload path for apparel images."""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create new filename using product title
    new_filename = f"{instance.title.replace(' ', '_')}_{instance.category}.{ext}"
    return os.path.join('apparel', new_filename)


class ApparelProduct(models.Model):
    """Model for apparel products."""
    
    CATEGORY_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available Now'),
        ('OUT_OF_STOCK', 'Out of Stock'),
    ]
    
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text="Product name/title"
    )
    
    description = models.TextField(
        help_text="Detailed product description"
    )
    
    image = models.ImageField(
        upload_to=apparel_image_upload_path,
        help_text="Upload product image (JPG, PNG)"
    )
    
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='MALE',
        help_text="Target audience category"
    )
    
    sizes = models.JSONField(
        default=list,
        help_text="Available sizes (S, M, L, XL, XXL)"
    )
    
    mrp_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum Retail Price in INR"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='AVAILABLE',
        help_text="Product availability status"
    )
    
    whatsapp_message = models.TextField(
        blank=True,
        help_text="Pre-filled WhatsApp message for orders"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Display this product on the website"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Apparel Product'
        verbose_name_plural = 'Apparel Products'
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"
    
    def get_status_color(self):
        """Get status badge color for frontend."""
        color_map = {
            'AVAILABLE': 'bg-green-500',
            'OUT_OF_STOCK': 'bg-red-500',
        }
        return color_map.get(self.status, 'bg-gray-500')
    
    def optimize_image(self):
        """Optimize uploaded image by resizing and compressing."""
        if not self.image:
            return
        
        # Open the image
        img = Image.open(self.image)
        
        # Convert RGBA to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate new dimensions (max width: 1200px, maintain aspect ratio)
        max_width = 1200
        if img.width > max_width:
            # Calculate proportional height
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to BytesIO with optimization
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        # Get the original filename and change extension to .jpg
        original_name = self.image.name
        name_without_ext = os.path.splitext(os.path.basename(original_name))[0]
        new_filename = f"{name_without_ext}.jpg"
        
        # Replace the image field with optimized version
        self.image = InMemoryUploadedFile(
            output,
            'ImageField',
            new_filename,
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
    
    def save(self, *args, **kwargs):
        """Override save to optimize image and set default WhatsApp message."""
        # Check if this is a new image upload
        try:
            # Only optimize if image is new (not already in database)
            if self.pk:  # Object exists, check if image changed
                try:
                    old_instance = ApparelProduct.objects.get(pk=self.pk)
                    # Only optimize if image has changed
                    if old_instance.image != self.image:
                        self.optimize_image()
                except ApparelProduct.DoesNotExist:
                    # Object being created, optimize the image
                    if self.image:
                        self.optimize_image()
            else:
                # New object, optimize if image exists
                if self.image:
                    self.optimize_image()
        except Exception as e:
            # Log error but don't crash - save without optimization
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Image optimization failed: {e}")
            print(f"⚠️  Image optimization failed: {e}")
            print("   → Saving product without optimization")
        
        # Set default WhatsApp message if not provided
        if not self.whatsapp_message:
            self.whatsapp_message = f"Hello! I would like to order {self.title}."
        
        super().save(*args, **kwargs)


class Order(models.Model):
    """Model for storing apparel orders."""
    
    PAYMENT_MODE_CHOICES = [
        ('ONLINE', 'Online Payment'),
        ('COD', 'Cash on Delivery'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Order Information
    order_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique order ID"
    )
    
    # Product Details
    product_title = models.CharField(
        max_length=200,
        help_text="Product name"
    )
    size = models.CharField(
        max_length=10,
        help_text="Product size"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Order quantity"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price in INR"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount (price × quantity)"
    )
    
    # Customer Details
    full_name = models.CharField(
        max_length=200,
        help_text="Customer full name"
    )
    mobile = models.CharField(
        max_length=15,
        help_text="Customer mobile number"
    )
    country_code = models.CharField(
        max_length=5,
        default='+91',
        help_text="Country code"
    )
    
    # Delivery Address
    house_flat_no = models.CharField(
        max_length=200,
        help_text="House/Flat number"
    )
    street_locality = models.CharField(
        max_length=200,
        help_text="Street/Locality"
    )
    city = models.CharField(
        max_length=100,
        help_text="City"
    )
    state = models.CharField(
        max_length=100,
        help_text="State"
    )
    pin_code = models.CharField(
        max_length=10,
        help_text="PIN code"
    )
    
    # Payment Information
    payment_mode = models.CharField(
        max_length=10,
        choices=PAYMENT_MODE_CHOICES,
        default='COD',
        help_text="Payment mode"
    )
    payment_status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        help_text="Payment status"
    )
    
    # Razorpay Fields (for online payments)
    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Razorpay order ID"
    )
    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Razorpay payment ID"
    )
    razorpay_signature = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Razorpay signature for verification"
    )
    
    # Order Status
    order_status = models.CharField(
        max_length=15,
        choices=ORDER_STATUS_CHOICES,
        default='PENDING',
        help_text="Order processing status"
    )
    
    # WhatsApp Integration
    whatsapp_message_sid = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Twilio WhatsApp message SID"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order {self.order_id} - {self.full_name}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate total amount."""
        if not self.total_amount:
            self.total_amount = self.price * self.quantity
        super().save(*args, **kwargs)
