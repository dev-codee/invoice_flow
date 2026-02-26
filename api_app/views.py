from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

__all__ = [
    'ClientViewSet', 'InvoiceViewSet', 'PaymentViewSet',
    'RevenueReportView', 'AgingReportView',
    'TokenObtainPairView', 'TokenRefreshView',
]


class ClientViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response([])


class InvoiceViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response([])


class PaymentViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response([])


class RevenueReportView(generics.GenericAPIView):
    def get(self, request):
        return Response({'revenue': 0})


class AgingReportView(generics.GenericAPIView):
    def get(self, request):
        return Response({'aging': []})
