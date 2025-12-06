from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=120, unique=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    image = models.ImageField(
        _('image'),
        upload_to='categories/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def products_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=220, unique=True, blank=True)
    description = models.TextField(_('description'))
    short_description = models.CharField(
        _('short description'),
        max_length=500,
        blank=True
    )

    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    discount_price = models.DecimalField(
        _('discount price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        default=0
    )

    stock = models.IntegerField(
        _('stock'),
        default=0,
        validators=[MinValueValidator(0)]
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('category')
    )

    image = models.ImageField(
        _('main image'),
        upload_to='products/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(_('is active'), default=True)
    is_featured = models.BooleanField(_('is featured'), default=False)

    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.CharField(_('meta description'), max_length=200, blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['price'])
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_on_sale(self):
        return self.discount_price and self.discount_price < self.price

    @property
    def final_price(self):
        if self.is_on_sale:
            return self.discount_price
        return self.price

    @property
    def discount_percentage(self):
        if not self.is_on_sale or not self.discount_price:
            return Decimal("0")

        discount = self.price - self.discount_price
        return round((discount / self.price) * 100, 2)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product')
    )
    image = models.ImageField(_('image'), upload_to='products/')
    alt_text = models.CharField(_('alt text'), max_length=200, blank=True)
    order = models.PositiveIntegerField(_('order'), default=0)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        db_table = 'product_images'
        verbose_name = _('product_image')
        verbose_name_plural = _('products_images')
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.product.name} - Image {self.id}'
