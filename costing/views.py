import json
from decimal import Decimal
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    TemplateView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from .forms import (
    MaterialForm,
    StickerSizeForm,
    PaperSizeForm,
    PriceSettingForm,
    QuoteForm,
    ProductCategoryForm,
    ProductPresetForm,
    ProductPriceTierForm,
    ProductQuoteForm,
    SaleOperationsForm,
    ExpenseLogForm,
    StockPurchaseForm,
    ShopTaskForm,
    QuickPOSProductForm,
    SmartPasteInquiryForm,
    SmartPasteRawForm,
    )
from .models import (
    Material,
    StickerSize,
    PaperSize,
    PriceSetting,
    SaleLog,
    SaleLogItem,
    MarketplaceFee,
    StockMovement,
    ProductCategory,
    ProductPreset,
    ProductPriceTier,
    CraftQuote,
    ExpenseLog,
    StockPurchase,
    ShopTask,
    QuickPOSProduct,
    QuickPOSPriceSnapshot,
    SmartPasteInquiry,
)
from .services import calculate_quote, create_sale_from_order_items, reverse_sale_inventory, calculate_product_preset_quote, save_product_quote, create_smart_paste_inquiry
from django.db.models import Sum, F, Count, Q, Max
from django.utils import timezone
from datetime import timedelta



class DashboardView(TemplateView):
    template_name = "costing/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        settings, _ = PriceSetting.objects.get_or_create(id=1)

        ctx["settings"] = settings
        ctx["sticker_sizes"] = StickerSize.objects.filter(is_active=True)
        ctx["paper_sizes"] = PaperSize.objects.filter(is_active=True)
        ctx["main_materials"] = Material.objects.filter(
            is_active=True,
            category=Material.CATEGORY_STICKER
        )
        ctx["laminations"] = Material.objects.filter(
            is_active=True,
            category=Material.CATEGORY_LAMINATION
        )
        ctx["packagings"] = Material.objects.filter(
            is_active=True,
            category=Material.CATEGORY_PACKAGING
        )

        ctx["platform_choices"] = SaleLog.PLATFORM_CHOICES
        ctx["payment_choices"] = SaleLog.PAYMENT_CHOICES
        ctx["status_choices"] = SaleLog.STATUS_CHOICES

        today = timezone.localdate()
        today_sales = SaleLog.objects.filter(created_at__date=today)
        month_sales = SaleLog.objects.filter(created_at__year=today.year, created_at__month=today.month)

        ctx["recent_sales"] = SaleLog.objects.all()[:5]
        ctx["today_revenue"] = today_sales.aggregate(total=Sum("selling_price"))["total"] or 0
        ctx["today_profit"] = today_sales.aggregate(total=Sum("profit"))["total"] or 0
        ctx["monthly_sales"] = month_sales.aggregate(total=Sum("selling_price"))["total"] or 0
        low_stock_qs = Material.objects.filter(is_active=True, reorder_level__gt=0, stock_qty__lte=F("reorder_level")).order_by("stock_qty", "item_name")
        ctx["low_stock_count"] = low_stock_qs.count()
        ctx["low_stock_materials"] = low_stock_qs[:8]
        ctx["marketplace_fees"] = MarketplaceFee.objects.filter(is_active=True)
        ctx["today_orders"] = today_sales.count()
        ctx["top_repeat_customers"] = (
            SaleLog.objects.exclude(customer_name="")
            .values("customer_name")
            .annotate(order_count=Count("id"), total_spent=Sum("selling_price"))
            .order_by("-order_count", "-total_spent")[:6]
        )
        ctx["due_today_count"] = SaleLog.objects.filter(due_date=today).exclude(job_status=SaleLog.JOB_RELEASED).count()
        ctx["ready_count"] = SaleLog.objects.filter(job_status=SaleLog.JOB_READY).count()
        ctx["unpaid_balance"] = SaleLog.objects.aggregate(total=Sum("balance_amount"))["total"] or 0
        ctx["open_tasks"] = ShopTask.objects.filter(status=ShopTask.STATUS_OPEN)[:6]
        ctx["todays_expenses"] = ExpenseLog.objects.filter(date=today).aggregate(total=Sum("amount"))["total"] or 0

        return ctx

    def post(self, request, *args, **kwargs):
        order_items_json = request.POST.get("order_items_json", "[]")
        try:
            order_items = json.loads(order_items_json)
        except json.JSONDecodeError:
            order_items = []

        payload = {
            "customer_name": request.POST.get("customer_name", ""),
            "order_name": request.POST.get("order_name", ""),
            "platform": request.POST.get("platform") or SaleLog.PLATFORM_WALKIN,
            "payment_method": request.POST.get("payment_method") or SaleLog.PAYMENT_CASH,
            "status": request.POST.get("status") or SaleLog.STATUS_PENDING,
            "platform_order_id": request.POST.get("platform_order_id", ""),
            "tracking_number": request.POST.get("tracking_number", ""),
            "courier": request.POST.get("courier", ""),
            "buyer_username": request.POST.get("buyer_username", ""),
            "buyer_phone": request.POST.get("buyer_phone", ""),
            "shipping_address": request.POST.get("shipping_address", ""),
            "weight_grams": request.POST.get("weight_grams") or 0,
            "shipping_fee": request.POST.get("shipping_fee") or 0,
            "discount": request.POST.get("discount") or 0,
            "order_items": order_items,
        }

        try:
            sale = create_sale_from_order_items(payload)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("dashboard")
        except Exception as exc:
            messages.error(request, f"Could not log sale: {exc}")
            return redirect("dashboard")

        messages.success(request, f"Sale {sale.receipt_number} logged successfully with V2 pricing and stock audit.")
        return redirect("dashboard")

class FullQuoteCalculatorView(DashboardView):
    template_name = "costing/full_quote_calculator.html"


class SimpleCostingCalculatorView(TemplateView):
    template_name = "costing/simple_costing_calculator.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        settings, _ = PriceSetting.objects.get_or_create(id=1)
        ctx["settings"] = settings

        # Keep the Simple Costing page connected to the same data source as
        # the full Quote Calculator. This prevents mismatched pricing between
        # the simple and advanced calculators.
        ctx["sticker_sizes"] = StickerSize.objects.filter(is_active=True)
        ctx["main_materials"] = Material.objects.filter(
            is_active=True,
            category=Material.CATEGORY_STICKER,
        )
        ctx["laminations"] = Material.objects.filter(
            is_active=True,
            category=Material.CATEGORY_LAMINATION,
        )
        ctx["packagings"] = Material.objects.filter(
            is_active=True,
            category=Material.CATEGORY_PACKAGING,
        )
        ctx["platform_choices"] = SaleLog.PLATFORM_CHOICES
        ctx["payment_choices"] = SaleLog.PAYMENT_CHOICES
        ctx["status_choices"] = SaleLog.STATUS_CHOICES
        return ctx


class CalculateQuoteView(View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = request.POST.dict()

        form = QuoteForm(payload)

        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        cleaned_data = form.cleaned_data.copy()

        # Keep custom fields from Simple Costing.
        cleaned_data["use_cricut_cut"] = payload.get("use_cricut_cut")
        cleaned_data["packaging_capacity"] = payload.get("packaging_capacity")

        result = calculate_quote(cleaned_data)

        return JsonResponse({"ok": True, "result": result})


class LogSaleView(View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = request.POST.dict()

        # API-friendly endpoint: one item quote -> one sale.
        form = QuoteForm(payload)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        item = {
            "product_name": payload.get("order_name", ""),
            "sticker_size_id": form.cleaned_data["sticker_size_id"],
            "quantity": form.cleaned_data["quantity"],
            "material_id": form.cleaned_data.get("material_id"),
            "lamination_id": form.cleaned_data.get("lamination_id"),
            "packaging_id": form.cleaned_data.get("packaging_id"),
            "packaging_capacity": payload.get("packaging_capacity"),
            "use_cricut_cut": payload.get("use_cricut_cut"),
            "ink_cost_per_sheet": form.cleaned_data.get("ink_cost_per_sheet"),
            "labor_minutes": form.cleaned_data.get("labor_minutes"),
            "additional_direct_cost": form.cleaned_data.get("additional_direct_cost"),
            "target_sale_price": form.cleaned_data.get("target_sale_price"),
            "design_fee": payload.get("design_fee"),
        }

        sale_payload = {
            "customer_name": payload.get("customer_name", ""),
            "order_name": payload.get("order_name", ""),
            "platform": payload.get("platform") or SaleLog.PLATFORM_WALKIN,
            "payment_method": payload.get("payment_method") or SaleLog.PAYMENT_CASH,
            "status": payload.get("status") or SaleLog.STATUS_PENDING,
            "shipping_fee": payload.get("shipping_fee") or 0,
            "order_items": [item],
        }

        try:
            sale = create_sale_from_order_items(sale_payload)
        except Exception as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)

        return JsonResponse({
            "ok": True,
            "message": f"Sale {sale.receipt_number} logged successfully.",
            "sale_id": sale.id,
        })

class SalesLogView(ListView):
    model = SaleLog
    template_name = "costing/sales_log.html"
    context_object_name = "sales"

    def get_queryset(self):
        queryset = SaleLog.objects.all().order_by("-created_at")

        search = self.request.GET.get("search")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if search:
            queryset = (
                queryset.filter(customer_name__icontains=search)
                | queryset.filter(order_name__icontains=search)
                | queryset.filter(sticker_size__icontains=search)
            )

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.get_queryset()

        context["total_sales"] = queryset.aggregate(total=Sum("selling_price"))["total"] or 0
        context["total_cost"] = queryset.aggregate(total=Sum("cost"))["total"] or 0
        context["total_profit"] = queryset.aggregate(total=Sum("profit"))["total"] or 0
        context["total_orders"] = queryset.count()

        context["search"] = self.request.GET.get("search", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        return context


class SaleLogDeleteView(View):
    def post(self, request, pk):
        sale = get_object_or_404(SaleLog, pk=pk)
        reverse_sale_inventory(sale)
        sale.delete()
        messages.success(request, "Sale deleted successfully and deducted stock was restored.")
        return redirect("sales_log")


class PriceSettingsView(UpdateView):
    model = PriceSetting
    form_class = PriceSettingForm
    template_name = 'costing/price_settings.html'
    success_url = reverse_lazy('price_settings')

    def get_object(self, queryset=None):
        obj, _ = PriceSetting.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Price settings updated successfully.')
        return super().form_valid(form)


class MaterialListView(ListView):
    queryset = Material.objects.order_by("category", "item_name")
    template_name = "costing/materials.html"
    context_object_name = "materials"


class MaterialCreateView(CreateView):
    model = Material
    form_class = MaterialForm
    template_name = 'costing/material_form.html'
    success_url = reverse_lazy('materials')

    def form_valid(self, form):
        messages.success(self.request, 'Material added successfully.')
        return super().form_valid(form)


class MaterialUpdateView(UpdateView):
    model = Material
    form_class = MaterialForm
    template_name = 'costing/material_form.html'
    success_url = reverse_lazy('materials')

    def form_valid(self, form):
        messages.success(self.request, 'Material updated successfully.')
        return super().form_valid(form)


class MaterialDeleteView(DeleteView):
    model = Material
    template_name = 'costing/material_confirm_delete.html'
    success_url = reverse_lazy('materials')

    def form_valid(self, form):
        messages.success(self.request, 'Material deleted successfully.')
        return super().form_valid(form)


class BulkMaterialDeleteView(View):
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('selected_materials')
        if ids:
            Material.objects.filter(id__in=ids).delete()
            messages.success(request, f'{len(ids)} material(s) deleted.')
        else:
            messages.warning(request, 'No materials selected.')
        return redirect('materials')


class StickerSizeListView(ListView):
    model = StickerSize
    template_name = 'costing/sticker_sizes.html'
    context_object_name = 'sizes'


class StickerSizeCreateView(CreateView):
    model = StickerSize
    form_class = StickerSizeForm
    template_name = 'costing/sticker_size_form.html'
    success_url = reverse_lazy('sticker_sizes')

    def form_valid(self, form):
        messages.success(self.request, 'Sticker size added successfully.')
        return super().form_valid(form)


class StickerSizeUpdateView(UpdateView):
    model = StickerSize
    form_class = StickerSizeForm
    template_name = 'costing/sticker_size_form.html'
    success_url = reverse_lazy('sticker_sizes')

    def form_valid(self, form):
        messages.success(self.request, 'Sticker size updated successfully.')
        return super().form_valid(form)


class StickerSizeDeleteView(DeleteView):
    model = StickerSize
    template_name = 'costing/sticker_size_confirm_delete.html'
    success_url = reverse_lazy('sticker_sizes')


class PaperSizeListView(ListView):
    model = PaperSize
    template_name = 'costing/paper_sizes.html'
    context_object_name = 'papers'


class PaperSizeCreateView(CreateView):
    model = PaperSize
    form_class = PaperSizeForm
    template_name = 'costing/paper_size_form.html'
    success_url = reverse_lazy('paper_sizes')


class PaperSizeUpdateView(UpdateView):
    model = PaperSize
    form_class = PaperSizeForm
    template_name = 'costing/paper_size_form.html'
    success_url = reverse_lazy('paper_sizes')


class PaperSizeDeleteView(DeleteView):
    model = PaperSize
    template_name = 'costing/paper_size_confirm_delete.html'
    success_url = reverse_lazy('paper_sizes')


class SaleLogUpdateView(UpdateView):
    model = SaleLog
    form_class = SaleOperationsForm
    template_name = "costing/sale_form.html"
    success_url = reverse_lazy("sales_log")

    def form_valid(self, form):
        response = super().form_valid(form)
        sale = self.object
        if sale.status in [SaleLog.STATUS_CANCELLED, SaleLog.STATUS_REFUNDED] and sale.stock_deducted:
            reverse_sale_inventory(sale)
            messages.success(self.request, "Sale updated and deducted stock was restored.")
        else:
            messages.success(self.request, "Sale updated successfully.")
        return response


class SaleLogDetailView(DetailView):
    model = SaleLog
    template_name = "costing/sale_detail.html"
    context_object_name = "sale"


class SaleReceiptView(DetailView):
    model = SaleLog
    template_name = "costing/sale_receipt.html"
    context_object_name = "sale"


class ProductCatalogView(ListView):
    model = ProductPreset
    template_name = "costing/product_catalog.html"
    context_object_name = "products"

    def get_queryset(self):
        qs = ProductPreset.objects.select_related("category").prefetch_related("tiers").order_by("category__name", "name")
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = ProductCategory.objects.filter(is_active=True)
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["recent_quotes"] = CraftQuote.objects.select_related("product")[:8]
        return ctx


class ProductPresetCreateView(CreateView):
    model = ProductPreset
    form_class = ProductPresetForm
    template_name = "costing/product_preset_form.html"
    success_url = reverse_lazy("product_catalog")

    def form_valid(self, form):
        messages.success(self.request, "Product preset added.")
        return super().form_valid(form)


class ProductPresetUpdateView(UpdateView):
    model = ProductPreset
    form_class = ProductPresetForm
    template_name = "costing/product_preset_form.html"
    success_url = reverse_lazy("product_catalog")

    def form_valid(self, form):
        messages.success(self.request, "Product preset updated.")
        return super().form_valid(form)


class ProductPriceTierCreateView(CreateView):
    model = ProductPriceTier
    form_class = ProductPriceTierForm
    template_name = "costing/product_tier_form.html"
    success_url = reverse_lazy("product_catalog")

    def form_valid(self, form):
        messages.success(self.request, "Price tier added.")
        return super().form_valid(form)


class ProductQuoteView(TemplateView):
    template_name = "costing/product_quote.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["products"] = ProductPreset.objects.filter(is_active=True).select_related("category")
        ctx["quotes"] = CraftQuote.objects.select_related("product")[:10]
        return ctx

    def post(self, request, *args, **kwargs):
        form = ProductQuoteForm(request.POST)
        ctx = self.get_context_data()
        if not form.is_valid():
            ctx["errors"] = form.errors
            return self.render_to_response(ctx)
        try:
            result = calculate_product_preset_quote(
                form.cleaned_data["product_id"],
                form.cleaned_data["quantity"],
                platform=request.POST.get("platform") or SaleLog.PLATFORM_WALKIN,
            )
            ctx["result"] = result
            ctx["selected_product_id"] = form.cleaned_data["product_id"]
            ctx["entered_quantity"] = form.cleaned_data["quantity"]
            ctx["customer_name"] = form.cleaned_data.get("customer_name", "")
            if request.POST.get("save_quote") == "1":
                quote, result = save_product_quote(
                    form.cleaned_data["product_id"],
                    form.cleaned_data["quantity"],
                    customer_name=form.cleaned_data.get("customer_name", ""),
                    notes=form.cleaned_data.get("notes", ""),
                    platform=request.POST.get("platform") or SaleLog.PLATFORM_WALKIN,
                )
                messages.success(request, f"Quote saved for {quote.product.name}.")
                ctx["result"] = result
        except Exception as exc:
            ctx["errors"] = {"quote": [str(exc)]}
        return self.render_to_response(ctx)



class OrderQueueView(ListView):
    model = SaleLog
    template_name = "costing/order_queue.html"
    context_object_name = "orders"

    def get_queryset(self):
        qs = SaleLog.objects.all().order_by("due_date", "-rush_order", "-created_at")
        status = self.request.GET.get("job_status")
        if status:
            qs = qs.filter(job_status=status)
        due = self.request.GET.get("due")
        today = timezone.localdate()
        if due == "today":
            qs = qs.filter(due_date=today)
        elif due == "overdue":
            qs = qs.filter(due_date__lt=today).exclude(job_status__in=[SaleLog.JOB_RELEASED, SaleLog.JOB_READY])
        elif due == "ready":
            qs = qs.filter(job_status=SaleLog.JOB_READY)
        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(Q(customer_name__icontains=search) | Q(order_name__icontains=search) | Q(receipt_number__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        ctx["job_choices"] = SaleLog.JOB_CHOICES
        ctx["selected_job_status"] = self.request.GET.get("job_status", "")
        ctx["selected_due"] = self.request.GET.get("due", "")
        ctx["search"] = self.request.GET.get("search", "")
        ctx["due_today"] = SaleLog.objects.filter(due_date=today).exclude(job_status=SaleLog.JOB_RELEASED).count()
        ctx["overdue"] = SaleLog.objects.filter(due_date__lt=today).exclude(job_status__in=[SaleLog.JOB_RELEASED, SaleLog.JOB_READY]).count()
        ctx["ready"] = SaleLog.objects.filter(job_status=SaleLog.JOB_READY).count()
        return ctx


class UpdateJobStatusView(View):
    def post(self, request, pk):
        sale = get_object_or_404(SaleLog, pk=pk)
        new_status = request.POST.get("job_status")
        valid = dict(SaleLog.JOB_CHOICES)
        if new_status in valid:
            sale.job_status = new_status
            if new_status == SaleLog.JOB_RELEASED:
                sale.status = SaleLog.STATUS_COMPLETED
            sale.save(update_fields=["job_status", "status", "balance_amount"])
            messages.success(request, f"{sale.receipt_number} moved to {new_status}.")
        else:
            messages.error(request, "Invalid job status.")
        return redirect(request.META.get("HTTP_REFERER", "order_queue"))


class CustomerHistoryView(ListView):
    model = SaleLog
    template_name = "costing/customer_history.html"
    context_object_name = "sales"

    def get_queryset(self):
        self.customer = self.kwargs.get("customer_name", "")
        return SaleLog.objects.filter(customer_name=self.customer).order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx["customer_name"] = self.customer
        ctx["total_orders"] = qs.count()
        ctx["total_spent"] = qs.aggregate(total=Sum("selling_price"))["total"] or 0
        ctx["total_profit"] = qs.aggregate(total=Sum("profit"))["total"] or 0
        return ctx


class ReorderSaleView(View):
    def post(self, request, pk):
        source = get_object_or_404(SaleLog, pk=pk)
        source_items = []
        for item in source.items.all():
            source_items.append({
                "product_name": item.product_name,
                "sticker_size": item.sticker_size,
                "material_id": item.material_id,
                "lamination_id": item.lamination_id,
                "packaging_id": item.packaging_id,
                "material_name": item.material_name,
                "lamination_name": item.lamination_name,
                "packaging_name": item.packaging_name,
                "quantity": item.quantity,
                "sheets_needed": item.sheets_needed,
                "packaging_capacity": item.packaging_capacity,
                "material_qty_used": item.material_qty_used,
                "lamination_qty_used": item.lamination_qty_used,
                "packaging_qty_used": item.packaging_qty_used,
                "unit_price": item.unit_price,
                "line_total": item.line_total,
                "line_cost": item.line_cost,
                "line_profit": item.line_profit,
                "notes": f"Reorder from {source.receipt_number}",
            })
        payload = {
            "customer_name": source.customer_name,
            "order_name": f"Reorder - {source.order_name}",
            "platform": source.platform,
            "payment_method": source.payment_method,
            "status": SaleLog.STATUS_PENDING,
            "shipping_fee": source.shipping_fee,
            "discount": source.discount,
            "order_items": source_items,
        }
        try:
            sale = create_sale_from_order_items(payload)
            messages.success(request, f"Reorder created: {sale.receipt_number}.")
            return redirect("sale_edit", pk=sale.pk)
        except Exception as exc:
            messages.error(request, f"Could not reorder: {exc}")
            return redirect("sale_detail", pk=source.pk)


class ExpenseListView(ListView):
    model = ExpenseLog
    template_name = "costing/expenses.html"
    context_object_name = "expenses"

    def get_queryset(self):
        qs = ExpenseLog.objects.all()
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        today = timezone.localdate()
        ctx["form"] = ExpenseLogForm()
        ctx["categories"] = ExpenseLog.CATEGORY_CHOICES
        ctx["total"] = qs.aggregate(total=Sum("amount"))["total"] or 0
        ctx["today_total"] = ExpenseLog.objects.filter(date=today).aggregate(total=Sum("amount"))["total"] or 0
        return ctx

    def post(self, request, *args, **kwargs):
        form = ExpenseLogForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense logged.")
        else:
            messages.error(request, "Please check the expense form.")
        return redirect("expenses")


class StockPurchaseListView(ListView):
    model = StockPurchase
    template_name = "costing/stock_purchases.html"
    context_object_name = "purchases"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = StockPurchaseForm()
        return ctx

    def post(self, request, *args, **kwargs):
        form = StockPurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            messages.success(request, f"Stock added to {purchase.material.item_name}.")
        else:
            messages.error(request, "Please check the purchase form.")
        return redirect("stock_purchases")


class ShopTaskListView(ListView):
    model = ShopTask
    template_name = "costing/tasks.html"
    context_object_name = "tasks"

    def get_queryset(self):
        status = self.request.GET.get("status", ShopTask.STATUS_OPEN)
        return ShopTask.objects.filter(status=status) if status else ShopTask.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = ShopTaskForm()
        ctx["selected_status"] = self.request.GET.get("status", ShopTask.STATUS_OPEN)
        return ctx

    def post(self, request, *args, **kwargs):
        form = ShopTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Task saved.")
        else:
            messages.error(request, "Please check the task form.")
        return redirect("tasks")


class JobTicketView(DetailView):
    model = SaleLog
    template_name = "costing/job_ticket.html"
    context_object_name = "sale"


class CashflowView(TemplateView):
    template_name = "costing/cashflow.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        sales_today = SaleLog.objects.filter(created_at__date=today)
        expenses_today = ExpenseLog.objects.filter(date=today)
        ctx["sales_today"] = sales_today.aggregate(total=Sum("selling_price"))["total"] or 0
        ctx["collected_today"] = sales_today.aggregate(total=Sum("deposit_amount"))["total"] or 0
        ctx["profit_today"] = sales_today.aggregate(total=Sum("profit"))["total"] or 0
        ctx["expenses_today"] = expenses_today.aggregate(total=Sum("amount"))["total"] or 0
        ctx["net_cash_today"] = ctx["collected_today"] - ctx["expenses_today"]
        ctx["unpaid_balance"] = SaleLog.objects.aggregate(total=Sum("balance_amount"))["total"] or 0
        ctx["recent_expenses"] = ExpenseLog.objects.all()[:8]
        ctx["recent_sales"] = SaleLog.objects.all()[:8]
        return ctx


class AnalyticsDashboardView(TemplateView):
    """V3.5: modern analytics dashboard using the existing Satin Creative color palette."""
    template_name = "costing/analytics_dashboard.html"

    def _money(self, value):
        return float(value or 0)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start_7 = today - timedelta(days=6)
        start_30 = today - timedelta(days=29)

        sales_today = SaleLog.objects.filter(created_at__date=today)
        sales_month = SaleLog.objects.filter(created_at__year=today.year, created_at__month=today.month)
        sales_30 = SaleLog.objects.filter(created_at__date__gte=start_30, created_at__date__lte=today)
        expenses_today = ExpenseLog.objects.filter(date=today)
        expenses_month = ExpenseLog.objects.filter(date__year=today.year, date__month=today.month)

        revenue_today = sales_today.aggregate(total=Sum("selling_price"))["total"] or Decimal("0.00")
        cost_today = sales_today.aggregate(total=Sum("cost"))["total"] or Decimal("0.00")
        profit_today = sales_today.aggregate(total=Sum("profit"))["total"] or Decimal("0.00")
        revenue_month = sales_month.aggregate(total=Sum("selling_price"))["total"] or Decimal("0.00")
        cost_month = sales_month.aggregate(total=Sum("cost"))["total"] or Decimal("0.00")
        profit_month = sales_month.aggregate(total=Sum("profit"))["total"] or Decimal("0.00")
        expenses_month_total = expenses_month.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        net_income_month = profit_month - expenses_month_total
        orders_month = sales_month.count()
        aov_month = revenue_month / orders_month if orders_month else Decimal("0.00")

        day_labels, revenue_series, cost_series, profit_series = [], [], [], []
        for i in range(7):
            day = start_7 + timedelta(days=i)
            day_sales = SaleLog.objects.filter(created_at__date=day)
            day_labels.append(day.strftime("%b %d"))
            revenue_series.append(self._money(day_sales.aggregate(total=Sum("selling_price"))["total"]))
            cost_series.append(self._money(day_sales.aggregate(total=Sum("cost"))["total"]))
            profit_series.append(self._money(day_sales.aggregate(total=Sum("profit"))["total"]))

        platform_rows = (
            sales_30.values("platform")
            .annotate(total=Sum("selling_price"), orders=Count("id"), profit=Sum("profit"))
            .order_by("-total")[:6]
        )
        platform_labels = [r["platform"] or "Unknown" for r in platform_rows]
        platform_values = [self._money(r["total"]) for r in platform_rows]

        product_rows = (
            SaleLogItem.objects.filter(sale__created_at__date__gte=start_30, sale__created_at__date__lte=today)
            .values("product_name")
            .annotate(total=Sum("line_total"), profit=Sum("line_profit"), qty=Sum("quantity"))
            .order_by("-profit")[:8]
        )
        for r in product_rows:
            r["display_name"] = r["product_name"] or "Untitled Item"

        material_rows = (
            SaleLogItem.objects.filter(sale__created_at__date__gte=start_30, sale__created_at__date__lte=today)
            .exclude(material_name="")
            .values("material_name")
            .annotate(sheets=Sum("material_qty_used"), cost=Sum("line_cost"))
            .order_by("-sheets")[:7]
        )
        material_labels = [r["material_name"][:24] for r in material_rows]
        material_values = [self._money(r["sheets"]) for r in material_rows]

        job_counts = []
        for status, label in SaleLog.JOB_CHOICES:
            job_counts.append({
                "status": status,
                "label": label,
                "count": SaleLog.objects.filter(job_status=status).count(),
            })

        low_stock_qs = Material.objects.filter(is_active=True, reorder_level__gt=0, stock_qty__lte=F("reorder_level")).order_by("stock_qty", "item_name")
        top_customers = (
            SaleLog.objects.exclude(customer_name="")
            .values("customer_name")
            .annotate(total=Sum("selling_price"), orders=Count("id"), profit=Sum("profit"))
            .order_by("-total")[:6]
        )

        ctx.update({
            "revenue_today": revenue_today,
            "profit_today": profit_today,
            "cost_today": cost_today,
            "expenses_today": expenses_today.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
            "revenue_month": revenue_month,
            "cost_month": cost_month,
            "profit_month": profit_month,
            "expenses_month": expenses_month_total,
            "net_income_month": net_income_month,
            "orders_month": orders_month,
            "average_order_value": aov_month,
            "pending_orders": SaleLog.objects.exclude(job_status=SaleLog.JOB_RELEASED).exclude(status__in=[SaleLog.STATUS_CANCELLED, SaleLog.STATUS_REFUNDED]).count(),
            "due_today": SaleLog.objects.filter(due_date=today).exclude(job_status=SaleLog.JOB_RELEASED).count(),
            "unpaid_balance": SaleLog.objects.aggregate(total=Sum("balance_amount"))["total"] or Decimal("0.00"),
            "low_stock_count": low_stock_qs.count(),
            "low_stock_materials": low_stock_qs[:8],
            "recent_sales": SaleLog.objects.all()[:8],
            "top_customers": top_customers,
            "product_rows": product_rows,
            "platform_rows": platform_rows,
            "material_rows": material_rows,
            "job_counts": job_counts,
            "chart_labels": json.dumps(day_labels),
            "chart_revenue": json.dumps(revenue_series),
            "chart_cost": json.dumps(cost_series),
            "chart_profit": json.dumps(profit_series),
            "platform_labels": json.dumps(platform_labels),
            "platform_values": json.dumps(platform_values),
            "material_labels": json.dumps(material_labels),
            "material_values": json.dumps(material_values),
        })
        return ctx


class SmartBusinessView(TemplateView):
    """V3.6: intelligence and automation dashboard for pricing, capacity, inventory, and chat quotes."""
    template_name = "costing/smart_business.html"

    def _money(self, value):
        return float(value or 0)

    def _safe_decimal(self, value):
        return Decimal(str(value or 0))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start_30 = today - timedelta(days=29)
        start_7 = today - timedelta(days=6)

        settings, _ = PriceSetting.objects.get_or_create(id=1)
        sales_30 = SaleLog.objects.filter(created_at__date__gte=start_30, created_at__date__lte=today)
        sales_7 = SaleLog.objects.filter(created_at__date__gte=start_7, created_at__date__lte=today)
        open_orders = SaleLog.objects.exclude(job_status=SaleLog.JOB_RELEASED).exclude(status__in=[SaleLog.STATUS_CANCELLED, SaleLog.STATUS_REFUNDED])

        quote_count_30 = CraftQuote.objects.filter(created_at__date__gte=start_30, created_at__date__lte=today).count()
        order_count_30 = sales_30.count()
        conversion_rate = Decimal("0.00")
        if quote_count_30:
            conversion_rate = (Decimal(order_count_30) / Decimal(quote_count_30)) * Decimal("100")

        revenue_30 = sales_30.aggregate(total=Sum("selling_price"))["total"] or Decimal("0.00")
        profit_30 = sales_30.aggregate(total=Sum("profit"))["total"] or Decimal("0.00")
        cost_30 = sales_30.aggregate(total=Sum("cost"))["total"] or Decimal("0.00")
        avg_order_value = revenue_30 / order_count_30 if order_count_30 else Decimal("0.00")

        # Smart pricing suggestions from historical sales item data.
        product_rows = (
            SaleLogItem.objects.filter(sale__created_at__date__gte=start_30, sale__created_at__date__lte=today)
            .values("product_name", "sticker_size")
            .annotate(qty=Sum("quantity"), total=Sum("line_total"), cost=Sum("line_cost"), profit=Sum("line_profit"), orders=Count("sale", distinct=True))
            .order_by("-profit")[:8]
        )
        pricing_suggestions = []
        for row in product_rows:
            qty = row["qty"] or 0
            total = row["total"] or Decimal("0.00")
            cost = row["cost"] or Decimal("0.00")
            profit = row["profit"] or Decimal("0.00")
            avg_unit = total / Decimal(qty) if qty else Decimal("0.00")
            avg_cost_unit = cost / Decimal(qty) if qty else Decimal("0.00")
            protected_price = avg_cost_unit / (Decimal("1.00") - (settings.default_margin_percent / Decimal("100.00"))) if settings.default_margin_percent < 100 else avg_unit
            aggressive = max(avg_unit * Decimal("0.95"), protected_price)
            suggested = max(avg_unit, protected_price)
            premium = suggested * Decimal("1.12")
            margin = (profit / total * Decimal("100.00")) if total else Decimal("0.00")
            pricing_suggestions.append({
                "name": row["product_name"] or "Untitled product",
                "size": row["sticker_size"] or "Mixed size",
                "qty": qty,
                "orders": row["orders"],
                "avg_unit": avg_unit,
                "aggressive": aggressive,
                "suggested": suggested,
                "premium": premium,
                "margin": margin,
            })

        if not pricing_suggestions:
            # Starter suggestions still useful before sales data exists.
            pricing_suggestions = [
                {"name": "Waterproof Stickers", "size": "Small bundle", "qty": 4, "orders": 0, "avg_unit": Decimal("25.00"), "aggressive": Decimal("99.00"), "suggested": Decimal("119.00"), "premium": Decimal("149.00"), "margin": Decimal("35.00")},
                {"name": "Logo Labels", "size": "2 x 2 in", "qty": 50, "orders": 0, "avg_unit": Decimal("3.50"), "aggressive": Decimal("179.00"), "suggested": Decimal("220.00"), "premium": Decimal("249.00"), "margin": Decimal("35.00")},
                {"name": "Invitation Set", "size": "A6 / custom", "qty": 20, "orders": 0, "avg_unit": Decimal("15.00"), "aggressive": Decimal("299.00"), "suggested": Decimal("349.00"), "premium": Decimal("399.00"), "margin": Decimal("40.00")},
            ]

        # Reorder forecast from last 30 days of stock-out movements.
        forecast_rows = []
        materials = Material.objects.filter(is_active=True).order_by("category", "item_name")
        for material in materials:
            used_30 = StockMovement.objects.filter(
                material=material,
                movement_type=StockMovement.MOVEMENT_OUT,
                created_at__date__gte=start_30,
                created_at__date__lte=today,
            ).aggregate(total=Sum("quantity"))["total"] or Decimal("0.00")
            daily_use = used_30 / Decimal("30.00") if used_30 else Decimal("0.00")
            days_left = None
            if daily_use > 0:
                days_left = (material.stock_qty or Decimal("0.00")) / daily_use
            if material.is_low_stock or used_30 > 0:
                forecast_rows.append({
                    "material": material,
                    "used_30": used_30,
                    "daily_use": daily_use,
                    "days_left": days_left,
                    "status": "Reorder now" if material.is_low_stock else ("Watch" if days_left is not None and days_left <= 14 else "OK"),
                })
        forecast_rows = sorted(forecast_rows, key=lambda x: (x["days_left"] is None, x["days_left"] or Decimal("9999")))[:10]

        # Production capacity and queue pressure.
        pending_sheet_total = SaleLogItem.objects.filter(
            sale__in=open_orders
        ).aggregate(total=Sum("sheets_needed"))["total"] or 0
        due_today = open_orders.filter(due_date=today).count()
        overdue = [sale for sale in open_orders if sale.is_overdue]
        high_qty_orders = open_orders.filter(quantity__gte=300).count()
        capacity_level = "Normal"
        capacity_class = "good"
        if pending_sheet_total >= 60 or len(overdue) >= 3 or high_qty_orders >= 2:
            capacity_level = "High Load"
            capacity_class = "danger"
        elif pending_sheet_total >= 30 or due_today >= 3 or high_qty_orders >= 1:
            capacity_level = "Moderate Load"
            capacity_class = "warning"

        # CRM-lite customers.
        top_customers = (
            SaleLog.objects.exclude(customer_name="")
            .values("customer_name")
            .annotate(total=Sum("selling_price"), orders=Count("id"), profit=Sum("profit"), last_order=Max("created_at"))
            .order_by("-orders", "-total")[:8]
        )

        # Sales velocity by channel.
        channel_rows = (
            sales_30.values("platform")
            .annotate(total=Sum("selling_price"), orders=Count("id"), profit=Sum("profit"))
            .order_by("-total")[:6]
        )

        # One-click quote templates, designed for Messenger/FB.
        chat_templates = [
            {
                "title": "Small waterproof sticker bundle",
                "text": "Hi! For waterproof stickers, our starter bundle is 4 pcs for ₱100. Please send your design/photo and preferred size so we can confirm the final quote 😊",
            },
            {
                "title": "Logo labels quote",
                "text": "Hi! For logo labels, pricing depends on size and quantity. Send your logo, preferred size, and quantity, then we’ll compute the best price for you 😊",
            },
            {
                "title": "Rush order notice",
                "text": "Hi! We can accept rush orders depending on today’s queue. Rush jobs may have an additional fee and we’ll confirm the ready time before production.",
            },
            {
                "title": "Large order capacity notice",
                "text": "Hi! For large quantity orders, we’ll check our print/cut schedule first so we can give you a realistic completion date and avoid delays.",
            },
        ]

        # Decision cards.
        decisions = []
        if conversion_rate and conversion_rate < 35:
            decisions.append("Quote conversion is low. Test a lower aggressive price or use bundle offers for common products.")
        if forecast_rows and forecast_rows[0]["status"] == "Reorder now":
            decisions.append(f"Reorder {forecast_rows[0]['material'].item_name} soon to avoid production delays.")
        if capacity_level != "Normal":
            decisions.append("Queue load is elevated. Add lead-time warnings before accepting more rush jobs.")
        if not decisions:
            decisions.append("Operations look stable. Focus on repeat customers and bundle offers today.")

        ctx.update({
            "settings": settings,
            "quote_count_30": quote_count_30,
            "order_count_30": order_count_30,
            "conversion_rate": conversion_rate,
            "revenue_30": revenue_30,
            "profit_30": profit_30,
            "cost_30": cost_30,
            "avg_order_value": avg_order_value,
            "pricing_suggestions": pricing_suggestions,
            "forecast_rows": forecast_rows,
            "pending_sheet_total": pending_sheet_total,
            "due_today": due_today,
            "overdue_count": len(overdue),
            "high_qty_orders": high_qty_orders,
            "capacity_level": capacity_level,
            "capacity_class": capacity_class,
            "top_customers": top_customers,
            "channel_rows": channel_rows,
            "chat_templates": chat_templates,
            "decisions": decisions,
            "open_orders": open_orders.order_by("due_date", "-rush_order", "created_at")[:8],
        })
        return ctx


class ProductCategoryCreateView(CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = "costing/product_category_form.html"
    success_url = reverse_lazy("product_catalog")

    def form_valid(self, form):
        messages.success(self.request, "Product category added.")
        return super().form_valid(form)


class FastPOSView(TemplateView):
    """V3.7 Fast Counter POS: editable product buttons with live material-cost margin checks."""
    template_name = "costing/fast_pos.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        products = QuickPOSProduct.objects.filter(active=True).select_related(
            "product_type", "product_preset", "main_material", "lamination", "packaging"
        )
        ctx["pos_products"] = products
        ctx["low_margin_products"] = [p for p in products if p.is_low_margin]
        ctx["recent_pos_sales"] = SaleLog.objects.filter(notes__icontains="POS:")[:8]
        return ctx

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(QuickPOSProduct, pk=request.POST.get("product_id"), active=True)
        bundle_count = int(request.POST.get("bundle_count") or 1)
        customer_name = request.POST.get("customer_name", "Walk-in Customer") or "Walk-in Customer"
        payment_method = request.POST.get("payment_method") or SaleLog.PAYMENT_CASH

        requirements = product.material_requirements(bundle_count)
        sheets = requirements["sheets"]
        packaging_qty = requirements["packaging_qty"]

        selling_price = product.selling_price * Decimal(str(bundle_count))
        cost = product.estimated_cost * Decimal(str(bundle_count))
        profit = selling_price - cost
        total_qty = product.bundle_quantity * bundle_count

        sale = SaleLog.objects.create(
            platform=SaleLog.PLATFORM_WALKIN,
            customer_name=customer_name,
            order_name=product.name,
            sticker_size=product.button_label or product.name,
            quantity=total_qty,
            selling_price=selling_price,
            cost=cost,
            profit=profit,
            payment_method=payment_method,
            status=SaleLog.STATUS_PAID,
            job_status=SaleLog.JOB_RELEASED,
            deposit_amount=selling_price,
            notes=f"POS: {product.name} x {bundle_count} bundle(s)",
            cost_breakdown={
                "source": "V3.7 Fast POS",
                "pos_product_id": product.id,
                "bundle_count": bundle_count,
                "bundle_quantity": product.bundle_quantity,
                "estimated_cost_per_bundle": str(product.estimated_cost),
                "margin_per_bundle": str(product.estimated_margin),
            },
        )
        item = SaleLogItem.objects.create(
            sale=sale,
            line_number=1,
            product_name=product.name,
            sticker_size=product.button_label or product.name,
            material=product.main_material,
            lamination=product.lamination,
            packaging=product.packaging,
            material_name=product.main_material.item_name if product.main_material else "",
            lamination_name=product.lamination.item_name if product.lamination else "",
            packaging_name=product.packaging.item_name if product.packaging else "",
            quantity=total_qty,
            sheets_needed=int(sheets),
            material_qty_used=sheets,
            lamination_qty_used=sheets if product.lamination else Decimal("0.00"),
            packaging_qty_used=packaging_qty if product.packaging else Decimal("0.00"),
            unit_price=selling_price / Decimal(str(total_qty or 1)),
            line_total=selling_price,
            line_cost=cost,
            line_profit=profit,
        )

        # Deduct linked inventory immediately for paid POS sales.
        for material, qty in [
            (product.main_material, sheets),
            (product.lamination, sheets if product.lamination else Decimal("0.00")),
            (product.packaging, packaging_qty if product.packaging else Decimal("0.00")),
        ]:
            if material and qty and qty > 0:
                try:
                    material.deduct_stock(qty)
                    StockMovement.objects.create(
                        material=material,
                        sale=sale,
                        sale_item=item,
                        movement_type=StockMovement.MOVEMENT_OUT,
                        quantity=qty,
                        balance_after=material.stock_qty,
                        notes=f"Fast POS sale: {product.name}",
                    )
                except ValueError as exc:
                    messages.warning(request, str(exc))

        sale.stock_deducted = True
        sale.save(update_fields=["stock_deducted"])
        messages.success(request, f"POS sale logged: {product.name} x {bundle_count} bundle(s).")
        return redirect("fast_pos")


class QuickPOSProductListView(ListView):
    model = QuickPOSProduct
    template_name = "costing/pos_products.html"
    context_object_name = "pos_products"


class QuickPOSProductCreateView(CreateView):
    model = QuickPOSProduct
    form_class = QuickPOSProductForm
    template_name = "costing/pos_product_form.html"
    success_url = reverse_lazy("pos_products")


class QuickPOSProductUpdateView(UpdateView):
    model = QuickPOSProduct
    form_class = QuickPOSProductForm
    template_name = "costing/pos_product_form.html"
    success_url = reverse_lazy("pos_products")


class CreatePOSPriceSnapshotView(View):
    def post(self, request, pk):
        product = get_object_or_404(QuickPOSProduct, pk=pk)
        QuickPOSPriceSnapshot.objects.create(
            product=product,
            selling_price=product.selling_price,
            estimated_cost=product.estimated_cost,
            estimated_margin=product.estimated_margin,
            notes="Manual V3.7 price/cost snapshot",
        )
        messages.success(request, "POS price snapshot saved for inflation/material cost tracking.")
        return redirect("pos_products")


class SmartPasteView(TemplateView):
    """V5 Smart Paste: paste messy customer chat and turn it into a structured quote draft."""
    template_name = "costing/smart_paste.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = SmartPasteRawForm()
        ctx["recent_inquiries"] = SmartPasteInquiry.objects.all()[:10]
        ctx["main_materials"] = Material.objects.filter(is_active=True, category=Material.CATEGORY_STICKER).order_by("item_name")
        ctx["laminations"] = Material.objects.filter(is_active=True, category=Material.CATEGORY_LAMINATION).order_by("item_name")
        ctx["packagings"] = Material.objects.filter(is_active=True, category=Material.CATEGORY_PACKAGING).order_by("item_name")
        return ctx

    def post(self, request, *args, **kwargs):
        form = SmartPasteRawForm(request.POST)
        ctx = self.get_context_data()
        if not form.is_valid():
            ctx["form"] = form
            messages.error(request, "Please paste a customer message first.")
            return self.render_to_response(ctx)
        inquiry, parsed = create_smart_paste_inquiry(form.cleaned_data["raw_message"])
        ctx["form"] = SmartPasteRawForm(initial={"raw_message": form.cleaned_data["raw_message"]})
        ctx["inquiry"] = inquiry
        ctx["parsed"] = parsed
        ctx["recent_inquiries"] = SmartPasteInquiry.objects.all()[:10]
        messages.success(request, "Smart Paste parsed the message. Review the extracted quote details below.")
        return self.render_to_response(ctx)


class SmartPasteInquiryUpdateView(UpdateView):
    model = SmartPasteInquiry
    form_class = SmartPasteInquiryForm
    template_name = "costing/smart_paste_edit.html"
    success_url = reverse_lazy("smart_paste")

    def form_valid(self, form):
        messages.success(self.request, "Smart Paste inquiry updated.")
        return super().form_valid(form)
