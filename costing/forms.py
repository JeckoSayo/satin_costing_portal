from django import forms
from .models import Material, PaperSize, StickerSize, PriceSetting, SaleLog, ExpenseLog, StockPurchase, ShopTask


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "form-check-input"})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})


class MaterialForm(BootstrapModelForm):
    class Meta:
        model = Material
        fields = [
            "category",
            "item_name",
            "pack_price",
            "pack_qty",
            "stock_qty",
            "reorder_level",
            "unit",
            "sku",
            "supplier",
            "use_type",
            "packaging_capacity",
            "is_active",
            "notes",
        ]

        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
            "packaging_capacity": forms.NumberInput(attrs={
                "min": 1,
                "step": 1,
            }),
        }

        labels = {
            "packaging_capacity": "Packaging Capacity",
        }

        help_texts = {
            "packaging_capacity": "For packaging only. Example: if 1 OPP bag holds 2 stickers, enter 2.",
        }


class StickerSizeForm(BootstrapModelForm):
    class Meta:
        model = StickerSize
        fields = [
            "name",
            "paper_size",
            "width_in",
            "height_in",
            "use_cricut_safe_area",
            "is_active",
            "notes",
        ]

        widgets = {
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class PaperSizeForm(BootstrapModelForm):
    class Meta:
        model = PaperSize
        fields = [
            "name",
            "width_in",
            "height_in",
            "use_cricut_safe_area",
            "is_active",
        ]


class PriceSettingForm(BootstrapModelForm):
    class Meta:
        model = PriceSetting
        fields = [
            "orders_per_month",
            "labor_rate_per_hour",
            "default_ink_cost_per_sheet",
            "default_markup_percent",
            "default_margin_percent",
            "default_discount_percent",
            "default_sales_tax_percent",
            "safety_buffer_per_order",
            "additional_direct_cost",
            "minimum_order_price",
            "default_waste_percent",
            "default_marketplace_fee_percent",
            "rounding_mode",
        ]


class QuoteForm(forms.Form):
    customer_name = forms.CharField(required=False)
    order_name = forms.CharField(required=False)

    sticker_size_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=0)

    material_id = forms.IntegerField(required=False, min_value=1)
    lamination_id = forms.IntegerField(required=False, min_value=1)
    packaging_id = forms.IntegerField(required=False, min_value=1)

    ink_cost_per_sheet = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )

    labor_minutes = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )

    additional_direct_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )

    target_sale_price = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )

    shipping_fee = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )

    platform = forms.CharField(required=False)

    rush_percent = forms.DecimalField(
        required=False,
        max_digits=7,
        decimal_places=2,
        min_value=0,
    )

    design_fee = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )

from .models import ProductCategory, ProductPreset, ProductPriceTier, QuickPOSProduct, SmartPasteInquiry


class ProductCategoryForm(BootstrapModelForm):
    class Meta:
        model = ProductCategory
        fields = ["name", "pricing_type", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ProductPresetForm(BootstrapModelForm):
    class Meta:
        model = ProductPreset
        fields = [
            "category", "name", "sku", "description",
            "base_selling_price", "base_quantity", "minimum_order_qty", "minimum_order_price",
            "target_margin_percent", "markup_percent", "waste_percent",
            "handling_fee", "labor_per_sheet", "machine_overhead", "design_fee",
            "max_daily_qty", "manual_quote_above_qty", "lead_time_note",
            "default_sticker_size", "main_material", "lamination", "packaging",
            "ink_cost_per_sheet", "units_per_sheet_override", "is_active", "notes",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ProductPriceTierForm(BootstrapModelForm):
    class Meta:
        model = ProductPriceTier
        fields = ["product", "min_qty", "max_qty", "fixed_bundle_price", "bundle_qty", "unit_price", "label"]


class ProductQuoteForm(forms.Form):
    product_id = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1)
    customer_name = forms.CharField(required=False)
    notes = forms.CharField(required=False)

class SaleOperationsForm(BootstrapModelForm):
    class Meta:
        model = SaleLog
        fields = [
            "customer_name", "order_name", "platform", "payment_method", "status",
            "job_status", "due_date", "rush_order",
            "deposit_amount", "override_price", "override_reason",
            "platform_order_id", "tracking_number", "courier",
            "buyer_username", "buyer_phone", "shipping_address", "weight_grams",
            "internal_job_notes", "notes",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "shipping_address": forms.Textarea(attrs={"rows": 2}),
            "internal_job_notes": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ExpenseLogForm(BootstrapModelForm):
    class Meta:
        model = ExpenseLog
        fields = ["category", "description", "amount", "supplier", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class StockPurchaseForm(BootstrapModelForm):
    class Meta:
        model = StockPurchase
        fields = ["material", "supplier", "quantity_added", "total_cost", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class ShopTaskForm(BootstrapModelForm):
    class Meta:
        model = ShopTask
        fields = ["title", "due_date", "priority", "status", "related_sale", "notes"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

class QuickPOSProductForm(BootstrapModelForm):
    class Meta:
        model = QuickPOSProduct
        fields = [
            "name", "button_label", "product_type", "product_preset",
            "selling_price", "bundle_quantity", "units_per_sheet", "sheets_per_bundle",
            "main_material", "lamination", "packaging", "packaging_quantity",
            "ink_cost_per_sheet", "handling_fee", "labor_per_sheet", "blade_wear_per_sheet",
            "machine_overhead", "waste_percent", "target_margin_percent", "suggested_price",
            "active", "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

# V5 patch: better categorized POS material selectors and Smart Paste forms.
# These definitions intentionally override the earlier QuickPOSProductForm name in this module.
class QuickPOSProductForm(BootstrapModelForm):
    class Meta:
        model = QuickPOSProduct
        fields = [
            "name", "button_label", "product_type", "product_preset",
            "selling_price", "bundle_quantity", "units_per_sheet", "sheets_per_bundle",
            "main_material", "lamination", "packaging", "packaging_quantity",
            "ink_cost_per_sheet", "handling_fee", "labor_per_sheet", "blade_wear_per_sheet",
            "machine_overhead", "waste_percent", "target_margin_percent", "suggested_price",
            "active", "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["main_material"].queryset = Material.objects.filter(
            is_active=True, category=Material.CATEGORY_STICKER
        ).order_by("item_name")
        self.fields["lamination"].queryset = Material.objects.filter(
            is_active=True, category=Material.CATEGORY_LAMINATION
        ).order_by("item_name")
        self.fields["packaging"].queryset = Material.objects.filter(
            is_active=True, category=Material.CATEGORY_PACKAGING
        ).order_by("item_name")


class SmartPasteInquiryForm(BootstrapModelForm):
    class Meta:
        model = SmartPasteInquiry
        fields = [
            "raw_message", "customer_name", "product_name", "product_type",
            "quantity", "width_in", "height_in", "material_keyword", "finish_keyword",
            "deadline_text", "delivery_method", "payment_method", "suggested_reply", "status",
        ]
        widgets = {
            "raw_message": forms.Textarea(attrs={"rows": 7, "placeholder": "Paste Messenger/Facebook/Instagram order message here..."}),
            "suggested_reply": forms.Textarea(attrs={"rows": 4}),
        }


class SmartPasteRawForm(forms.Form):
    raw_message = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 8,
            "class": "form-control figma-control",
            "placeholder": "Example: Hi po, need 100 pcs waterproof stickers 2x2 matte, pickup tomorrow, GCash."
        })
    )
