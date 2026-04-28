# Generated manually for V3 product catalog.
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('costing', '0010_v21_sheet_based_labor'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('pricing_type', models.CharField(choices=[('STICKER', 'Sticker / Label'), ('PHOTO', 'Photo Print'), ('INVITATION', 'Invitation / Card'), ('CRICUT', 'Cricut Craft'), ('EVENT', 'Event Package'), ('OTHER', 'Other Custom')], default='OTHER', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='ProductPreset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160)),
                ('sku', models.CharField(blank=True, max_length=80)),
                ('description', models.TextField(blank=True)),
                ('base_selling_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Fixed or bundle selling price before add-ons/shipping.', max_digits=12)),
                ('base_quantity', models.PositiveIntegerField(default=1, help_text='How many pieces/sets are included in base selling price.')),
                ('minimum_order_qty', models.PositiveIntegerField(default=1)),
                ('minimum_order_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('target_margin_percent', models.DecimalField(decimal_places=2, default=Decimal('35.00'), max_digits=7)),
                ('markup_percent', models.DecimalField(decimal_places=2, default=Decimal('45.00'), max_digits=7)),
                ('waste_percent', models.DecimalField(decimal_places=2, default=Decimal('7.00'), max_digits=7)),
                ('handling_fee', models.DecimalField(decimal_places=2, default=Decimal('10.00'), max_digits=10)),
                ('labor_per_sheet', models.DecimalField(decimal_places=2, default=Decimal('2.00'), max_digits=10)),
                ('machine_overhead', models.DecimalField(decimal_places=2, default=Decimal('5.00'), max_digits=10)),
                ('design_fee', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('max_daily_qty', models.PositiveIntegerField(default=300, help_text='Soft warning only. Does not block sales.')),
                ('manual_quote_above_qty', models.PositiveIntegerField(default=500, help_text='Show manual quote warning above this quantity.')),
                ('lead_time_note', models.CharField(blank=True, max_length=160)),
                ('ink_cost_per_sheet', models.DecimalField(decimal_places=2, default=Decimal('3.00'), max_digits=10)),
                ('units_per_sheet_override', models.PositiveIntegerField(default=0, help_text='Optional. Leave 0 to use sticker size fit.')),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='costing.productcategory')),
                ('default_sticker_size', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='costing.stickersize')),
                ('lamination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='preset_laminations', to='costing.material')),
                ('main_material', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='preset_main_materials', to='costing.material')),
                ('packaging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='preset_packagings', to='costing.material')),
            ],
            options={'ordering': ['category__name', 'name'], 'unique_together': {('category', 'name')}},
        ),
        migrations.CreateModel(
            name='ProductPriceTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_qty', models.PositiveIntegerField(default=1)),
                ('max_qty', models.PositiveIntegerField(blank=True, null=True)),
                ('fixed_bundle_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Use for bundle price such as 4 for 100.', max_digits=12)),
                ('bundle_qty', models.PositiveIntegerField(default=0, help_text='How many pieces included in fixed bundle price. Leave 0 for unit price.')),
                ('unit_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Fallback price per piece/set in this tier.', max_digits=12)),
                ('label', models.CharField(blank=True, max_length=120)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tiers', to='costing.productpreset')),
            ],
            options={'ordering': ['product', 'min_qty']},
        ),
        migrations.CreateModel(
            name='CraftQuote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer_name', models.CharField(blank=True, max_length=120)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('selected_tier_label', models.CharField(blank=True, max_length=120)),
                ('total_cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('selling_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('profit', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('profit_margin', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=7)),
                ('cost_breakdown', models.JSONField(blank=True, default=dict)),
                ('notes', models.TextField(blank=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='quotes', to='costing.productpreset')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
