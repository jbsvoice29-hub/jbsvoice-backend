from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from twilio.rest import Client
from django.conf import settings
from decouple import config
from .models import Order
from .payment_views import send_whatsapp_notification
import os
import uuid


@api_view(['POST'])
def create_whatsapp_order(request):
    """
    Create a COD (Cash on Delivery) order and send WhatsApp notification.
    For online payments, use the payment verification endpoint instead.
    """
    try:
        # Get order data from request
        data = request.data
        
        # Validate payment mode - this endpoint is only for COD
        payment_mode = data.get('payment_mode', 'COD')
        if payment_mode == 'ONLINE':
            return Response(
                {'error': 'Online payments must be processed through payment verification endpoint'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required fields
        required_fields = ['product_title', 'size', 'quantity', 'price', 'full_name', 
                          'mobile', 'country_code', 'pin_code', 'state', 'city', 
                          'house_flat_no', 'street_locality']
        
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Missing required field: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Generate unique order ID
        order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total price
        total_price = float(data['price']) * int(data['quantity'])
        
        # Create order in database
        order = Order.objects.create(
            order_id=order_id,
            product_title=data['product_title'],
            size=data['size'],
            quantity=data['quantity'],
            price=data['price'],
            total_amount=total_price,
            full_name=data['full_name'],
            mobile=data['mobile'],
            country_code=data['country_code'],
            house_flat_no=data['house_flat_no'],
            street_locality=data['street_locality'],
            city=data['city'],
            state=data['state'],
            pin_code=data['pin_code'],
            payment_mode='COD',
            payment_status='PENDING',
            order_status='CONFIRMED'
        )
        
        # Send WhatsApp notification
        try:
            print(f"\n{'='*60}")
            print(f"🔔 Attempting WhatsApp notification for Order: {order_id}")
            print(f"{'='*60}")
            whatsapp_message_sid = send_whatsapp_notification(order)
            order.whatsapp_message_sid = whatsapp_message_sid
            order.save()
            print(f"✅ WhatsApp notification successful!")
            print(f"{'='*60}\n")
        except Exception as e:
            error_msg = str(e)
            print(f"\n{'='*60}")
            print(f"❌ WhatsApp notification failed (non-critical)")
            print(f"   Order ID: {order_id}")
            print(f"   Error: {error_msg}")
            print(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            # Still create order but don't fail if WhatsApp fails
            return Response({
                'success': True,
                'message': 'Order placed successfully!',
                'order_id': order_id,
                'warning': f'WhatsApp notification could not be sent: {error_msg}'
            }, status=status.HTTP_201_CREATED)
        
        
        # Return success response
        return Response({
            'success': True,
            'message': 'Order placed successfully! We will contact you shortly.',
            'order_id': order_id,
            'whatsapp_message_sid': whatsapp_message_sid
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Error processing order: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to process order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

