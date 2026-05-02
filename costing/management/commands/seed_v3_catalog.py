from decimal import Decimal
from django.core.management.base import BaseCommand
from costing.models import ProductCategory, ProductPreset, ProductPriceTier, Material, StickerSize


class Command(BaseCommand):
    help = "Seeds V3 product catalog presets for a Canon G670 + Cricut print/craft studio. Run after seed_demo_data."

    def handle(self, *args, **options):
        cat_sticker, _ = ProductCategory.objects.get_or_create(
            name='Waterproof Stickers / Labels',
            defaults={'pricing_type': ProductCategory.PRICING_STICKER, 'description': 'Retail sticker bundles and small-batch logo labels.'}
        )
        cat_photo, _ = ProductCategory.objects.get_or_create(
            name='Photo Prints',
            defaults={'pricing_type': ProductCategory.PRICING_PHOTO, 'description': '4R, A5, A4 photo prints using Canon G670.'}
        )
        cat_invite, _ = ProductCategory.objects.get_or_create(
            name='Invitations / Cards',
            defaults={'pricing_type': ProductCategory.PRICING_INVITATION, 'description': 'Birthday, wedding, baptism and event cards.'}
        )
        cat_cricut, _ = ProductCategory.objects.get_or_create(
            name='Cricut Crafts',
            defaults={'pricing_type': ProductCategory.PRICING_CRICUT, 'description': 'Cake toppers, decals, tags, names, layered crafts.'}
        )
        cat_event, _ = ProductCategory.objects.get_or_create(
            name='Event Packages',
            defaults={'pricing_type': ProductCategory.PRICING_EVENT, 'description': 'Bundled event sets for birthdays, weddings and small businesses.'}
        )

        vinyl = Material.objects.filter(item_name__icontains='Waterproof A4 White Matte').first() or Material.objects.filter(category=Material.CATEGORY_STICKER).first()
        glossy = Material.objects.filter(item_name__icontains='Glossy').first() or vinyl
        laminate = Material.objects.filter(category=Material.CATEGORY_LAMINATION).first()
        opp = Material.objects.filter(category=Material.CATEGORY_PACKAGING).first()
        size_2x2 = StickerSize.objects.filter(name='2 x 2 in').first()
        size_2x15 = StickerSize.objects.filter(name='2 x 1.5 in').first()

        retail, _ = ProductPreset.objects.get_or_create(category=cat_sticker, name='Retail Waterproof Stickers - 4 for ₱100', defaults={
            'description': 'Kiosk/market style ready-made waterproof sticker bundle.',
            'base_selling_price': Decimal('100.00'), 'base_quantity': 4,
            'minimum_order_qty': 4, 'minimum_order_price': Decimal('100.00'),
            'target_margin_percent': Decimal('45.00'), 'markup_percent': Decimal('60.00'), 'waste_percent': Decimal('8.00'),
            'handling_fee': Decimal('10.00'), 'labor_per_sheet': Decimal('2.00'), 'machine_overhead': Decimal('5.00'),
            'max_daily_qty': 200, 'manual_quote_above_qty': 300, 'lead_time_note': 'Good for ready-made retail bundles.',
            'default_sticker_size': size_2x2, 'main_material': vinyl, 'packaging': opp,
            'ink_cost_per_sheet': Decimal('3.00')
        })
        ProductPriceTier.objects.get_or_create(product=retail, min_qty=1, max_qty=1, defaults={'unit_price': Decimal('35.00'), 'label': 'Single ₱35'})
        ProductPriceTier.objects.get_or_create(product=retail, min_qty=2, max_qty=3, defaults={'fixed_bundle_price': Decimal('60.00'), 'bundle_qty': 2, 'label': '2 for ₱60'})
        ProductPriceTier.objects.get_or_create(product=retail, min_qty=4, max_qty=7, defaults={'fixed_bundle_price': Decimal('100.00'), 'bundle_qty': 4, 'label': '4 for ₱100'})
        ProductPriceTier.objects.get_or_create(product=retail, min_qty=8, max_qty=99, defaults={'fixed_bundle_price': Decimal('180.00'), 'bundle_qty': 8, 'label': '8 for ₱180'})

        logo, _ = ProductPreset.objects.get_or_create(category=cat_sticker, name='Small-Batch Logo Stickers', defaults={
            'description': 'For customers who cannot meet 500 pcs MOQ. Protect Canon G670 capacity.',
            'base_selling_price': Decimal('180.00'), 'base_quantity': 50,
            'minimum_order_qty': 20, 'minimum_order_price': Decimal('149.00'),
            'target_margin_percent': Decimal('35.00'), 'markup_percent': Decimal('45.00'), 'waste_percent': Decimal('7.00'),
            'handling_fee': Decimal('20.00'), 'labor_per_sheet': Decimal('2.50'), 'machine_overhead': Decimal('8.00'),
            'max_daily_qty': 300, 'manual_quote_above_qty': 500, 'lead_time_note': '500+ should be manual quote / scheduled production.',
            'default_sticker_size': size_2x15, 'main_material': vinyl, 'packaging': opp,
            'ink_cost_per_sheet': Decimal('3.00')
        })
        ProductPriceTier.objects.get_or_create(product=logo, min_qty=20, max_qty=49, defaults={'unit_price': Decimal('4.00'), 'label': 'Small MOQ ₱4 each'})
        ProductPriceTier.objects.get_or_create(product=logo, min_qty=50, max_qty=99, defaults={'unit_price': Decimal('3.20'), 'label': '50+ ₱3.20 each'})
        ProductPriceTier.objects.get_or_create(product=logo, min_qty=100, max_qty=299, defaults={'unit_price': Decimal('2.50'), 'label': '100+ ₱2.50 each'})
        ProductPriceTier.objects.get_or_create(product=logo, min_qty=300, max_qty=499, defaults={'unit_price': Decimal('1.80'), 'label': '300+ ₱1.80 each'})

        photo, _ = ProductPreset.objects.get_or_create(category=cat_photo, name='Photo Print 4R / Small Photo', defaults={
            'description': 'Simple photo print preset. Adjust material to your actual photo paper.',
            'base_selling_price': Decimal('15.00'), 'base_quantity': 1,
            'minimum_order_qty': 1, 'minimum_order_price': Decimal('15.00'),
            'target_margin_percent': Decimal('40.00'), 'markup_percent': Decimal('70.00'), 'waste_percent': Decimal('5.00'),
            'handling_fee': Decimal('5.00'), 'labor_per_sheet': Decimal('1.50'), 'machine_overhead': Decimal('3.00'),
            'max_daily_qty': 100, 'manual_quote_above_qty': 200,
            'main_material': glossy, 'ink_cost_per_sheet': Decimal('5.00'), 'units_per_sheet_override': 4,
        })
        ProductPriceTier.objects.get_or_create(product=photo, min_qty=1, max_qty=9, defaults={'unit_price': Decimal('15.00'), 'label': '1-9 pcs ₱15 each'})
        ProductPriceTier.objects.get_or_create(product=photo, min_qty=10, max_qty=99, defaults={'unit_price': Decimal('12.00'), 'label': '10+ ₱12 each'})

        invite, _ = ProductPreset.objects.get_or_create(category=cat_invite, name='Birthday / Wedding Invitation Card', defaults={
            'description': 'Printed invite/card. Add design fee for custom layouts.',
            'base_selling_price': Decimal('350.00'), 'base_quantity': 20,
            'minimum_order_qty': 10, 'minimum_order_price': Decimal('249.00'),
            'target_margin_percent': Decimal('45.00'), 'markup_percent': Decimal('70.00'), 'waste_percent': Decimal('8.00'),
            'handling_fee': Decimal('30.00'), 'labor_per_sheet': Decimal('3.00'), 'machine_overhead': Decimal('10.00'), 'design_fee': Decimal('100.00'),
            'max_daily_qty': 100, 'manual_quote_above_qty': 200,
            'main_material': glossy, 'packaging': opp, 'ink_cost_per_sheet': Decimal('6.00'), 'units_per_sheet_override': 2,
        })
        ProductPriceTier.objects.get_or_create(product=invite, min_qty=10, max_qty=19, defaults={'unit_price': Decimal('20.00'), 'label': '10-19 pcs ₱20 each'})
        ProductPriceTier.objects.get_or_create(product=invite, min_qty=20, max_qty=49, defaults={'unit_price': Decimal('17.50'), 'label': '20+ ₱17.50 each'})
        ProductPriceTier.objects.get_or_create(product=invite, min_qty=50, max_qty=99, defaults={'unit_price': Decimal('15.00'), 'label': '50+ ₱15 each'})

        cricut, _ = ProductPreset.objects.get_or_create(category=cat_cricut, name='Cricut Cake Topper / Custom Name', defaults={
            'description': 'High-margin Cricut craft preset with design and machine handling.',
            'base_selling_price': Decimal('149.00'), 'base_quantity': 1,
            'minimum_order_qty': 1, 'minimum_order_price': Decimal('149.00'),
            'target_margin_percent': Decimal('55.00'), 'markup_percent': Decimal('100.00'), 'waste_percent': Decimal('10.00'),
            'handling_fee': Decimal('40.00'), 'labor_per_sheet': Decimal('5.00'), 'machine_overhead': Decimal('15.00'), 'design_fee': Decimal('50.00'),
            'max_daily_qty': 20, 'manual_quote_above_qty': 30,
            'main_material': glossy, 'ink_cost_per_sheet': Decimal('4.00'), 'units_per_sheet_override': 1,
        })
        ProductPriceTier.objects.get_or_create(product=cricut, min_qty=1, max_qty=2, defaults={'unit_price': Decimal('149.00'), 'label': 'Basic topper ₱149'})
        ProductPriceTier.objects.get_or_create(product=cricut, min_qty=3, max_qty=9, defaults={'unit_price': Decimal('129.00'), 'label': '3+ ₱129 each'})

        ProductPreset.objects.get_or_create(category=cat_event, name='Birthday Starter Print + Craft Package', defaults={
            'description': 'Starter package: invites, labels/stickers, small toppers/tags. Edit to your real offer.',
            'base_selling_price': Decimal('999.00'), 'base_quantity': 1,
            'minimum_order_qty': 1, 'minimum_order_price': Decimal('999.00'),
            'target_margin_percent': Decimal('50.00'), 'markup_percent': Decimal('90.00'), 'waste_percent': Decimal('10.00'),
            'handling_fee': Decimal('100.00'), 'labor_per_sheet': Decimal('5.00'), 'machine_overhead': Decimal('30.00'), 'design_fee': Decimal('250.00'),
            'max_daily_qty': 5, 'manual_quote_above_qty': 10,
            'main_material': glossy, 'lamination': laminate, 'packaging': opp, 'ink_cost_per_sheet': Decimal('8.00'), 'units_per_sheet_override': 1,
        })

        self.stdout.write(self.style.SUCCESS('V3 product catalog seeded.'))
