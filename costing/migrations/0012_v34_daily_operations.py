# Generated for PrintCraft V3.4 Daily Operations Edition
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("costing", "0011_v3_product_catalog"),
    ]

    operations = [
        migrations.AddField(
            model_name="salelog",
            name="job_status",
            field=models.CharField(
                choices=[
                    ("New", "New"),
                    ("Designing", "Designing"),
                    ("Printing", "Printing"),
                    ("Cutting", "Cutting"),
                    ("Packing", "Packing"),
                    ("Ready", "Ready for Pickup / Ship"),
                    ("Released", "Released / Completed"),
                    ("On Hold", "On Hold"),
                ],
                default="New",
                max_length=40,
            ),
        ),
        migrations.AddField(
            model_name="salelog",
            name="due_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="salelog",
            name="rush_order",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="salelog",
            name="deposit_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="salelog",
            name="balance_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="salelog",
            name="override_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="salelog",
            name="override_reason",
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name="salelog",
            name="internal_job_notes",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="ExpenseLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(auto_now_add=True)),
                ("category", models.CharField(choices=[
                    ("Materials", "Materials"), ("Ink", "Ink"), ("Tools / Blades", "Tools / Blades"),
                    ("Packaging", "Packaging"), ("Delivery", "Delivery"), ("Utilities", "Utilities"),
                    ("Marketing", "Marketing"), ("Other", "Other")
                ], default="Other", max_length=40)),
                ("description", models.CharField(max_length=220)),
                ("amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("supplier", models.CharField(blank=True, max_length=160)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="StockPurchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purchase_date", models.DateField(auto_now_add=True)),
                ("supplier", models.CharField(blank=True, max_length=160)),
                ("quantity_added", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("total_cost", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("stock_applied", models.BooleanField(default=False)),
                ("material", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="purchases", to="costing.material")),
            ],
            options={"ordering": ["-purchase_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ShopTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("priority", models.CharField(choices=[("Low", "Low"), ("Normal", "Normal"), ("High", "High")], default="Normal", max_length=20)),
                ("status", models.CharField(choices=[("Open", "Open"), ("Done", "Done"), ("Cancelled", "Cancelled")], default="Open", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("related_sale", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tasks", to="costing.salelog")),
            ],
            options={"ordering": ["status", "due_date", "-created_at"]},
        ),
    ]
