from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("costing", "0016_alter_material_reorder_level"),
    ]

    operations = [
        migrations.AddField(
            model_name="salelogitem",
            name="other_material",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sale_other_material_items",
                to="costing.material",
            ),
        ),
        migrations.AddField(
            model_name="salelogitem",
            name="other_material_name",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="salelogitem",
            name="other_material_qty_used",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
            ),
        ),
    ]
