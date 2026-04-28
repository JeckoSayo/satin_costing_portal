from django.contrib import admin
from .models import (
    PaperSize,
    StickerSize,
    Material,
    PriceSetting,
    EquipmentOverhead,
    SaleLog,
    SaleLogItem,
    MarketplaceFee,
    StockMovement,
    ExpenseLog,
    StockPurchase,
    ShopTask,
)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("item_name", "category", "stock_qty", "reorder_level", "unit", "unit_cost", "is_active")
    list_filter = ("category", "use_type", "is_active")
    search_fields = ("item_name", "sku", "supplier")
    readonly_fields = ("unit_cost",)


@admin.register(SaleLogItem)
class SaleLogItemAdmin(admin.ModelAdmin):
    list_display = ("line_id", "sale", "product_name", "quantity", "line_total", "line_cost", "line_profit")
    search_fields = ("line_id", "product_name", "sale__receipt_number")


class SaleLogItemInline(admin.TabularInline):
    model = SaleLogItem
    extra = 0
    readonly_fields = ("line_id", "line_total", "line_cost", "line_profit")


@admin.register(SaleLog)
class SaleLogAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "created_at", "platform", "customer_name", "selling_price", "cost", "profit", "status", "stock_deducted")
    list_filter = ("platform", "payment_method", "status", "stock_deducted", "created_at")
    search_fields = ("receipt_number", "customer_name", "order_name", "platform_order_id", "tracking_number")
    readonly_fields = ("receipt_number", "cost_breakdown")
    inlines = [SaleLogItemInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "material", "movement_type", "quantity", "balance_after", "sale")
    list_filter = ("movement_type", "created_at", "material__category")
    search_fields = ("material__item_name", "sale__receipt_number", "notes")
    readonly_fields = ("created_at",)


@admin.register(MarketplaceFee)
class MarketplaceFeeAdmin(admin.ModelAdmin):
    list_display = ("platform", "fee_percent", "fixed_fee", "is_active")
    list_filter = ("is_active",)


admin.site.register(PaperSize)
admin.site.register(StickerSize)
admin.site.register(PriceSetting)
admin.site.register(EquipmentOverhead)

from .models import ProductCategory, ProductPreset, ProductPriceTier, CraftQuote


class ProductPriceTierInline(admin.TabularInline):
    model = ProductPriceTier
    extra = 1


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "pricing_type", "is_active")
    list_filter = ("pricing_type", "is_active")
    search_fields = ("name",)


@admin.register(ProductPreset)
class ProductPresetAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "base_selling_price", "base_quantity", "minimum_order_price", "target_margin_percent", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "sku", "description")
    inlines = [ProductPriceTierInline]


@admin.register(CraftQuote)
class CraftQuoteAdmin(admin.ModelAdmin):
    list_display = ("created_at", "product", "customer_name", "quantity", "selling_price", "profit", "profit_margin")
    list_filter = ("created_at", "product__category")
    search_fields = ("product__name", "customer_name")
    readonly_fields = ("cost_breakdown",)

@admin.register(ExpenseLog)
class ExpenseLogAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "description", "supplier", "amount")
    list_filter = ("category", "date")
    search_fields = ("description", "supplier", "notes")


@admin.register(StockPurchase)
class StockPurchaseAdmin(admin.ModelAdmin):
    list_display = ("purchase_date", "material", "supplier", "quantity_added", "total_cost", "unit_cost", "stock_applied")
    list_filter = ("purchase_date", "stock_applied", "material__category")
    search_fields = ("material__item_name", "supplier", "notes")


@admin.register(ShopTask)
class ShopTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "due_date", "priority", "status", "related_sale")
    list_filter = ("status", "priority", "due_date")
    search_fields = ("title", "notes", "related_sale__receipt_number")

try:
    from .models import QuickPOSProduct, QuickPOSPriceSnapshot

    @admin.register(QuickPOSProduct)
    class QuickPOSProductAdmin(admin.ModelAdmin):
        list_display = ("name", "button_label", "selling_price", "bundle_quantity", "estimated_cost", "estimated_margin", "active")
        list_filter = ("active", "product_type")
        search_fields = ("name", "button_label", "sku")
        readonly_fields = ("estimated_cost", "estimated_profit", "estimated_margin", "recommended_price", "created_at", "updated_at")

    @admin.register(QuickPOSPriceSnapshot)
    class QuickPOSPriceSnapshotAdmin(admin.ModelAdmin):
        list_display = ("product", "snapshot_date", "selling_price", "estimated_cost", "estimated_margin")
        list_filter = ("snapshot_date",)
        search_fields = ("product__name",)
except Exception:
    pass

try:
    from .models import SmartPasteInquiry

    @admin.register(SmartPasteInquiry)
    class SmartPasteInquiryAdmin(admin.ModelAdmin):
        list_display = ("created_at", "customer_name", "product_name", "quantity", "confidence_score", "status")
        list_filter = ("status", "product_type", "created_at")
        search_fields = ("raw_message", "customer_name", "product_name", "material_keyword", "finish_keyword")
        readonly_fields = ("parsed_data", "created_at", "updated_at")
except Exception:
    pass
