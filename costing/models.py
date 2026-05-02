from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
from django.db import models


class PaperSize(models.Model):
    name = models.CharField(max_length=100)
    width_in = models.DecimalField(max_digits=6, decimal_places=2)
    height_in = models.DecimalField(max_digits=6, decimal_places=2)

    use_cricut_safe_area = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def cricut_safe_width_in(self):
        if not self.use_cricut_safe_area:
            return self.width_in
        return Decimal(str(round(float(self.width_in) * 0.87, 2)))

    @property
    def cricut_safe_height_in(self):
        if not self.use_cricut_safe_area:
            return self.height_in
        return Decimal(str(round(float(self.height_in) * 0.83, 2)))


class StickerSize(models.Model):
    name = models.CharField(max_length=100)
    width_in = models.DecimalField(max_digits=6, decimal_places=2)
    height_in = models.DecimalField(max_digits=6, decimal_places=2)
    paper_size = models.ForeignKey(PaperSize, on_delete=models.SET_NULL, null=True, blank=True)
    use_cricut_safe_area = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["width_in", "height_in"]

    def __str__(self):
        return self.name

    def get_fit(self, use_cricut=True):
        if not self.paper_size:
            paper_w = Decimal("8.27")
            paper_h = Decimal("11.69")
        else:
            if use_cricut:
                paper_w = self.paper_size.cricut_safe_width_in
                paper_h = self.paper_size.cricut_safe_height_in
            else:
                paper_w = self.paper_size.width_in
                paper_h = self.paper_size.height_in

        if self.width_in <= 0 or self.height_in <= 0:
            return 0

        normal = (
            int((paper_w / self.width_in).to_integral_value(rounding=ROUND_FLOOR))
            * int((paper_h / self.height_in).to_integral_value(rounding=ROUND_FLOOR))
        )

        rotated = (
            int((paper_w / self.height_in).to_integral_value(rounding=ROUND_FLOOR))
            * int((paper_h / self.width_in).to_integral_value(rounding=ROUND_FLOOR))
        )

        return max(normal, rotated)

    @property
    def safe_fit(self):
        return self.get_fit(use_cricut=True)

    @property
    def max_tight_fit(self):
        return self.get_fit(use_cricut=False)

    @property
    def best_for_costing(self):
        return self.get_fit(use_cricut=self.use_cricut_safe_area)


class Material(models.Model):
    CATEGORY_STICKER = "Sticker Paper"
    CATEGORY_LAMINATION = "Lamination"
    CATEGORY_PACKAGING = "Packaging"
    CATEGORY_INK = "Ink"
    CATEGORY_OTHER = "Other"

    CATEGORY_CHOICES = [
        (CATEGORY_STICKER, "Sticker Paper / Main Material"),
        (CATEGORY_LAMINATION, "Lamination / Photo Top"),
        (CATEGORY_PACKAGING, "Packaging"),
        (CATEGORY_INK, "Ink"),
        (CATEGORY_OTHER, "Other"),
    ]

    USE_DIRECT = "Direct Material"
    USE_EQUIPMENT = "Equipment"
    USE_TOOL = "Tool"

    USE_TYPE_CHOICES = [
        (USE_DIRECT, "Direct Material"),
        (USE_EQUIPMENT, "Equipment"),
        (USE_TOOL, "Tool"),
    ]

    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    item_name = models.CharField(max_length=180, unique=True)
    pack_price = models.DecimalField(max_digits=12, decimal_places=2)
    pack_qty = models.DecimalField(max_digits=12, decimal_places=2)
    stock_qty = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current stock on hand. Example: sheets, pcs, bags."
    )
    unit = models.CharField(max_length=40)
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        null=True,
        help_text="Optional low stock warning level."
    )
    sku = models.CharField(max_length=80, blank=True)
    supplier = models.CharField(max_length=160, blank=True)

    use_type = models.CharField(max_length=40, choices=USE_TYPE_CHOICES, default=USE_DIRECT)

    packaging_capacity = models.PositiveIntegerField(
        default=1,
        blank=True,
        null=True,
        help_text="For packaging only. Example: 1 OPP bag can hold 2 stickers, enter 2.",
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "item_name"]

    def __str__(self):
        return self.item_name

    @property
    def unit_cost(self):
        if not self.pack_qty:
            return Decimal("0.00")
        return self.pack_price / self.pack_qty

    def units_needed_for_quantity(self, quantity):
        quantity = Decimal(str(quantity or 0))

        if quantity <= 0:
            return Decimal("0")

        if self.category != self.CATEGORY_PACKAGING:
            return quantity

        capacity = Decimal(str(self.packaging_capacity or 1))
        return (quantity / capacity).to_integral_value(rounding=ROUND_CEILING)

    def cost_for_quantity(self, quantity):
        return self.units_needed_for_quantity(quantity) * self.unit_cost

    @property
    def is_low_stock(self):
        return (self.stock_qty or Decimal("0.00")) <= (self.reorder_level or Decimal("0.00"))

    def deduct_stock(self, quantity):
        quantity = Decimal(str(quantity or 0))

        if quantity <= 0:
            return

        if (self.stock_qty or Decimal("0.00")) < quantity:
            raise ValueError(f"Insufficient stock for {self.item_name}. Available: {self.stock_qty}, needed: {quantity}")

        self.stock_qty = (self.stock_qty or Decimal("0.00")) - quantity
        self.save(update_fields=["stock_qty"])

    def add_stock(self, quantity):
        quantity = Decimal(str(quantity or 0))
        if quantity <= 0:
            return
        self.stock_qty = (self.stock_qty or Decimal("0.00")) + quantity
        self.save(update_fields=["stock_qty"])


class PriceSetting(models.Model):
    orders_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("30.00"))
    labor_rate_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("80.00"), help_text="Legacy/manual labor rate. V2.1 uses sheet-based labor by default.")
    base_handling_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("10.00"), help_text="Automatic handling/setup fee per quote/order.")
    labor_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("2.00"), help_text="Automatic labor cost per printed sheet.")
    blade_wear_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"), help_text="Blade/cutter wear cost per sheet.")
    machine_overhead_per_order = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("5.00"), help_text="Printer/cutter/electricity overhead per quote/order.")
    default_ink_cost_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("3.00"))
    default_markup_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("45.00"))
    default_margin_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("35.00"))
    default_discount_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    default_sales_tax_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    safety_buffer_per_order = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("10.00"))
    additional_direct_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.08"))

    minimum_order_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("149.00"),
        help_text="Lowest allowed product selling price before shipping/tax."
    )
    default_waste_percent = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("7.00"),
        help_text="Extra buffer for misprints, test cuts, and spoilage."
    )
    default_marketplace_fee_percent = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Fallback selling fee when no marketplace-specific rule exists."
    )
    rounding_mode = models.CharField(
        max_length=20,
        default="ENDING_9",
        choices=[
            ("NONE", "No rounding"),
            ("WHOLE", "Round up to whole peso"),
            ("ENDING_9", "Round up to next price ending in 9"),
        ],
    )

    def __str__(self):
        return "Price Settings"


class EquipmentOverhead(models.Model):
    name = models.CharField(max_length=100)
    monthly_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @property
    def per_order_cost(self):
        settings = PriceSetting.objects.first()
        orders = settings.orders_per_month if settings and settings.orders_per_month else Decimal("1")
        return self.monthly_cost / orders


class SaleLog(models.Model):
    PLATFORM_WALKIN = "Walk-in"
    PLATFORM_SHOPEE = "Shopee"
    PLATFORM_LAZADA = "Lazada"
    PLATFORM_TIKTOK = "TikTok Shop"
    PLATFORM_FACEBOOK = "Facebook"
    PLATFORM_INSTAGRAM = "Instagram"
    PLATFORM_OTHER = "Other"

    PLATFORM_CHOICES = [
        (PLATFORM_WALKIN, "Walk-in"),
        (PLATFORM_SHOPEE, "Shopee"),
        (PLATFORM_LAZADA, "Lazada"),
        (PLATFORM_TIKTOK, "TikTok Shop"),
        (PLATFORM_FACEBOOK, "Facebook"),
        (PLATFORM_INSTAGRAM, "Instagram"),
        (PLATFORM_OTHER, "Other"),
    ]

    STATUS_PENDING = "Pending"
    STATUS_PAID = "Paid"
    STATUS_PACKING = "Packing"
    STATUS_SHIPPED = "Shipped"
    STATUS_COMPLETED = "Completed"
    STATUS_CANCELLED = "Cancelled"
    STATUS_REFUNDED = "Refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_PACKING, "Packing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    PAYMENT_CASH = "Cash"
    PAYMENT_GCASH = "GCash"
    PAYMENT_BANK = "Bank Transfer"
    PAYMENT_COD = "COD"
    PAYMENT_PLATFORM = "Platform Payment"
    PAYMENT_OTHER = "Other"

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_GCASH, "GCash"),
        (PAYMENT_BANK, "Bank Transfer"),
        (PAYMENT_COD, "COD"),
        (PAYMENT_PLATFORM, "Platform Payment"),
        (PAYMENT_OTHER, "Other"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, blank=True, unique=True)

    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default=PLATFORM_WALKIN)
    platform_order_id = models.CharField(max_length=120, blank=True)
    tracking_number = models.CharField(max_length=120, blank=True)
    courier = models.CharField(max_length=80, blank=True)

    customer_name = models.CharField(max_length=120, blank=True)
    buyer_username = models.CharField(max_length=120, blank=True)
    buyer_phone = models.CharField(max_length=50, blank=True)
    shipping_address = models.TextField(blank=True)

    order_name = models.CharField(max_length=120, blank=True)
    sticker_size = models.CharField(max_length=120, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    weight_grams = models.PositiveIntegerField(default=0)

    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    platform_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    sales_tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    stock_deducted = models.BooleanField(default=False)
    cost_breakdown = models.JSONField(default=dict, blank=True)

    cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    payment_method = models.CharField(max_length=80, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    status = models.CharField(max_length=80, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)

    # V3.4 daily shop operations
    JOB_NEW = "New"
    JOB_DESIGNING = "Designing"
    JOB_PRINTING = "Printing"
    JOB_CUTTING = "Cutting"
    JOB_PACKING = "Packing"
    JOB_READY = "Ready"
    JOB_RELEASED = "Released"
    JOB_ON_HOLD = "On Hold"
    JOB_CHOICES = [
        (JOB_NEW, "New"),
        (JOB_DESIGNING, "Designing"),
        (JOB_PRINTING, "Printing"),
        (JOB_CUTTING, "Cutting"),
        (JOB_PACKING, "Packing"),
        (JOB_READY, "Ready for Pickup / Ship"),
        (JOB_RELEASED, "Released / Completed"),
        (JOB_ON_HOLD, "On Hold"),
    ]
    job_status = models.CharField(max_length=40, choices=JOB_CHOICES, default=JOB_NEW)
    due_date = models.DateField(null=True, blank=True)
    rush_order = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    override_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    override_reason = models.CharField(max_length=220, blank=True)
    internal_job_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.receipt_number or self.id} - {self.customer_name or self.platform}"

    @property
    def item_count(self):
        return self.items.count()

    @property
    def total_quantity(self):
        if self.items.exists():
            return sum(item.quantity for item in self.items.all())
        return self.quantity

    @property
    def items_total(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def items_cost(self):
        return sum(item.line_cost for item in self.items.all())

    @property
    def items_profit(self):
        return sum(item.line_profit for item in self.items.all())

    @property
    def gross_total(self):
        return self.selling_price + self.shipping_fee + self.sales_tax

    @property
    def net_total(self):
        return self.gross_total - self.discount - self.platform_fee

    @property
    def price_per_piece(self):
        qty = self.total_quantity
        if qty:
            return self.selling_price / qty
        return Decimal("0.00")

    @property
    def profit_per_piece(self):
        qty = self.total_quantity
        if qty:
            return self.profit / qty
        return Decimal("0.00")

    @property
    def total_collected(self):
        return self.selling_price + self.shipping_fee + self.sales_tax

    @property
    def balance_due(self):
        return max((self.total_collected - (self.deposit_amount or Decimal("0.00"))), Decimal("0.00"))

    @property
    def payment_progress(self):
        total = self.total_collected
        if not total:
            return Decimal("0.00")
        return ((self.deposit_amount or Decimal("0.00")) / total) * Decimal("100")

    @property
    def is_overdue(self):
        from django.utils import timezone
        return bool(self.due_date and self.due_date < timezone.localdate() and self.job_status not in [self.JOB_RELEASED, self.JOB_READY])

    def save(self, *args, **kwargs):
        if self.override_price and self.override_price > 0:
            self.selling_price = self.override_price
        if not self.profit:
            self.profit = self.net_total - self.cost
        self.balance_amount = self.balance_due

        super().save(*args, **kwargs)

        expected_receipt_number = f"RCPT-{self.id:06d}"

        if self.receipt_number != expected_receipt_number:
            self.receipt_number = expected_receipt_number
            SaleLog.objects.filter(pk=self.pk).update(receipt_number=expected_receipt_number)


class SaleLogItem(models.Model):
    sale = models.ForeignKey(
        SaleLog,
        on_delete=models.CASCADE,
        related_name="items"
    )

    line_number = models.PositiveIntegerField(default=1)
    line_id = models.CharField(max_length=80, blank=True, unique=True)

    sku = models.CharField(max_length=80, blank=True)
    product_name = models.CharField(max_length=120, blank=True)
    sticker_size = models.CharField(max_length=120, blank=True)
    material = models.ForeignKey(
        Material,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale_material_items"
    )

    lamination = models.ForeignKey(
        Material,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale_lamination_items"
    )

    packaging = models.ForeignKey(
        Material,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sale_packaging_items"
    )

    material_name = models.CharField(max_length=180, blank=True)
    lamination_name = models.CharField(max_length=180, blank=True)
    packaging_name = models.CharField(max_length=180, blank=True)

    quantity = models.PositiveIntegerField(default=0)
    sheets_needed = models.PositiveIntegerField(default=0)
    packaging_capacity = models.PositiveIntegerField(default=1)
    material_qty_used = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    lamination_qty_used = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    packaging_qty_used = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["line_number"]

    def __str__(self):
        return self.line_id or self.product_name or "Sale Item"

    def save(self, *args, **kwargs):
        if not self.line_number:
            last_line = SaleLogItem.objects.filter(sale=self.sale).count()
            self.line_number = last_line + 1

        super().save(*args, **kwargs)

        if not self.line_id:
            line_code = f"{self.sale.receipt_number}-{self.line_number:02d}"
            SaleLogItem.objects.filter(pk=self.pk).update(line_id=line_code)


class MarketplaceFee(models.Model):
    platform = models.CharField(max_length=50, choices=SaleLog.PLATFORM_CHOICES, unique=True)
    fee_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["platform"]

    def __str__(self):
        return f"{self.platform} fee"


class StockMovement(models.Model):
    MOVEMENT_IN = "IN"
    MOVEMENT_OUT = "OUT"
    MOVEMENT_REVERSAL = "REVERSAL"
    MOVEMENT_ADJUSTMENT = "ADJUSTMENT"

    MOVEMENT_CHOICES = [
        (MOVEMENT_IN, "Stock In"),
        (MOVEMENT_OUT, "Stock Out / Sale"),
        (MOVEMENT_REVERSAL, "Sale Reversal"),
        (MOVEMENT_ADJUSTMENT, "Adjustment"),
    ]

    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="stock_movements")
    sale = models.ForeignKey(SaleLog, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements")
    sale_item = models.ForeignKey(SaleLogItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} {self.material.unit} - {self.material.item_name}"


class ProductCategory(models.Model):
    """V3: product groups for a print + Cricut craft studio."""
    PRICING_STICKER = "STICKER"
    PRICING_PHOTO = "PHOTO"
    PRICING_INVITATION = "INVITATION"
    PRICING_CRICUT = "CRICUT"
    PRICING_EVENT = "EVENT"
    PRICING_OTHER = "OTHER"

    PRICING_CHOICES = [
        (PRICING_STICKER, "Sticker / Label"),
        (PRICING_PHOTO, "Photo Print"),
        (PRICING_INVITATION, "Invitation / Card"),
        (PRICING_CRICUT, "Cricut Craft"),
        (PRICING_EVENT, "Event Package"),
        (PRICING_OTHER, "Other Custom"),
    ]

    name = models.CharField(max_length=120, unique=True)
    pricing_type = models.CharField(max_length=20, choices=PRICING_CHOICES, default=PRICING_OTHER)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductPreset(models.Model):
    """V3: reusable selling products such as 4-for-100 stickers, photo prints, invites, and Cricut crafts."""
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    sku = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)

    # Pricing controls
    base_selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Fixed or bundle selling price before add-ons/shipping.")
    base_quantity = models.PositiveIntegerField(default=1, help_text="How many pieces/sets are included in base selling price.")
    minimum_order_qty = models.PositiveIntegerField(default=1)
    minimum_order_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    target_margin_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("35.00"))
    markup_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("45.00"))
    waste_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("7.00"))
    handling_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("10.00"))
    labor_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("2.00"))
    machine_overhead = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("5.00"))
    design_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # Capacity guardrails
    max_daily_qty = models.PositiveIntegerField(default=300, help_text="Soft warning only. Does not block sales.")
    manual_quote_above_qty = models.PositiveIntegerField(default=500, help_text="Show manual quote warning above this quantity.")
    lead_time_note = models.CharField(max_length=160, blank=True)

    # Optional inventory/cost links
    default_sticker_size = models.ForeignKey(StickerSize, on_delete=models.SET_NULL, null=True, blank=True)
    main_material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name="preset_main_materials")
    lamination = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name="preset_laminations")
    packaging = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name="preset_packagings")
    ink_cost_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("3.00"))
    units_per_sheet_override = models.PositiveIntegerField(default=0, help_text="Optional. Leave 0 to use sticker size fit.")

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["category__name", "name"]
        unique_together = [["category", "name"]]

    def __str__(self):
        return self.name


class ProductPriceTier(models.Model):
    """V3: market pricing ladder for product presets (e.g. 4 for 100, 15 pcs for 250)."""
    product = models.ForeignKey(ProductPreset, on_delete=models.CASCADE, related_name="tiers")
    min_qty = models.PositiveIntegerField(default=1)
    max_qty = models.PositiveIntegerField(null=True, blank=True)
    fixed_bundle_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Use for bundle price such as 4 for 100.")
    bundle_qty = models.PositiveIntegerField(default=0, help_text="How many pieces included in fixed bundle price. Leave 0 for unit price.")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Fallback price per piece/set in this tier.")
    label = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["product", "min_qty"]

    def __str__(self):
        return self.label or f"{self.product.name}: {self.min_qty}+"


class CraftQuote(models.Model):
    """V3: saved quote from product catalog calculator. Keeps your costing audit without forcing a sale."""
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(ProductPreset, on_delete=models.PROTECT, related_name="quotes")
    customer_name = models.CharField(max_length=120, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    selected_tier_label = models.CharField(max_length=120, blank=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    profit_margin = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    cost_breakdown = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"



class ExpenseLog(models.Model):
    """V3.4: daily operating expense tracker for true net income."""
    CATEGORY_MATERIALS = "Materials"
    CATEGORY_INK = "Ink"
    CATEGORY_TOOLS = "Tools / Blades"
    CATEGORY_PACKAGING = "Packaging"
    CATEGORY_DELIVERY = "Delivery"
    CATEGORY_UTILITIES = "Utilities"
    CATEGORY_MARKETING = "Marketing"
    CATEGORY_OTHER = "Other"
    CATEGORY_CHOICES = [
        (CATEGORY_MATERIALS, "Materials"),
        (CATEGORY_INK, "Ink"),
        (CATEGORY_TOOLS, "Tools / Blades"),
        (CATEGORY_PACKAGING, "Packaging"),
        (CATEGORY_DELIVERY, "Delivery"),
        (CATEGORY_UTILITIES, "Utilities"),
        (CATEGORY_MARKETING, "Marketing"),
        (CATEGORY_OTHER, "Other"),
    ]
    date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    description = models.CharField(max_length=220)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    supplier = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} - {self.description}"


class StockPurchase(models.Model):
    """V3.4: stock-in purchase log. Adds stock and keeps cost history."""
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="purchases")
    purchase_date = models.DateField(auto_now_add=True)
    supplier = models.CharField(max_length=160, blank=True)
    quantity_added = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stock_applied = models.BooleanField(default=False)

    class Meta:
        ordering = ["-purchase_date", "-created_at"]

    @property
    def unit_cost(self):
        if not self.quantity_added:
            return Decimal("0.00")
        return self.total_cost / self.quantity_added

    def apply_stock(self):
        if self.stock_applied or self.quantity_added <= 0:
            return
        self.material.add_stock(self.quantity_added)
        StockMovement.objects.create(
            material=self.material,
            movement_type=StockMovement.MOVEMENT_IN,
            quantity=self.quantity_added,
            balance_after=self.material.stock_qty,
            notes=f"Stock purchase: {self.supplier or 'supplier not set'}",
        )
        self.stock_applied = True
        self.save(update_fields=["stock_applied"])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.stock_applied:
            self.apply_stock()

    def __str__(self):
        return f"{self.material.item_name} +{self.quantity_added}"


class ShopTask(models.Model):
    """V3.4: simple task board for pending quotes, follow-ups, and shop reminders."""
    STATUS_OPEN = "Open"
    STATUS_DONE = "Done"
    STATUS_CANCELLED = "Cancelled"
    STATUS_CHOICES = [(STATUS_OPEN, "Open"), (STATUS_DONE, "Done"), (STATUS_CANCELLED, "Cancelled")]
    PRIORITY_LOW = "Low"
    PRIORITY_NORMAL = "Normal"
    PRIORITY_HIGH = "High"
    PRIORITY_CHOICES = [(PRIORITY_LOW, "Low"), (PRIORITY_NORMAL, "Normal"), (PRIORITY_HIGH, "High")]

    title = models.CharField(max_length=180)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    related_sale = models.ForeignKey(SaleLog, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["status", "due_date", "-created_at"]

    def __str__(self):
        return self.title

class QuickPOSProduct(models.Model):
    """V3.7: fast counter/POS product button linked to live material costs."""
    name = models.CharField(max_length=120, unique=True)
    button_label = models.CharField(max_length=80, blank=True, help_text="Short label shown on POS button. Example: 4 for ₱100")
    product_type = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True)
    product_preset = models.ForeignKey(ProductPreset, on_delete=models.SET_NULL, null=True, blank=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    bundle_quantity = models.PositiveIntegerField(default=1, help_text="How many pieces are included in the selling price.")
    units_per_sheet = models.PositiveIntegerField(default=0, help_text="Leave 0 to use linked product/sticker-size fit when available.")
    sheets_per_bundle = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    main_material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_main_products")
    lamination = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_lamination_products")
    packaging = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name="pos_packaging_products")
    packaging_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    ink_cost_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("3.00"))
    handling_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("5.00"))
    labor_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    blade_wear_per_sheet = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.50"))
    machine_overhead = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("2.00"))
    waste_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("5.00"))
    target_margin_percent = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("35.00"))
    suggested_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), help_text="Optional suggested next price if current margin is low.")
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.button_label or self.name

    def _money(self, value):
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))

    @property
    def effective_sheets_per_bundle(self):
        if self.sheets_per_bundle and self.sheets_per_bundle > 0:
            return Decimal(str(self.sheets_per_bundle))
        if self.units_per_sheet and self.bundle_quantity:
            return (Decimal(str(self.bundle_quantity)) / Decimal(str(self.units_per_sheet))).to_integral_value(rounding=ROUND_CEILING)
        return Decimal("1.00")

    @property
    def estimated_cost(self):
        sheets = self.effective_sheets_per_bundle
        material_cost = (self.main_material.unit_cost if self.main_material else Decimal("0.00")) * sheets
        lamination_cost = (self.lamination.unit_cost if self.lamination else Decimal("0.00")) * sheets
        packaging_cost = (self.packaging.unit_cost if self.packaging else Decimal("0.00")) * Decimal(str(self.packaging_quantity or 0))
        ink_cost = Decimal(str(self.ink_cost_per_sheet or 0)) * sheets
        production_cost = material_cost + lamination_cost + packaging_cost + ink_cost + Decimal(str(self.handling_fee or 0)) + Decimal(str(self.labor_per_sheet or 0)) * sheets + Decimal(str(self.blade_wear_per_sheet or 0)) * sheets + Decimal(str(self.machine_overhead or 0))
        waste = production_cost * (Decimal(str(self.waste_percent or 0)) / Decimal("100"))
        return self._money(production_cost + waste)

    @property
    def estimated_profit(self):
        return self._money(Decimal(str(self.selling_price or 0)) - self.estimated_cost)

    @property
    def estimated_margin(self):
        price = Decimal(str(self.selling_price or 0))
        if price <= 0:
            return Decimal("0.00")
        return self._money((self.estimated_profit / price) * Decimal("100"))

    @property
    def is_low_margin(self):
        return self.estimated_margin < Decimal(str(self.target_margin_percent or 0))

    @property
    def recommended_price(self):
        cost = self.estimated_cost
        target = Decimal(str(self.target_margin_percent or 0))
        if target >= 100:
            return self.selling_price
        raw = cost / (Decimal("1.00") - (target / Decimal("100")))
        whole = int(raw.to_integral_value(rounding=ROUND_CEILING))
        if whole <= 9:
            return Decimal("9.00")
        rem = whole % 10
        candidate = whole + (9 - rem)
        return Decimal(str(candidate)).quantize(Decimal("0.01"))

    def material_requirements(self, bundle_count=1):
        bundles = Decimal(str(bundle_count or 1))
        sheets = self.effective_sheets_per_bundle * bundles
        packaging_qty = Decimal(str(self.packaging_quantity or 0)) * bundles
        return {"sheets": sheets, "packaging_qty": packaging_qty}


class QuickPOSPriceSnapshot(models.Model):
    """V3.7: optional monthly cost snapshot for inflation/material price review."""
    product = models.ForeignKey(QuickPOSProduct, on_delete=models.CASCADE, related_name="price_snapshots")
    snapshot_date = models.DateField(auto_now_add=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estimated_margin = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-snapshot_date", "product__name"]

    def __str__(self):
        return f"{self.product.name} - {self.snapshot_date}"


class SmartPasteInquiry(models.Model):
    """V5: pasted customer chat parsed into quote/order draft fields."""
    STATUS_DRAFT = "Draft"
    STATUS_QUOTED = "Quoted"
    STATUS_CONVERTED = "Converted"
    STATUS_DISCARDED = "Discarded"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_QUOTED, "Quoted"),
        (STATUS_CONVERTED, "Converted"),
        (STATUS_DISCARDED, "Discarded"),
    ]

    raw_message = models.TextField()
    customer_name = models.CharField(max_length=160, blank=True)
    product_name = models.CharField(max_length=180, blank=True)
    product_type = models.CharField(max_length=40, blank=True, default="STICKER")
    quantity = models.PositiveIntegerField(default=1)
    width_in = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height_in = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    material_keyword = models.CharField(max_length=120, blank=True)
    finish_keyword = models.CharField(max_length=120, blank=True)
    deadline_text = models.CharField(max_length=180, blank=True)
    delivery_method = models.CharField(max_length=80, blank=True)
    payment_method = models.CharField(max_length=80, blank=True)
    parsed_data = models.JSONField(default=dict, blank=True)
    suggested_reply = models.TextField(blank=True)
    confidence_score = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_quote = models.ForeignKey(CraftQuote, on_delete=models.SET_NULL, null=True, blank=True, related_name="smart_paste_inquiries")
    created_sale = models.ForeignKey(SaleLog, on_delete=models.SET_NULL, null=True, blank=True, related_name="smart_paste_inquiries")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Smart Paste inquiries"

    def __str__(self):
        return f"Smart Paste #{self.pk or 'new'} - {self.customer_name or self.product_name or 'Draft'}"
