from decimal import Decimal
from django.core.management.base import BaseCommand
from costing.models import QuickPOSProduct, ProductCategory, ProductPreset, Material


class Command(BaseCommand):
    help = "Seed V3.7 fast POS buttons linked to current Materials Master costs."

    def handle(self, *args, **options):
        sticker_category = ProductCategory.objects.filter(pricing_type=ProductCategory.PRICING_STICKER).first()
        photo_category = ProductCategory.objects.filter(pricing_type=ProductCategory.PRICING_PHOTO).first()
        main_material = Material.objects.filter(category=Material.CATEGORY_STICKER, is_active=True).first()
        lamination = Material.objects.filter(category=Material.CATEGORY_LAMINATION, is_active=True).first()
        packaging = Material.objects.filter(category=Material.CATEGORY_PACKAGING, is_active=True).first()

        defaults = [
            {
                "name": "Waterproof Stickers 4 for 100",
                "button_label": "4 for ₱100",
                "product_type": sticker_category,
                "selling_price": Decimal("100.00"),
                "bundle_quantity": 4,
                "sheets_per_bundle": Decimal("1.00"),
                "main_material": main_material,
                "lamination": None,
                "packaging": packaging,
                "packaging_quantity": Decimal("1.00"),
                "target_margin_percent": Decimal("45.00"),
            },
            {
                "name": "Mini Magnets 3 for 100",
                "button_label": "3 for ₱100",
                "product_type": sticker_category,
                "selling_price": Decimal("100.00"),
                "bundle_quantity": 3,
                "sheets_per_bundle": Decimal("1.00"),
                "main_material": main_material,
                "lamination": lamination,
                "packaging": packaging,
                "packaging_quantity": Decimal("1.00"),
                "target_margin_percent": Decimal("45.00"),
            },
            {
                "name": "Face Cutout Waterproof Pack",
                "button_label": "15 pcs ₱250",
                "product_type": sticker_category,
                "selling_price": Decimal("250.00"),
                "bundle_quantity": 15,
                "sheets_per_bundle": Decimal("2.00"),
                "main_material": main_material,
                "lamination": lamination,
                "packaging": packaging,
                "packaging_quantity": Decimal("1.00"),
                "target_margin_percent": Decimal("40.00"),
            },
            {
                "name": "4R Photo Print",
                "button_label": "4R Photo",
                "product_type": photo_category,
                "selling_price": Decimal("25.00"),
                "bundle_quantity": 1,
                "sheets_per_bundle": Decimal("1.00"),
                "main_material": main_material,
                "lamination": None,
                "packaging": packaging,
                "packaging_quantity": Decimal("1.00"),
                "target_margin_percent": Decimal("35.00"),
            },
        ]

        created = 0
        for row in defaults:
            _, was_created = QuickPOSProduct.objects.update_or_create(
                name=row["name"],
                defaults=row,
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"V3.7 POS seed complete. Created {created} new POS products."))
