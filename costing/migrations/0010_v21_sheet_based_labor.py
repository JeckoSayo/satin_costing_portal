from decimal import Decimal
from django.db import migrations, models


def set_v21_defaults(apps, schema_editor):
    PriceSetting = apps.get_model('costing', 'PriceSetting')
    settings = PriceSetting.objects.first()
    if settings:
        settings.default_markup_percent = Decimal('45.00')
        settings.default_margin_percent = Decimal('35.00')
        settings.safety_buffer_per_order = Decimal('10.00')
        settings.minimum_order_price = Decimal('149.00')
        settings.base_handling_fee = Decimal('10.00')
        settings.labor_per_sheet = Decimal('2.00')
        settings.blade_wear_per_sheet = Decimal('1.00')
        settings.machine_overhead_per_order = Decimal('5.00')
        settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('costing', '0009_v2_pricing_inventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='pricesetting',
            name='base_handling_fee',
            field=models.DecimalField(decimal_places=2, default=Decimal('10.00'), help_text='Automatic handling/setup fee per quote/order.', max_digits=10),
        ),
        migrations.AddField(
            model_name='pricesetting',
            name='labor_per_sheet',
            field=models.DecimalField(decimal_places=2, default=Decimal('2.00'), help_text='Automatic labor cost per printed sheet.', max_digits=10),
        ),
        migrations.AddField(
            model_name='pricesetting',
            name='blade_wear_per_sheet',
            field=models.DecimalField(decimal_places=2, default=Decimal('1.00'), help_text='Blade/cutter wear cost per sheet.', max_digits=10),
        ),
        migrations.AddField(
            model_name='pricesetting',
            name='machine_overhead_per_order',
            field=models.DecimalField(decimal_places=2, default=Decimal('5.00'), help_text='Printer/cutter/electricity overhead per quote/order.', max_digits=10),
        ),
        migrations.AlterField(
            model_name='pricesetting',
            name='labor_rate_per_hour',
            field=models.DecimalField(decimal_places=2, default=Decimal('80.00'), help_text='Legacy/manual labor rate. V2.1 uses sheet-based labor by default.', max_digits=10),
        ),
        migrations.RunPython(set_v21_defaults, migrations.RunPython.noop),
    ]
