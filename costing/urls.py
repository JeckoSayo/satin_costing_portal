from django.urls import path
from .views import (
    DashboardView, FullQuoteCalculatorView, CalculateQuoteView, LogSaleView,
    MaterialListView, MaterialCreateView, MaterialUpdateView, MaterialDeleteView, BulkMaterialDeleteView,
    StickerSizeListView, StickerSizeCreateView, StickerSizeUpdateView, StickerSizeDeleteView,
    PaperSizeListView, PaperSizeCreateView, PaperSizeUpdateView, PaperSizeDeleteView,
    PriceSettingsView, SalesLogView, SaleLogDeleteView, SaleLogUpdateView, SaleLogDetailView,
    SaleReceiptView, ProductCatalogView, ProductPresetCreateView, ProductPresetUpdateView, ProductPriceTierCreateView, ProductQuoteView, ProductCategoryCreateView, OrderQueueView, UpdateJobStatusView, CustomerHistoryView, ReorderSaleView, ExpenseListView, StockPurchaseListView, ShopTaskListView, JobTicketView, CashflowView, AnalyticsDashboardView, SmartBusinessView, FastPOSView, QuickPOSProductListView, QuickPOSProductCreateView, QuickPOSProductUpdateView, CreatePOSPriceSnapshotView, SmartPasteView, SmartPasteInquiryUpdateView
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('quote-calculator/', FullQuoteCalculatorView.as_view(), name='quote_calculator'),
    path('calculate-quote/', CalculateQuoteView.as_view(), name='calculate_quote'),
    path('log-sale/', LogSaleView.as_view(), name='log_sale'),
    path('sales/', SalesLogView.as_view(), name='sales_log'),
    path('queue/', OrderQueueView.as_view(), name='order_queue'),
    path('queue/<int:pk>/status/', UpdateJobStatusView.as_view(), name='update_job_status'),
    path('customers/<str:customer_name>/', CustomerHistoryView.as_view(), name='customer_history'),
    path('sales/<int:pk>/reorder/', ReorderSaleView.as_view(), name='sale_reorder'),
    path('sales/<int:pk>/job-ticket/', JobTicketView.as_view(), name='job_ticket'),
    path('expenses/', ExpenseListView.as_view(), name='expenses'),
    path('stock-purchases/', StockPurchaseListView.as_view(), name='stock_purchases'),
    path('tasks/', ShopTaskListView.as_view(), name='tasks'),
    path('cashflow/', CashflowView.as_view(), name='cashflow'),
    path('analytics/', AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('smart-business/', SmartBusinessView.as_view(), name='smart_business'),
    path('smart-paste/', SmartPasteView.as_view(), name='smart_paste'),
    path('smart-paste/<int:pk>/edit/', SmartPasteInquiryUpdateView.as_view(), name='smart_paste_edit'),
    path('pos/', FastPOSView.as_view(), name='fast_pos'),
    path('pos/products/', QuickPOSProductListView.as_view(), name='pos_products'),
    path('pos/products/add/', QuickPOSProductCreateView.as_view(), name='pos_product_add'),
    path('pos/products/<int:pk>/edit/', QuickPOSProductUpdateView.as_view(), name='pos_product_edit'),
    path('pos/products/<int:pk>/snapshot/', CreatePOSPriceSnapshotView.as_view(), name='pos_product_snapshot'),


    path('materials/', MaterialListView.as_view(), name='materials'),
    path('materials/add/', MaterialCreateView.as_view(), name='material_add'),
    path('materials/<int:pk>/edit/', MaterialUpdateView.as_view(), name='material_edit'),
    path('materials/<int:pk>/delete/', MaterialDeleteView.as_view(), name='material_delete'),
    path('materials/bulk-delete/', BulkMaterialDeleteView.as_view(), name='material_bulk_delete'),

    path('sticker-sizes/', StickerSizeListView.as_view(), name='sticker_sizes'),
    path('sticker-sizes/add/', StickerSizeCreateView.as_view(), name='sticker_size_add'),
    path('sticker-sizes/<int:pk>/edit/', StickerSizeUpdateView.as_view(), name='sticker_size_edit'),
    path('sticker-sizes/<int:pk>/delete/', StickerSizeDeleteView.as_view(), name='sticker_size_delete'),

    path('paper-sizes/', PaperSizeListView.as_view(), name='paper_sizes'),
    path('paper-sizes/add/', PaperSizeCreateView.as_view(), name='paper_size_add'),
    path('paper-sizes/<int:pk>/edit/', PaperSizeUpdateView.as_view(), name='paper_size_edit'),
    path('paper-sizes/<int:pk>/delete/', PaperSizeDeleteView.as_view(), name='paper_size_delete'),

    path('settings/', PriceSettingsView.as_view(), name='price_settings'),
    path('products/', ProductCatalogView.as_view(), name='product_catalog'),
    path('products/quote/', ProductQuoteView.as_view(), name='product_quote'),
    path('products/add/', ProductPresetCreateView.as_view(), name='product_add'),
    path('products/category/add/', ProductCategoryCreateView.as_view(), name='product_category_add'),
    path('products/tier/add/', ProductPriceTierCreateView.as_view(), name='product_tier_add'),
    path('products/<int:pk>/edit/', ProductPresetUpdateView.as_view(), name='product_edit'),
    path("sales/<int:pk>/delete/", SaleLogDeleteView.as_view(), name="sale_delete"),
    path("sales/<int:pk>/edit/", SaleLogUpdateView.as_view(), name="sale_edit"),
    path("sales/<int:pk>/", SaleLogDetailView.as_view(), name="sale_detail"),
    path("sales/<int:pk>/receipt/", SaleReceiptView.as_view(), name="sale_receipt"),
]
