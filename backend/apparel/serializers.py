from rest_framework import serializers
from .models import ApparelProduct


class ApparelProductSerializer(serializers.ModelSerializer):
    """Serializer for ApparelProduct model."""
    
    # Read-only fields to include computed values
    status_color = serializers.CharField(source='get_status_color', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    # Make image URL absolute
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ApparelProduct
        fields = [
            'id',
            'title',
            'description',
            'image',
            'image_url',
            'category',
            'category_display',
            'sizes',
            'mrp_price',
            'status',
            'status_display',
            'status_color',
            'whatsapp_message',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """Get absolute URL for image."""
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def validate_sizes(self, value):
        """Validate sizes field."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Sizes must be a list.")
        
        valid_sizes = ['S', 'M', 'L', 'XL', 'XXL']
        for size in value:
            if size not in valid_sizes:
                raise serializers.ValidationError(
                    f"Invalid size '{size}'. Must be one of: {', '.join(valid_sizes)}"
                )
        
        return value
    
    def validate_mrp_price(self, value):
        """Validate MRP price."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
    
    def validate_image(self, value):
        """Validate uploaded image."""
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file size must be less than 5MB.")
            
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            ext = value.name.lower().split('.')[-1]
            if f'.{ext}' not in valid_extensions:
                raise serializers.ValidationError(
                    f"Invalid file type. Allowed types: {', '.join(valid_extensions)}"
                )
        
        return value
