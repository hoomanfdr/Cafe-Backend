from django.db import models


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="نام دسته‌بندی"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True,
        verbose_name="تصویر"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="دسته‌بندی"
    )

    name = models.CharField(
        max_length=150,
        verbose_name="نام محصول"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="قیمت"
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="تصویر"
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی"
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="موجود"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["name"]

    def __str__(self):
        return self.name