from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from twilio.rest import Client
from django.conf import settings
from decouple import config
from .models import Order
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
        
        # Format WhatsApp message
        message = f"""🛍️ *New Order Received!*

📦 *Order Details:*
• Order ID: {order_id}
• Product: {data['product_title']}
• Size: {data['size']}
• Quantity: {data['quantity']}
• Total: ₹{total_price:.2f}
💵 Payment: Cash on Delivery

👤 *Customer Details:*
• Name: {data['full_name']}
• Mobile: {data['country_code']} {data['mobile']}

📍 *Delivery Address:*
• House/Flat: {data['house_flat_no']}
• Street: {data['street_locality']}
• City: {data['city']}
• State: {data['state']}
• PIN Code: {data['pin_code']}

✅ Please confirm this order!"""

        # Send WhatsApp message via Twilio
        # Use config to read from .env file
        account_sid = config('TWILIO_ACCOUNT_SID', default=None)
        auth_token = config('TWILIO_AUTH_TOKEN', default=None)
        from_whatsapp = config('TWILIO_WHATSAPP_FROM', default=None)
        to_whatsapp = config('TWILIO_WHATSAPP_TO', default=None)
        
        # Check if credentials are configured
        if not all([account_sid, auth_token, from_whatsapp, to_whatsapp]):
            print("Twilio credentials missing:", {
                'account_sid': bool(account_sid),
                'auth_token': bool(auth_token),
                'from_whatsapp': from_whatsapp,
                'to_whatsapp': to_whatsapp
            })
            # Still create order but don't fail if WhatsApp fails
            return Response({
                'success': True,
                'message': 'Order placed successfully!',
                'order_id': order_id,
                'warning': 'WhatsApp notification could not be sent (credentials missing)'
            }, status=status.HTTP_201_CREATED)
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send message
        message_response = client.messages.create(
            body=message,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        
        # Save WhatsApp message SID
        order.whatsapp_message_sid = message_response.sid
        order.save()
        
        print(f"WhatsApp Message Sent: SID={message_response.sid}, Status={message_response.status}")
        print(f"To: {to_whatsapp}")
        
        # Return success response
        return Response({
            'success': True,
            'message': 'Order placed successfully! We will contact you shortly.',
            'order_id': order_id,
            'whatsapp_message_sid': message_response.sid
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Error processing order: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to process order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
