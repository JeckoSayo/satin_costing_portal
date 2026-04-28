from decimal import Decimal
from django.core.management.base import BaseCommand
from costing.models import PaperSize, StickerSize, Material, PriceSetting, EquipmentOverhead, MarketplaceFee, SaleLog, ProductCategory, ProductPreset, ProductPriceTier


class Command(BaseCommand):
    help = 'Seeds demo data based on the Excel costing calculator.'

    def handle(self, *args, **options):
        settings, _ = PriceSetting.objects.get_or_create(id=1)
        settings.orders_per_month = Decimal('30.00')
        settings.labor_rate_per_hour = Decimal('80.00')
        settings.default_ink_cost_per_sheet = Decimal('3.00')
        settings.default_markup_percent = Decimal('45.00')
        settings.default_margin_percent = Decimal('35.00')
        settings.default_discount_percent = Decimal('0.00')
        settings.default_sales_tax_percent = Decimal('0.00')
        settings.safety_buffer_per_order = Decimal('10.00')
        settings.additional_direct_cost = Decimal('0.08')
        settings.base_handling_fee = Decimal('10.00')
        settings.labor_per_sheet = Decimal('2.00')
        settings.blade_wear_per_sheet = Decimal('1.00')
        settings.machine_overhead_per_order = Decimal('5.00')
        settings.minimum_order_price = Decimal('149.00')
        settings.default_waste_percent = Decimal('7.00')
        settings.default_marketplace_fee_percent = Decimal('0.00')
        settings.rounding_mode = 'ENDING_9'
        settings.save()

        marketplace_defaults = [
            (SaleLog.PLATFORM_SHOPEE, Decimal('8.00'), Decimal('0.00')),
            (SaleLog.PLATFORM_LAZADA, Decimal('8.00'), Decimal('0.00')),
            (SaleLog.PLATFORM_TIKTOK, Decimal('7.00'), Decimal('0.00')),
            (SaleLog.PLATFORM_FACEBOOK, Decimal('0.00'), Decimal('0.00')),
            (SaleLog.PLATFORM_WALKIN, Decimal('0.00'), Decimal('0.00')),
        ]
        for platform, percent, fixed in marketplace_defaults:
            MarketplaceFee.objects.get_or_create(
                platform=platform,
                defaults={'fee_percent': percent, 'fixed_fee': fixed, 'notes': 'Edit this to match your current actual seller fees.'}
            )

        a4, _ = PaperSize.objects.get_or_create(
            name='A4',
            defaults={
                'width_in': Decimal('8.27'),
                'height_in': Decimal('11.69'),
                'use_cricut_safe_area': True,
            }
        )
        PaperSize.objects.get_or_create(name='Short Letter', defaults={'width_in': Decimal('8.50'), 'height_in': Decimal('11.00')})
        PaperSize.objects.get_or_create(name='Long Bond', defaults={'width_in': Decimal('8.50'), 'height_in': Decimal('13.00')})
        PaperSize.objects.get_or_create(name='Letter', defaults={'width_in': Decimal('8.50'), 'height_in': Decimal('11.00')})

        for name, w, h, cricut in [
            ('0.75 x 0.75 in', '0.75', '0.75', True),
            ('1 x 1 in', '1.00', '1.00', True),
            ('1.25 x 1.25 in', '1.25', '1.25', True),
            ('1.5 x 1.5 in', '1.50', '1.50', True),
            ('1.75 x 1.75 in', '1.75', '1.75', True),
            ('2 x 1.5 in', '2.00', '1.50', True),
            ('2 x 2 in', '2.00', '2.00', True),
            ('2.5 x 2.5 in', '2.50', '2.50', True),
            ('3.2 x 4.5 in', '3.20', '4.50', True),
        ]:
            StickerSize.objects.get_or_create(name=name, paper_size=a4, defaults={'width_in': Decimal(w), 'height_in': Decimal(h), 'use_cricut_safe_area': cricut})

        data = [
            (Material.CATEGORY_PACKAGING, 'OPP Plastic Bag With Adhesive 3.5x5', '41.00', '100', 'pcs', '100 pcs pack'),
            (Material.CATEGORY_STICKER, 'Yasen A4 Inkjet Sticker Glossy', '189.00', '100', 'sheets', '100 sheets pack'),
            (Material.CATEGORY_LAMINATION, 'Yasen A4 Cold Lamination Premium Rainbow', '129.00', '20', 'sheets', '20 sheets pack'),
            (Material.CATEGORY_LAMINATION, 'Yasen A4 Cold Lamination Hologram Broken', '99.00', '20', 'sheets', '20 sheets pack'),
            (Material.CATEGORY_LAMINATION, 'Yasen A4 Cold Lamination Hologram Fireworks', '99.00', '20', 'sheets', '20 sheets pack'),
            (Material.CATEGORY_LAMINATION, 'Yasen A4 Cold Lamination Leather Texture', '99.00', '20', 'sheets', '20 sheets pack'),
            (Material.CATEGORY_STICKER, 'Yasen Matte Label Sticker Paper 150gsm', '59.00', '20', 'sheets', '20 sheets pack'),
            (Material.CATEGORY_STICKER, 'Yasen ATM Magnetic Sheet With Adhesive 1mm', '26.00', '10', 'sheets', '10 sheets pack'),
            (Material.CATEGORY_STICKER, 'Quaff Vinyl Inkjet Sticker Waterproof A4 White Glossy', '180.00', '22', 'sheets', '22 sheets based on 20+2 listing'),
            (Material.CATEGORY_STICKER, 'Quaff Vinyl Inkjet Sticker Waterproof A4 Semi-Clear', '180.00', '22', 'sheets', '22 sheets based on 20+2 listing'),
            (Material.CATEGORY_STICKER, 'Quaff Vinyl Inkjet Sticker Waterproof A4 White Matte', '150.00', '22', 'sheets', '22 sheets based on 20+2 listing'),
            (Material.CATEGORY_STICKER, 'Quaff A4 Double Sided Glossy Photo Paper 200gsm', '128.00', '20', 'sheets', 'Pack qty estimated'),
            (Material.CATEGORY_INK, 'Canon G670 Ink Refill', '800.00', '1', 'prints', 'Estimate based on yield; edit actual yield'),
        ]
        for category, name, price, qty, unit, notes in data:
            Material.objects.get_or_create(item_name=name, defaults={'category': category, 'pack_price': Decimal(price), 'pack_qty': Decimal(qty), 'stock_qty': Decimal(qty), 'reorder_level': Decimal(qty) * Decimal('0.25'), 'unit': unit, 'notes': notes})

        EquipmentOverhead.objects.get_or_create(name='Equipment Overhead', defaults={'monthly_cost': Decimal('1294.20'), 'notes': 'Monthly overhead divided by orders per month'})
        self.stdout.write(self.style.SUCCESS('Demo data seeded.'))
