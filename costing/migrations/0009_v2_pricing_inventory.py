# V2 pricing and inventory safety migration

from decimal import Decimal
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("costing", "0008_material_stock_qty_salelogitem_lamination_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="material",
            name="reorder_level",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), help_text="Low stock warning level.", max_digits=12),
        ),
        migrations.AddField(
            model_name="material",
            name="sku",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="material",
            name="supplier",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="pricesetting",
            name="minimum_order_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("99.00"), help_text="Lowest allowed product selling price before shipping/tax.", max_digits=10),
        ),
        migrations.AddField(
            model_name="pricesetting",
            name="default_waste_percent",
            field=models.DecimalField(decimal_places=2, default=Decimal("7.00"), help_text="Extra buffer for misprints, test cuts, and spoilage.", max_digits=7),
        ),
        migrations.AddField(
            model_name="pricesetting",
            name="default_marketplace_fee_percent",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), help_text="Fallback selling fee when no marketplace-specific rule exists.", max_digits=7),
        ),
        migrations.AddField(
            model_name="pricesetting",
            name="rounding_mode",
            field=models.CharField(choices=[("NONE", "No rounding"), ("WHOLE", "Round up to whole peso"), ("ENDING_9", "Round up to next price ending in 9")], default="ENDING_9", max_length=20),
        ),
        migrations.AddField(
            model_name="salelog",
            name="stock_deducted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="salelog",
            name="cost_breakdown",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.CreateModel(
            name="MarketplaceFee",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("platform", models.CharField(choices=[("Walk-in", "Walk-in"), ("Shopee", "Shopee"), ("Lazada", "Lazada"), ("TikTok Shop", "TikTok Shop"), ("Facebook", "Facebook"), ("Instagram", "Instagram"), ("Other", "Other")], max_length=50, unique=True)),
                ("fee_percent", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=7)),
                ("fixed_fee", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["platform"]},
        ),
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("movement_type", models.CharField(choices=[("IN", "Stock In"), ("OUT", "Stock Out / Sale"), ("REVERSAL", "Sale Reversal"), ("ADJUSTMENT", "Adjustment")], max_length=20)),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=12)),
                ("balance_after", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("material", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="stock_movements", to="costing.material")),
                ("sale", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="stock_movements", to="costing.salelog")),
                ("sale_item", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="stock_movements", to="costing.salelogitem")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
