# Generated for PrintCraft V5 Smart Paste Edition
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('costing', '0013_v37_fast_pos'),
    ]

    operations = [
        migrations.CreateModel(
            name='SmartPasteInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_message', models.TextField()),
                ('customer_name', models.CharField(blank=True, max_length=160)),
                ('product_name', models.CharField(blank=True, max_length=180)),
                ('product_type', models.CharField(blank=True, default='STICKER', max_length=40)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('width_in', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('height_in', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('material_keyword', models.CharField(blank=True, max_length=120)),
                ('finish_keyword', models.CharField(blank=True, max_length=120)),
                ('deadline_text', models.CharField(blank=True, max_length=180)),
                ('delivery_method', models.CharField(blank=True, max_length=80)),
                ('payment_method', models.CharField(blank=True, max_length=80)),
                ('parsed_data', models.JSONField(blank=True, default=dict)),
                ('suggested_reply', models.TextField(blank=True)),
                ('confidence_score', models.PositiveSmallIntegerField(default=0)),
                ('status', models.CharField(choices=[('Draft', 'Draft'), ('Quoted', 'Quoted'), ('Converted', 'Converted'), ('Discarded', 'Discarded')], default='Draft', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_quote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='smart_paste_inquiries', to='costing.craftquote')),
                ('created_sale', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='smart_paste_inquiries', to='costing.salelog')),
            ],
            options={
                'verbose_name_plural': 'Smart Paste inquiries',
                'ordering': ['-created_at'],
            },
        ),
    ]
