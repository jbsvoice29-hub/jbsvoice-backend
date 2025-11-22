from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ApparelProduct
from .serializers import ApparelProductSerializer


class ApparelProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing apparel products.
    
    Provides CRUD operations:
    - list: GET /api/apparel/
    - create: POST /api/apparel/
    - retrieve: GET /api/apparel/{id}/
    - update: PUT /api/apparel/{id}/
    - partial_update: PATCH /api/apparel/{id}/
    - destroy: DELETE /api/apparel/{id}/
    """
    
    queryset = ApparelProduct.objects.filter(is_active=True)
    serializer_class = ApparelProductSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        Supports filtering by category.
        """
        queryset = ApparelProduct.objects.filter(is_active=True)
        
        # Filter by category if provided
        category = self.request.query_params.get('category', None)
        if category and category.upper() != 'ALL':
            queryset = queryset.filter(category=category.upper())
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new apparel product."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        """Update an existing apparel product."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete apparel product (mark as inactive)."""
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(
            {"message": "Product deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of all available categories."""
        categories = [
            {'value': choice[0], 'label': choice[1]}
            for choice in ApparelProduct.CATEGORY_CHOICES
        ]
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def sizes(self, request):
        """Get list of all available sizes."""
        sizes = [
            {'value': choice[0], 'label': choice[1]}
            for choice in ApparelProduct.SIZE_CHOICES
        ]
        return Response(sizes)
