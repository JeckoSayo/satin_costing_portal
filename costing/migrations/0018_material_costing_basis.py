from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("costing", "0017_salelogitem_other_material"),
    ]

    operations = [
        migrations.AddField(
            model_name="material",
            name="costing_basis",
            field=models.CharField(
                choices=[
                    ("per_sheet", "Per Print Sheet"),
                    ("per_piece", "Per Piece"),
                    ("per_order", "Per Order"),
                ],
                default="per_sheet",
                help_text="How this material is costed when used as Other Direct Material.",
                max_length=20,
            ),
        ),
    ]
