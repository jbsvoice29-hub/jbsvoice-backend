from django.contrib import admin
from django.utils.html import format_html
from .models import ApparelProduct, Order


@admin.register(ApparelProduct)
class ApparelProductAdmin(admin.ModelAdmin):
    """Admin interface for Apparel Products."""
    
    list_display = [
        'image_thumbnail',
        'title',
        'category',
        'mrp_price',
        'status',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'category',
        'status',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'description',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'image_preview',
    ]
    
    fieldsets = (
        ('Product Information', {
            'fields': ('title', 'description', 'category', 'status')
        }),
        ('Pricing & Sizes', {
            'fields': ('mrp_price', 'sizes')
        }),
        ('Media', {
            'fields': ('image', 'image_preview')
        }),
        ('WhatsApp Integration', {
            'fields': ('whatsapp_message',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_thumbnail(self, obj):
        """Display small thumbnail in list view."""
        if obj and obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return '-'
    image_thumbnail.short_description = 'Image'
    
    def image_preview(self, obj):
        """Display larger image preview in detail view."""
        if obj and obj.image:
            return format_html('<img src="{}" width="300" style="border-radius: 8px;" />', obj.image.url)
        return 'No image uploaded'
    image_preview.short_description = 'Image Preview'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Orders."""
    
    list_display = [
        'order_id',
        'product_title',
        'full_name',
        'mobile',
        'total_amount',
        'payment_mode',
        'payment_status',
        'order_status',
        'created_at',
    ]
    
    list_filter = [
        'payment_mode',
        'payment_status',
        'order_status',
        'created_at',
    ]
    
    search_fields = [
        'order_id',
        'product_title',
        'full_name',
        'mobile',
        'razorpay_order_id',
        'razorpay_payment_id',
    ]
    
    readonly_fields = [
        'order_id',
        'razorpay_order_id',
        'razorpay_payment_id',
        'razorpay_signature',
        'whatsapp_message_sid',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'order_status')
        }),
        ('Product Details', {
            'fields': ('product_title', 'size', 'quantity', 'price', 'total_amount')
        }),
        ('Customer Details', {
            'fields': ('full_name', 'mobile', 'country_code')
        }),
        ('Delivery Address', {
            'fields': ('house_flat_no', 'street_locality', 'city', 'state', 'pin_code')
        }),
        ('Payment Information', {
            'fields': ('payment_mode', 'payment_status', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('WhatsApp', {
            'fields': ('whatsapp_message_sid',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
