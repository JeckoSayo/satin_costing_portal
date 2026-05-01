from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP, ROUND_UP
from django.db import transaction
from django.db.models import F
from .models import (
    Material,
    StickerSize,
    PriceSetting,
    EquipmentOverhead,
    SaleLog,
    SaleLogItem,
    MarketplaceFee,
    StockMovement,
    ProductPreset,
    ProductPriceTier,
    CraftQuote,
)


def D(value, default="0"):
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))


def money(value):
    return D(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def whole(value):
    return D(value).quantize(Decimal("1"), rounding=ROUND_UP)


def get_object_or_none(model, pk):
    if not pk:
        return None
    try:
        return model.objects.get(pk=pk)
    except (model.DoesNotExist, ValueError, TypeError):
        return None


def round_selling_price(value, mode="ENDING_9"):
    value = money(value)
    if mode == "NONE":
        return value
    rounded = whole(value)
    if mode == "WHOLE":
        return rounded
    # Commercial price ending in 9: 91 -> 99, 100 -> 109, 149 -> 149.
    if rounded <= 9:
        return Decimal("9.00")
    remainder = rounded % Decimal("10")
    if remainder <= Decimal("9"):
        candidate = rounded + (Decimal("9") - remainder)
    else:
        candidate = rounded
    if candidate < value:
        candidate += Decimal("10")
    return money(candidate)


def serialize_for_jsonfield(value):
    if isinstance(value, Decimal):
        return str(money(value))
    if isinstance(value, dict):
        return {key: serialize_for_jsonfield(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_for_jsonfield(item) for item in value]
    return value


def get_marketplace_fee_percent(platform):
    settings = PriceSetting.objects.first() or PriceSetting.objects.create()
    if not platform:
        return settings.default_marketplace_fee_percent
    fee = MarketplaceFee.objects.filter(platform=platform, is_active=True).first()
    if fee:
        return fee.fee_percent
    return settings.default_marketplace_fee_percent


def get_marketplace_fixed_fee(platform):
    if not platform:
        return Decimal("0")
    fee = MarketplaceFee.objects.filter(platform=platform, is_active=True).first()
    return fee.fixed_fee if fee else Decimal("0")


def calculate_quote(data):
    """
    V2 server-side pricing engine.

    Keeps the original app flow but adds:
    - waste/spoilage buffer
    - minimum order floor
    - platform fee protection
    - smart rounding
    - target margin protection
    """
    settings = PriceSetting.objects.first() or PriceSetting.objects.create()

    quantity = int(D(data.get("quantity"), "0"))
    platform = data.get("platform") or SaleLog.PLATFORM_WALKIN

    sticker_size = get_object_or_none(StickerSize, data.get("sticker_size_id"))
    material = get_object_or_none(Material, data.get("material_id"))
    lamination = get_object_or_none(Material, data.get("lamination_id"))
    packaging = get_object_or_none(Material, data.get("packaging_id"))

    costing_qty_per_sheet = D(sticker_size.best_for_costing if sticker_size else 0)

    sheets_needed = Decimal("0")
    if quantity > 0 and costing_qty_per_sheet > 0:
        sheets_needed = (D(quantity) / costing_qty_per_sheet).to_integral_value(rounding=ROUND_CEILING)

    material_unit = D(material.unit_cost if material else 0)
    lamination_unit = D(lamination.unit_cost if lamination else 0)
    packaging_unit = D(packaging.unit_cost if packaging else 0)

    packaging_qty = Decimal("0")
    if packaging:
        packaging_qty = packaging.units_needed_for_quantity(quantity)

    ink_cost_per_sheet = D(data.get("ink_cost_per_sheet"), settings.default_ink_cost_per_sheet)
    manual_extra_minutes = D(data.get("labor_minutes"), "0")
    additional_direct_cost = D(data.get("additional_direct_cost"), settings.additional_direct_cost)
    target_sale_price = D(data.get("target_sale_price"), "0")
    design_fee = D(data.get("design_fee"), "0")
    rush_percent = D(data.get("rush_percent"), "0")
    shipping_fee = D(data.get("shipping_fee"), "0")

    selected_material_total = sheets_needed * material_unit
    selected_lamination_total = sheets_needed * lamination_unit if lamination else Decimal("0")
    selected_packaging_total = packaging_qty * packaging_unit if packaging else Decimal("0")
    ink_usage_total = sheets_needed * ink_cost_per_sheet
    safety_buffer_total = settings.safety_buffer_per_order

    base_material_cost = (
        selected_material_total
        + selected_lamination_total
        + selected_packaging_total
        + ink_usage_total
        + safety_buffer_total
    )

    waste_cost = base_material_cost * settings.default_waste_percent / Decimal("100")
    total_material_cost = base_material_cost + waste_cost

    labor_rate = settings.labor_rate_per_hour
    base_handling_fee = D(settings.base_handling_fee)
    labor_per_sheet_total = sheets_needed * D(settings.labor_per_sheet)
    blade_wear_total = sheets_needed * D(settings.blade_wear_per_sheet)
    manual_extra_labor = (manual_extra_minutes / Decimal("60")) * labor_rate
    total_labor_cost = base_handling_fee + labor_per_sheet_total + blade_wear_total + manual_extra_labor

    equipment_overhead_total = sum((D(x.per_order_cost) for x in EquipmentOverhead.objects.all()), Decimal("0")) + D(settings.machine_overhead_per_order)

    total_additional_cost = additional_direct_cost + equipment_overhead_total + design_fee
    total_product_cost = total_material_cost + total_labor_cost + total_additional_cost

    markup_price = total_product_cost * (Decimal("1") + settings.default_markup_percent / Decimal("100"))

    marketplace_fee_percent = get_marketplace_fee_percent(platform)
    marketplace_fixed_fee = get_marketplace_fixed_fee(platform)
    margin_percent = settings.default_margin_percent
    total_margin_protection = margin_percent + marketplace_fee_percent

    margin_divisor = Decimal("1") - total_margin_protection / Decimal("100")
    margin_price = Decimal("0") if margin_divisor <= 0 else (total_product_cost + marketplace_fixed_fee) / margin_divisor

    base_price_before_floor = max(markup_price, margin_price, target_sale_price)
    rush_fee = base_price_before_floor * rush_percent / Decimal("100")
    minimum_order_price = settings.minimum_order_price

    recommended_base_price = max(base_price_before_floor + rush_fee, minimum_order_price)
    recommended_base_price = round_selling_price(recommended_base_price, settings.rounding_mode)

    discount = recommended_base_price * settings.default_discount_percent / Decimal("100")
    product_sale_price = max(recommended_base_price - discount, minimum_order_price)
    product_sale_price = round_selling_price(product_sale_price, settings.rounding_mode)

    platform_fee = (product_sale_price * marketplace_fee_percent / Decimal("100")) + marketplace_fixed_fee
    sales_tax = product_sale_price * settings.default_sales_tax_percent / Decimal("100")
    total_collected = product_sale_price + shipping_fee + sales_tax

    profit = product_sale_price - total_product_cost - platform_fee
    profit_margin = Decimal("0") if product_sale_price == 0 else profit / product_sale_price * Decimal("100")

    price_per_piece = Decimal("0") if quantity == 0 else product_sale_price / D(quantity)
    profit_per_piece = Decimal("0") if quantity == 0 else profit / D(quantity)

    stock_plan = {
        "material_qty_used": money(sheets_needed if material else 0),
        "lamination_qty_used": money(sheets_needed if lamination else 0),
        "packaging_qty_used": money(packaging_qty if packaging else 0),
    }

    return {
        "quantity": quantity,
        "sticker_size": sticker_size.name if sticker_size else "",
        "costing_qty_per_sheet": int(costing_qty_per_sheet or 0),
        "safe_fit": sticker_size.safe_fit if sticker_size else 0,
        "max_tight_fit": sticker_size.max_tight_fit if sticker_size else 0,
        "sheets_needed": int(sheets_needed),
        "minimum_order_price": money(minimum_order_price),
        "waste_percent": money(settings.default_waste_percent),
        "marketplace_fee_percent": money(marketplace_fee_percent),
        "marketplace_fee": money(platform_fee),
        "shipping_fee": money(shipping_fee),
        "total_collected": money(total_collected),
        "stock_plan": stock_plan,

        "material_items": {
            "selected_material": {"qty": int(sheets_needed), "unit": "sheet", "unit_cost": money(material_unit), "total": money(selected_material_total)},
            "selected_lamination": {"qty": int(sheets_needed) if lamination else 0, "unit": "sheet", "unit_cost": money(lamination_unit), "total": money(selected_lamination_total)},
            "selected_packaging": {"qty": int(packaging_qty) if packaging else 0, "unit": "pcs", "unit_cost": money(packaging_unit), "total": money(selected_packaging_total)},
            "ink_usage": {"qty": int(sheets_needed), "unit": "sheet", "unit_cost": money(ink_cost_per_sheet), "total": money(ink_usage_total)},
            "safety_buffer": {"qty": 1, "unit": "order", "unit_cost": money(safety_buffer_total), "total": money(safety_buffer_total)},
            "waste_buffer": {"qty": 1, "unit": "order", "unit_cost": money(waste_cost), "total": money(waste_cost)},
        },

        "labor_items": {
            "base_handling": {"qty": 1, "unit_cost": money(base_handling_fee), "total": money(base_handling_fee)},
            "labor_per_sheet": {"qty": int(sheets_needed), "unit_cost": money(settings.labor_per_sheet), "total": money(labor_per_sheet_total)},
            "blade_wear": {"qty": int(sheets_needed), "unit_cost": money(settings.blade_wear_per_sheet), "total": money(blade_wear_total)},
            "manual_extra": {"minutes": money(manual_extra_minutes), "rate_hour": money(labor_rate), "total": money(manual_extra_labor)},
            "total": money(total_labor_cost),
        },

        "additional_items": {
            "additional_direct_cost": {"qty": 1, "unit_cost": money(additional_direct_cost), "total": money(additional_direct_cost)},
            "machine_overhead": {"qty": 1, "unit_cost": money(settings.machine_overhead_per_order), "total": money(settings.machine_overhead_per_order)},
            "equipment_overhead": {"qty": 1, "unit_cost": money(equipment_overhead_total), "total": money(equipment_overhead_total)},
            "design_fee": {"qty": 1, "unit_cost": money(design_fee), "total": money(design_fee)},
            "total": money(total_additional_cost),
        },

        "total_material_cost": money(total_material_cost),
        "total_labor_cost": money(total_labor_cost),
        "total_additional_cost": money(total_additional_cost),
        "total_product_cost": money(total_product_cost),
        "markup_price": money(markup_price),
        "margin_price": money(margin_price),
        "target_sale_price": money(target_sale_price),
        "recommended_base_price": money(recommended_base_price),
        "discount": money(discount),
        "product_sale_price": money(product_sale_price),
        "sales_tax": money(sales_tax),
        "sales_price_tax": money(product_sale_price + sales_tax + shipping_fee),
        "profit": money(profit),
        "profit_margin": money(profit_margin),
        "price_per_piece": money(price_per_piece),
        "profit_per_piece": money(profit_per_piece),

        # Simple costing summary aligned with the tutorial formula:
        # SRP = Materials + Labor + Overhead + Profit.
        # This is saved in Sales Log cost_breakdown so logged sales,
        # receipts, and inventory deduction all use the same computed values.
        "simple_costing_summary": {
            "materials": money(total_material_cost),
            "labor": money(total_labor_cost),
            "overhead": money(total_additional_cost),
            "profit": money(profit),
            "srp": money(product_sale_price),
        },
    }


def _stock_is_deductible_status(status):
    return status not in [SaleLog.STATUS_CANCELLED, SaleLog.STATUS_REFUNDED]


def _deduct_material(material, qty, sale, sale_item, notes):
    qty = D(qty)
    if not material or qty <= 0:
        return

    locked = Material.objects.select_for_update().get(pk=material.pk)
    locked.deduct_stock(qty)
    StockMovement.objects.create(
        material=locked,
        sale=sale,
        sale_item=sale_item,
        movement_type=StockMovement.MOVEMENT_OUT,
        quantity=qty,
        balance_after=locked.stock_qty,
        notes=notes,
    )


def _restore_material(material, qty, sale, sale_item, notes):
    qty = D(qty)
    if not material or qty <= 0:
        return

    locked = Material.objects.select_for_update().get(pk=material.pk)
    locked.add_stock(qty)
    StockMovement.objects.create(
        material=locked,
        sale=sale,
        sale_item=sale_item,
        movement_type=StockMovement.MOVEMENT_REVERSAL,
        quantity=qty,
        balance_after=locked.stock_qty,
        notes=notes,
    )


@transaction.atomic
def create_sale_from_order_items(payload):
    items = payload.get("order_items") or []
    if not items:
        raise ValueError("Please add at least one item before logging the sale.")

    platform = payload.get("platform") or SaleLog.PLATFORM_WALKIN
    payment_method = payload.get("payment_method") or SaleLog.PAYMENT_CASH
    status = payload.get("status") or SaleLog.STATUS_PENDING
    shipping_fee = D(payload.get("shipping_fee"), "0")
    order_discount = D(payload.get("discount"), "0")

    computed_items = []
    total_qty = 0
    selling_price = Decimal("0")
    sales_tax = Decimal("0")
    cost = Decimal("0")
    platform_fee = Decimal("0")
    profit = Decimal("0")
    simple_materials_total = Decimal("0")
    simple_labor_total = Decimal("0")
    simple_overhead_total = Decimal("0")

    for item in items:
        quote_data = {
            "sticker_size_id": item.get("sticker_size_id") or item.get("sticker_size"),
            "quantity": item.get("quantity"),
            "material_id": item.get("material_id"),
            "lamination_id": item.get("lamination_id"),
            "packaging_id": item.get("packaging_id"),
            "ink_cost_per_sheet": item.get("ink_cost_per_sheet"),
            "labor_minutes": item.get("labor_minutes"),
            "additional_direct_cost": item.get("additional_direct_cost"),
            "target_sale_price": item.get("target_sale_price"),
            "platform": platform,
        }
        result = calculate_quote(quote_data)

        line_qty = int(D(item.get("quantity"), "0"))
        computed_items.append((item, result))
        total_qty += line_qty
        selling_price += D(result["product_sale_price"])
        sales_tax += D(result["sales_tax"])
        cost += D(result["total_product_cost"])
        platform_fee += D(result["marketplace_fee"])
        profit += D(result["profit"])
        simple_summary = result.get("simple_costing_summary", {})
        simple_materials_total += D(simple_summary.get("materials"), "0")
        simple_labor_total += D(simple_summary.get("labor"), "0")
        simple_overhead_total += D(simple_summary.get("overhead"), "0")

    profit -= order_discount
    simple_srp_total = selling_price
    simple_profit_total = profit

    sale = SaleLog.objects.create(
        customer_name=payload.get("customer_name", ""),
        order_name=payload.get("order_name", ""),
        sticker_size="Multiple Items" if len(computed_items) > 1 else computed_items[0][1]["sticker_size"],
        quantity=total_qty,
        selling_price=money(selling_price),
        shipping_fee=money(shipping_fee),
        discount=money(order_discount),
        platform_fee=money(platform_fee),
        sales_tax=money(sales_tax),
        cost=money(cost),
        profit=money(profit),
        platform=platform,
        payment_method=payment_method,
        status=status,
        platform_order_id=payload.get("platform_order_id", ""),
        tracking_number=payload.get("tracking_number", ""),
        courier=payload.get("courier", ""),
        buyer_username=payload.get("buyer_username", ""),
        buyer_phone=payload.get("buyer_phone", ""),
        shipping_address=payload.get("shipping_address", ""),
        weight_grams=int(D(payload.get("weight_grams"), "0")),
        due_date=payload.get("due_date") or None,
        rush_order=bool(payload.get("rush_order")),
        deposit_amount=money(D(payload.get("deposit_amount"), "0")),
        override_price=money(D(payload.get("override_price"), "0")),
        override_reason=payload.get("override_reason", ""),
        internal_job_notes=payload.get("internal_job_notes", ""),
        notes=payload.get("notes", "Logged from V3.4 daily operations engine"),
        cost_breakdown=serialize_for_jsonfield({
            "version": "v3.4_daily_operations",
            "simple_costing_summary": {
                "materials": money(simple_materials_total),
                "labor": money(simple_labor_total),
                "overhead": money(simple_overhead_total),
                "profit": money(simple_profit_total),
                "srp": money(simple_srp_total),
            },
            "inventory_sync": {
                "stock_deducted": _stock_is_deductible_status(status),
                "deducts_materials": True,
                "deducts_lamination": True,
                "deducts_packaging": True,
            },
            "items": [r for _, r in computed_items],
        }),
    )

    for index, (item, result) in enumerate(computed_items, start=1):
        material = get_object_or_none(Material, item.get("material_id"))
        lamination = get_object_or_none(Material, item.get("lamination_id"))
        packaging = get_object_or_none(Material, item.get("packaging_id"))

        sale_item = SaleLogItem.objects.create(
            sale=sale,
            line_number=index,
            sku=item.get("sku", ""),
            product_name=item.get("product_name", ""),
            sticker_size=result["sticker_size"],
            material=material,
            lamination=lamination,
            packaging=packaging,
            material_name=material.item_name if material else item.get("material_name", ""),
            lamination_name=lamination.item_name if lamination else item.get("lamination_name", ""),
            packaging_name=packaging.item_name if packaging else item.get("packaging_name", ""),
            quantity=int(D(item.get("quantity"), "0")),
            sheets_needed=int(D(result["sheets_needed"])),
            packaging_capacity=int(D(item.get("packaging_capacity"), "1")),
            material_qty_used=D(result["stock_plan"]["material_qty_used"]),
            lamination_qty_used=D(result["stock_plan"]["lamination_qty_used"]),
            packaging_qty_used=D(result["stock_plan"]["packaging_qty_used"]),
            unit_price=money(result["price_per_piece"]),
            line_total=money(result["product_sale_price"]),
            line_cost=money(result["total_product_cost"]),
            line_profit=money(result["profit"]),
            notes=item.get("notes", ""),
        )

        if _stock_is_deductible_status(sale.status):
            _deduct_material(material, sale_item.material_qty_used, sale, sale_item, "Deducted from sale")
            _deduct_material(lamination, sale_item.lamination_qty_used, sale, sale_item, "Deducted from sale")
            _deduct_material(packaging, sale_item.packaging_qty_used, sale, sale_item, "Deducted from sale")

    if _stock_is_deductible_status(sale.status):
        sale.stock_deducted = True
        sale.save(update_fields=["stock_deducted"])

    return sale


@transaction.atomic
def reverse_sale_inventory(sale):
    sale = SaleLog.objects.select_for_update().get(pk=sale.pk)
    if not sale.stock_deducted:
        return

    for item in sale.items.select_related("material", "lamination", "packaging"):
        _restore_material(item.material, item.material_qty_used, sale, item, "Restored from sale deletion/cancellation")
        _restore_material(item.lamination, item.lamination_qty_used, sale, item, "Restored from sale deletion/cancellation")
        _restore_material(item.packaging, item.packaging_qty_used, sale, item, "Restored from sale deletion/cancellation")

    sale.stock_deducted = False
    sale.save(update_fields=["stock_deducted"])


def _best_price_tier(product, quantity):
    quantity = int(quantity or 0)
    selected = None
    for tier in product.tiers.all().order_by("min_qty"):
        if quantity < tier.min_qty:
            continue
        if tier.max_qty and quantity > tier.max_qty:
            continue
        selected = tier
    return selected


def calculate_product_preset_quote(product_id, quantity, platform=None):
    """V3 product catalog pricing for stickers, photos, invitations, Cricut crafts, and event packages."""
    settings = PriceSetting.objects.first() or PriceSetting.objects.create()
    product = ProductPreset.objects.select_related(
        "category", "default_sticker_size", "main_material", "lamination", "packaging"
    ).get(pk=product_id)
    quantity = int(quantity or 0)
    if quantity < product.minimum_order_qty:
        quantity = product.minimum_order_qty

    units_per_sheet = D(product.units_per_sheet_override or 0)
    if units_per_sheet <= 0 and product.default_sticker_size:
        units_per_sheet = D(product.default_sticker_size.best_for_costing)
    if units_per_sheet <= 0:
        units_per_sheet = Decimal("1")

    sheets_needed = (D(quantity) / units_per_sheet).to_integral_value(rounding=ROUND_CEILING)

    material_cost = sheets_needed * D(product.main_material.unit_cost if product.main_material else 0)
    lamination_cost = sheets_needed * D(product.lamination.unit_cost if product.lamination else 0)
    packaging_qty = product.packaging.units_needed_for_quantity(quantity) if product.packaging else Decimal("0")
    packaging_cost = packaging_qty * D(product.packaging.unit_cost if product.packaging else 0)
    ink_cost = sheets_needed * D(product.ink_cost_per_sheet)
    base_material_cost = material_cost + lamination_cost + packaging_cost + ink_cost
    waste_cost = base_material_cost * D(product.waste_percent) / Decimal("100")

    labor_cost = D(product.handling_fee) + (sheets_needed * D(product.labor_per_sheet))
    overhead_cost = D(product.machine_overhead) + D(product.design_fee)
    total_cost = base_material_cost + waste_cost + labor_cost + overhead_cost

    margin_divisor = Decimal("1") - (D(product.target_margin_percent) / Decimal("100"))
    margin_price = total_cost if margin_divisor <= 0 else total_cost / margin_divisor
    markup_price = total_cost * (Decimal("1") + D(product.markup_percent) / Decimal("100"))

    tier = _best_price_tier(product, quantity)
    market_price = D(product.base_selling_price)
    tier_label = "Base price"
    if tier:
        tier_label = tier.label or f"{tier.min_qty}+ tier"
        if tier.fixed_bundle_price > 0 and tier.bundle_qty > 0:
            bundles = (D(quantity) / D(tier.bundle_qty)).to_integral_value(rounding=ROUND_CEILING)
            market_price = bundles * D(tier.fixed_bundle_price)
        elif tier.unit_price > 0:
            market_price = D(quantity) * D(tier.unit_price)
    elif product.base_selling_price > 0 and product.base_quantity > 0:
        bundles = (D(quantity) / D(product.base_quantity)).to_integral_value(rounding=ROUND_CEILING)
        market_price = bundles * D(product.base_selling_price)

    floor_price = D(product.minimum_order_price) if product.minimum_order_price > 0 else D(settings.minimum_order_price)
    selling_price = max(market_price, margin_price, markup_price, floor_price)
    selling_price = round_selling_price(selling_price, settings.rounding_mode)

    marketplace_percent = get_marketplace_fee_percent(platform or SaleLog.PLATFORM_WALKIN)
    marketplace_fixed = get_marketplace_fixed_fee(platform or SaleLog.PLATFORM_WALKIN)
    marketplace_fee = selling_price * D(marketplace_percent) / Decimal("100") + D(marketplace_fixed)

    profit = selling_price - total_cost - marketplace_fee
    profit_margin = Decimal("0") if selling_price <= 0 else (profit / selling_price) * Decimal("100")
    price_per_piece = Decimal("0") if quantity <= 0 else selling_price / D(quantity)

    warnings = []
    if quantity >= product.manual_quote_above_qty:
        warnings.append("Manual quote recommended: quantity is above this product's machine/capacity threshold.")
    elif quantity >= product.max_daily_qty:
        warnings.append("Capacity warning: this may need longer lead time on Canon G670 / Cricut workflow.")
    if product.main_material and product.main_material.stock_qty < sheets_needed:
        warnings.append(f"Low stock: {product.main_material.item_name} has {product.main_material.stock_qty}, needs {sheets_needed}.")

    return {
        "version": "v3_product_catalog",
        "product_id": product.id,
        "product_name": product.name,
        "category": product.category.name,
        "pricing_type": product.category.pricing_type,
        "quantity": quantity,
        "sheets_needed": int(sheets_needed),
        "units_per_sheet": int(units_per_sheet),
        "tier_label": tier_label,
        "lead_time_note": product.lead_time_note,
        "warnings": warnings,
        "material_cost": money(material_cost),
        "lamination_cost": money(lamination_cost),
        "packaging_cost": money(packaging_cost),
        "ink_cost": money(ink_cost),
        "waste_cost": money(waste_cost),
        "labor_cost": money(labor_cost),
        "overhead_cost": money(overhead_cost),
        "total_cost": money(total_cost),
        "market_price": money(market_price),
        "markup_price": money(markup_price),
        "margin_price": money(margin_price),
        "selling_price": money(selling_price),
        "price_per_piece": money(price_per_piece),
        "marketplace_fee": money(marketplace_fee),
        "profit": money(profit),
        "profit_margin": money(profit_margin),
    }


def save_product_quote(product_id, quantity, customer_name="", notes="", platform=None):
    result = calculate_product_preset_quote(product_id, quantity, platform=platform)
    quote = CraftQuote.objects.create(
        product_id=product_id,
        customer_name=customer_name or "",
        quantity=result["quantity"],
        selected_tier_label=result["tier_label"],
        total_cost=result["total_cost"],
        selling_price=result["selling_price"],
        profit=result["profit"],
        profit_margin=result["profit_margin"],
        notes=notes or "",
        cost_breakdown=serialize_for_jsonfield(result),
    )
    return quote, result


# -----------------------------
# V5 Smart Paste / Smart Parse
# -----------------------------
import re
from datetime import timedelta as _timedelta
from django.utils import timezone as _timezone


def _smart_find(pattern, text, flags=re.IGNORECASE):
    match = re.search(pattern, text or "", flags)
    return match.group(1).strip() if match else ""


def _normalize_chat_text(text):
    return " ".join((text or "").replace("×", "x").replace("X", "x").split())


def parse_smart_paste_message(raw_message):
    """Parse common PH/Facebook/Messenger print-craft inquiries into draft fields.

    This is intentionally deterministic and offline: regex + keyword rules, not an API.
    It is safe for local use and can be improved over time with your real customer messages.
    """
    text = _normalize_chat_text(raw_message)
    lower = text.lower()
    confidence = 0

    qty_patterns = [
        r"(?:qty|quantity|pcs|pieces|piraso|pc)\s*[:\-]?\s*(\d+)",
        r"(\d+)\s*(?:pcs|pieces|pc|piraso|stickers?|labels?|cards?|invites?|invitations?)",
        r"(?:need|gusto|pa(?:-|\s)?print|print|order)\s*(?:ng|of)?\s*(\d+)",
    ]
    quantity = 1
    for pat in qty_patterns:
        found = _smart_find(pat, lower)
        if found:
            quantity = max(1, int(found))
            confidence += 15
            break

    size_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:in|inch|inches|\")?\s*x\s*(\d+(?:\.\d+)?)\s*(?:in|inch|inches|\")?", lower)
    width = height = None
    if size_match:
        width = Decimal(size_match.group(1))
        height = Decimal(size_match.group(2))
        confidence += 20

    cm_match = re.search(r"(\d+(?:\.\d+)?)\s*cm\s*x\s*(\d+(?:\.\d+)?)\s*cm", lower)
    if cm_match:
        width = (Decimal(cm_match.group(1)) / Decimal("2.54")).quantize(Decimal("0.01"))
        height = (Decimal(cm_match.group(2)) / Decimal("2.54")).quantize(Decimal("0.01"))
        confidence += 20

    product_type = "STICKER"
    product_name = "Custom sticker"
    if any(word in lower for word in ["photo", "4r", "picture", "passport"]):
        product_type = "PHOTO"
        product_name = "Photo print"
    elif any(word in lower for word in ["invitation", "invite", "wedding", "birthday", "card", "thank you"]):
        product_type = "INVITATION"
        product_name = "Invitation / card"
    elif any(word in lower for word in ["topper", "cake topper", "decal", "vinyl cut", "name cut", "cricut"]):
        product_type = "CRICUT"
        product_name = "Cricut craft"
    elif any(word in lower for word in ["logo", "label", "sticker", "waterproof", "hologram"]):
        product_type = "STICKER"
        product_name = "Custom stickers / labels"
    if product_name:
        confidence += 10

    material_keyword = ""
    if "holo" in lower or "hologram" in lower:
        material_keyword = "hologram"
    elif "matte" in lower:
        material_keyword = "matte"
    elif "gloss" in lower:
        material_keyword = "glossy"
    elif "vinyl" in lower:
        material_keyword = "vinyl"
    elif "photo paper" in lower:
        material_keyword = "photo paper"
    elif "magnet" in lower or "magnetic" in lower:
        material_keyword = "magnetic"
    if material_keyword:
        confidence += 10

    finish_keyword = ""
    if any(w in lower for w in ["laminated", "lamination", "laminate"]):
        finish_keyword = "laminated"
    elif "waterproof" in lower:
        finish_keyword = "waterproof"
    elif "kiss cut" in lower or "kisscut" in lower:
        finish_keyword = "kiss cut"
    elif "die cut" in lower or "cutout" in lower or "cut out" in lower:
        finish_keyword = "die cut"
    if finish_keyword:
        confidence += 8

    customer_name = ""
    name_patterns = [
        r"(?:name|customer|client)\s*[:\-]\s*([A-Za-z ñÑ.'-]{2,60})",
        r"(?:ako si|i am|this is)\s+([A-Za-z ñÑ.'-]{2,60})",
    ]
    for pat in name_patterns:
        found = _smart_find(pat, text)
        if found:
            customer_name = found[:60]
            confidence += 8
            break

    deadline_text = ""
    if any(w in lower for w in ["today", "ngayon", "same day"]):
        deadline_text = "Today"
    elif any(w in lower for w in ["tomorrow", "bukas"]):
        deadline_text = "Tomorrow"
    else:
        date_hint = _smart_find(r"(?:due|need|needed|deadline|pickup|kuha)\s*(?:on|by|sa)?\s*([A-Za-z0-9 ,/-]{3,40})", text)
        deadline_text = date_hint[:80]
    if deadline_text:
        confidence += 8

    delivery_method = ""
    if any(w in lower for w in ["pickup", "pick up", "claim", "kuhain"]):
        delivery_method = "Pickup"
    elif any(w in lower for w in ["deliver", "delivery", "shipping", "ship", "lalamove", "j&t", "jnt"]):
        delivery_method = "Delivery"

    payment_method = ""
    if "gcash" in lower:
        payment_method = "GCash"
    elif "cash" in lower:
        payment_method = "Cash"
    elif "maya" in lower:
        payment_method = "Maya"

    warnings = []
    if not size_match and not cm_match:
        warnings.append("No clear size detected. Confirm width and height.")
    if quantity == 1 and not re.search(r"\b1\s*(?:pc|pcs|piece|pieces)\b", lower):
        warnings.append("No clear quantity detected. Defaulted to 1.")
    if not material_keyword:
        warnings.append("No material/finish detected. Confirm material before quoting.")

    suggested_reply = (
        f"Hi! I parsed your request as {quantity} pc(s) of {product_name}"
        + (f", size {width} x {height} in" if width and height else "")
        + (f", {material_keyword}" if material_keyword else "")
        + (f", {finish_keyword}" if finish_keyword else "")
        + ". Please confirm if these details are correct so we can compute the final price 😊"
    )

    return {
        "raw_message": raw_message or "",
        "customer_name": customer_name,
        "product_name": product_name,
        "product_type": product_type,
        "quantity": quantity,
        "width_in": str(width) if width is not None else "",
        "height_in": str(height) if height is not None else "",
        "material_keyword": material_keyword,
        "finish_keyword": finish_keyword,
        "deadline_text": deadline_text,
        "delivery_method": delivery_method,
        "payment_method": payment_method,
        "confidence_score": min(confidence, 100),
        "warnings": warnings,
        "suggested_reply": suggested_reply,
    }


def create_smart_paste_inquiry(raw_message):
    from .models import SmartPasteInquiry
    parsed = parse_smart_paste_message(raw_message)
    inquiry = SmartPasteInquiry.objects.create(
        raw_message=raw_message or "",
        customer_name=parsed.get("customer_name", ""),
        product_name=parsed.get("product_name", ""),
        product_type=parsed.get("product_type", "STICKER"),
        quantity=parsed.get("quantity") or 1,
        width_in=Decimal(parsed["width_in"]) if parsed.get("width_in") else None,
        height_in=Decimal(parsed["height_in"]) if parsed.get("height_in") else None,
        material_keyword=parsed.get("material_keyword", ""),
        finish_keyword=parsed.get("finish_keyword", ""),
        deadline_text=parsed.get("deadline_text", ""),
        delivery_method=parsed.get("delivery_method", ""),
        payment_method=parsed.get("payment_method", ""),
        parsed_data=parsed,
        suggested_reply=parsed.get("suggested_reply", ""),
        confidence_score=parsed.get("confidence_score") or 0,
    )
    return inquiry, parsed
