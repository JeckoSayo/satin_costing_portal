from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from . import services
from .models import CustomerOrder, ExpenseLog, Material, SaleLog, ShopTask, StockMovement, StockPurchase


def _after_commit(callback):
    transaction.on_commit(callback)


@receiver(pre_save, sender=SaleLog)
def remember_sale_previous_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        instance._previous_job_status = None
        return

    previous = sender.objects.filter(pk=instance.pk).values("status", "job_status").first()
    instance._previous_status = previous["status"] if previous else None
    instance._previous_job_status = previous["job_status"] if previous else None


@receiver(post_save, sender=SaleLog)
def broadcast_sale_saved(sender, instance, created, **kwargs):
    def notify():
        services.broadcast_dashboard_update()
        services.broadcast_sales_update()

        if created:
            services.broadcast_notification(
                "New order added",
                f"{instance.receipt_number or 'New order'} was added for {instance.customer_name or 'Walk-in'}.",
                level="info",
                event="order.created",
            )
        elif instance.status == SaleLog.STATUS_PAID and getattr(instance, "_previous_status", None) != SaleLog.STATUS_PAID:
            services.broadcast_notification(
                "Payment marked as paid",
                f"{instance.receipt_number} is now paid.",
                level="success",
                event="payment.paid",
            )

    _after_commit(notify)


@receiver(post_delete, sender=SaleLog)
def broadcast_sale_deleted(sender, instance, **kwargs):
    _after_commit(lambda: (services.broadcast_dashboard_update(), services.broadcast_sales_update()))


@receiver(pre_save, sender=ShopTask)
def remember_task_previous_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return

    previous = sender.objects.filter(pk=instance.pk).values("status").first()
    instance._previous_status = previous["status"] if previous else None


@receiver(post_save, sender=ShopTask)
def broadcast_task_saved(sender, instance, created, **kwargs):
    def notify():
        services.broadcast_dashboard_update()
        if instance.status == ShopTask.STATUS_DONE and getattr(instance, "_previous_status", None) != ShopTask.STATUS_DONE:
            services.broadcast_notification(
                "Task completed",
                instance.title,
                level="success",
                event="task.completed",
            )

    _after_commit(notify)


@receiver(post_delete, sender=ShopTask)
def broadcast_task_deleted(sender, instance, **kwargs):
    _after_commit(services.broadcast_dashboard_update)


@receiver(post_save, sender=Material)
def broadcast_material_saved(sender, instance, created, **kwargs):
    def notify():
        services.broadcast_inventory_update(material=instance)
        services.broadcast_dashboard_update()
        if instance.is_low_stock:
            services.broadcast_notification(
                "Low stock alert",
                f"{instance.item_name} is down to {instance.stock_qty} {instance.unit}.",
                level="warning",
                event="inventory.low_stock",
            )

    _after_commit(notify)


@receiver(post_delete, sender=Material)
def broadcast_material_deleted(sender, instance, **kwargs):
    _after_commit(lambda: (services.broadcast_inventory_update(), services.broadcast_dashboard_update()))


@receiver(post_save, sender=StockMovement)
def broadcast_stock_movement_saved(sender, instance, created, **kwargs):
    _after_commit(lambda: services.broadcast_inventory_update(material=instance.material))


@receiver(post_save, sender=StockPurchase)
def broadcast_stock_purchase_saved(sender, instance, created, **kwargs):
    _after_commit(lambda: services.broadcast_inventory_update(material=instance.material))


@receiver(post_save, sender=ExpenseLog)
@receiver(post_delete, sender=ExpenseLog)
def broadcast_expense_changed(sender, instance, **kwargs):
    _after_commit(services.broadcast_dashboard_update)


@receiver(post_save, sender=CustomerOrder)
@receiver(post_delete, sender=CustomerOrder)
def broadcast_customer_order_changed(sender, instance, **kwargs):
    _after_commit(lambda: (services.broadcast_customer_queue_update(), services.broadcast_staff_queue_update()))
