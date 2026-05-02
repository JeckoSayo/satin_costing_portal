from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('costing', '0012_v34_daily_operations'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuickPOSProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('button_label', models.CharField(blank=True, help_text='Short label shown on POS button. Example: 4 for ₱100', max_length=80)),
                ('selling_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('bundle_quantity', models.PositiveIntegerField(default=1, help_text='How many pieces are included in the selling price.')),
                ('units_per_sheet', models.PositiveIntegerField(default=0, help_text='Leave 0 to use linked product/sticker-size fit when available.')),
                ('sheets_per_bundle', models.DecimalField(decimal_places=2, default=Decimal('1.00'), max_digits=10)),
                ('packaging_quantity', models.DecimalField(decimal_places=2, default=Decimal('1.00'), max_digits=10)),
                ('ink_cost_per_sheet', models.DecimalField(decimal_places=2, default=Decimal('3.00'), max_digits=10)),
                ('handling_fee', models.DecimalField(decimal_places=2, default=Decimal('5.00'), max_digits=10)),
                ('labor_per_sheet', models.DecimalField(decimal_places=2, default=Decimal('1.00'), max_digits=10)),
                ('blade_wear_per_sheet', models.DecimalField(decimal_places=2, default=Decimal('0.50'), max_digits=10)),
                ('machine_overhead', models.DecimalField(decimal_places=2, default=Decimal('2.00'), max_digits=10)),
                ('waste_percent', models.DecimalField(decimal_places=2, default=Decimal('5.00'), max_digits=7)),
                ('target_margin_percent', models.DecimalField(decimal_places=2, default=Decimal('35.00'), max_digits=7)),
                ('suggested_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Optional suggested next price if current margin is low.', max_digits=12)),
                ('active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='costing.productcategory')),
                ('product_preset', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='costing.productpreset')),
                ('main_material', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pos_main_products', to='costing.material')),
                ('lamination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pos_lamination_products', to='costing.material')),
                ('packaging', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pos_packaging_products', to='costing.material')),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='QuickPOSPriceSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snapshot_date', models.DateField(auto_now_add=True)),
                ('selling_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('estimated_cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('estimated_margin', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=7)),
                ('notes', models.TextField(blank=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_snapshots', to='costing.quickposproduct')),
            ],
            options={'ordering': ['-snapshot_date', 'product__name']},
        ),
    ]
