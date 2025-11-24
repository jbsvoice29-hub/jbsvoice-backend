from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from decouple import config
import razorpay
import hmac
import hashlib
from .models import Order
from twilio.rest import Client
import uuid


@api_view(['POST'])
def create_razorpay_order(request):
    """
    Create a Razorpay order for online payment.
    
    Expected payload:
    {
        "amount": 399.00,
        "currency": "INR",
        "order_data": {
            "product_title": "Polo T-shirt",
            "size": "M",
            "quantity": 1,
            ... other order details
        }
    }
    """
    try:
        # Get Razorpay credentials from environment
        razorpay_key_id = config('RAZORPAY_KEY_ID', default=None)
        razorpay_key_secret = config('RAZORPAY_KEY_SECRET', default=None)
        
        if not all([razorpay_key_id, razorpay_key_secret]):
            return Response(
                {'error': 'Razorpay credentials not configured. Please contact administrator.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        # Get amount from request (in INR)
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'INR')
        
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert amount to paise (Razorpay expects amount in smallest currency unit)
        amount_in_paise = int(float(amount) * 100)
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': currency,
            'payment_capture': 1  # Auto capture payment
        })
        
        # Return order details to frontend
        return Response({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
            'currency': razorpay_order['currency'],
            'razorpay_key_id': razorpay_key_id  # Need this for frontend
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Error creating Razorpay order: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to create payment order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def verify_payment(request):
    """
    Verify Razorpay payment and create order.
    
    Expected payload:
    {
        "razorpay_order_id": "order_xxx",
        "razorpay_payment_id": "pay_xxx",
        "razorpay_signature": "signature_xxx",
        "order_data": {
            "product_title": "Polo T-shirt",
            "size": "M",
            "quantity": 1,
            "price": 399.00,
            "full_name": "John Doe",
            "mobile": "9876543210",
            "country_code": "+91",
            "pin_code": "500001",
            "state": "Telangana",
            "city": "Hyderabad",
            "house_flat_no": "123",
            "street_locality": "Main Street",
            "payment_mode": "ONLINE"
        }
    }
    """
    try:
        # Get payment details from request
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        order_data = request.data.get('order_data', {})
        
        # Validate required fields
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response(
                {'error': 'Missing payment verification details'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get Razorpay credentials
        razorpay_key_secret = config('RAZORPAY_KEY_SECRET', default=None)
        
        if not razorpay_key_secret:
            return Response(
                {'error': 'Razorpay credentials not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Verify signature
        generated_signature = hmac.new(
            razorpay_key_secret.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != razorpay_signature:
            return Response(
                {'error': 'Payment verification failed. Invalid signature.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Payment verified successfully, create order
        # Generate unique order ID
        order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total amount
        total_amount = float(order_data['price']) * int(order_data['quantity'])
        
        # Create order in database
        order = Order.objects.create(
            order_id=order_id,
            product_title=order_data['product_title'],
            size=order_data['size'],
            quantity=order_data['quantity'],
            price=order_data['price'],
            total_amount=total_amount,
            full_name=order_data['full_name'],
            mobile=order_data['mobile'],
            country_code=order_data.get('country_code', '+91'),
            house_flat_no=order_data['house_flat_no'],
            street_locality=order_data['street_locality'],
            city=order_data['city'],
            state=order_data['state'],
            pin_code=order_data['pin_code'],
            payment_mode='ONLINE',
            payment_status='COMPLETED',
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
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
        
        return Response({
            'success': True,
            'message': 'Payment verified and order placed successfully!',
            'order_id': order_id,
            'order_status': order.order_status,
            'payment_status': order.payment_status
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Error verifying payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Failed to verify payment: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def send_whatsapp_notification(order):
    """Send WhatsApp notification for order with comprehensive error logging."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get Twilio credentials with detailed logging
    account_sid = config('TWILIO_ACCOUNT_SID', default=None)
    auth_token = config('TWILIO_AUTH_TOKEN', default=None)
    from_whatsapp = config('TWILIO_WHATSAPP_FROM', default=None)
    to_whatsapp = config('TWILIO_WHATSAPP_TO', default=None)
    
    # Log which credentials are missing (without exposing values)
    missing_creds = []
    if not account_sid:
        missing_creds.append('TWILIO_ACCOUNT_SID')
    if not auth_token:
        missing_creds.append('TWILIO_AUTH_TOKEN')
    if not from_whatsapp:
        missing_creds.append('TWILIO_WHATSAPP_FROM')
    if not to_whatsapp:
        missing_creds.append('TWILIO_WHATSAPP_TO')
    
    if missing_creds:
        error_msg = f"Twilio credentials not configured. Missing: {', '.join(missing_creds)}"
        logger.error(error_msg)
        print(f"❌ WhatsApp ERROR: {error_msg}")
        raise Exception(error_msg)
    
    logger.info(f"✅ All Twilio credentials found. Attempting to send WhatsApp for order {order.order_id}")
    print(f"🔄 Sending WhatsApp notification for order {order.order_id}")
    print(f"   From: {from_whatsapp}")
    print(f"   To: {to_whatsapp}")
    
    # Format WhatsApp message
    payment_info = "💳 Payment: Online (PAID)" if order.payment_mode == 'ONLINE' else "💵 Payment: Cash on Delivery"
    
    message = f"""🛍️ *New Order Received!*

📦 *Order Details:*
• Order ID: {order.order_id}
• Product: {order.product_title}
• Size: {order.size}
• Quantity: {order.quantity}
• Total: ₹{order.total_amount:.2f}
{payment_info}

👤 *Customer Details:*
• Name: {order.full_name}
• Mobile: {order.country_code} {order.mobile}

📍 *Delivery Address:*
• House/Flat: {order.house_flat_no}
• Street: {order.street_locality}
• City: {order.city}
• State: {order.state}
• PIN Code: {order.pin_code}

✅ Please process this order!"""
    
    try:
        # Initialize Twilio client and send message
        client = Client(account_sid, auth_token)
        logger.info(f"Twilio client initialized. Sending message...")
        print(f"📤 Twilio client initialized successfully")
        
        message_response = client.messages.create(
            body=message,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        
        logger.info(f"✅ WhatsApp Message Sent Successfully: SID={message_response.sid}, Status={message_response.status}")
        print(f"✅ WhatsApp Message Sent: SID={message_response.sid}")
        print(f"   Status: {message_response.status}")
        
        return message_response.sid
        
    except Exception as e:
        error_details = str(e)
        logger.error(f"❌ Twilio API Error: {error_details}")
        print(f"❌ WhatsApp Send Failed!")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {error_details}")
        
        # Re-raise with more context
        raise Exception(f"Twilio WhatsApp Error: {error_details}")
