# مستندات API بک‌اند کافه

## آدرس پایه

http://127.0.0.1:8000

تمام APIها با `/api/` شروع می‌شوند.

---

# ۱. احراز هویت

پروژه از JWT برای احراز هویت استفاده می‌کند.

برای APIهای محافظت‌شده:

Authorization: Bearer <access_token>

## ثبت‌نام

POST /api/register/

نیاز به احراز هویت ندارد.

نمونه درخواست:

{
  "username": "ali",
  "email": "ali@example.com",
  "password": "password123",
  "password2": "password123"
}

قوانین:
- رمز عبور حداقل ۸ کاراکتر باشد.
- password2 باید با password یکسان باشد.

---

## دریافت JWT

POST /api/token/

نمونه درخواست:

{
  "username": "ali",
  "password": "password123"
}

نمونه پاسخ:

{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}

---

## تمدید JWT

POST /api/token/refresh/

نمونه درخواست:

{
  "refresh": "<refresh_token>"
}

---

## پروفایل

GET /api/profile/

نیاز به JWT دارد.

نمونه پاسخ:

{
  "id": 1,
  "username": "ali",
  "email": "ali@example.com",
  "first_name": "",
  "last_name": ""
}

---

# ۲. محصولات

API محصولات عمومی است.

## لیست محصولات

GET /api/products/

Pagination فعال است و هر صفحه حداکثر ۵ محصول دارد.

### فیلترها

category
is_available

مثال:

/api/products/?category=1

/api/products/?is_available=true

### جستجو

فیلدهای جستجو:

name
description

مثال:

/api/products/?search=espresso

### مرتب‌سازی

فیلدهای قابل مرتب‌سازی:

price
name
stock
created_at

مثال:

/api/products/?ordering=price

برای مرتب‌سازی نزولی:

/api/products/?ordering=-price

مرتب‌سازی پیش‌فرض بر اساس name است.

---

## جزئیات محصول

GET /api/products/<id>/

مثال:

GET /api/products/5/

اگر محصول وجود نداشته باشد:

404 Not Found

---

## دسته‌بندی‌ها

GET /api/categories/

نیاز به احراز هویت ندارد.

---

# ۳. سبد خرید

تمام APIهای سبد خرید نیاز به JWT دارند.

## دریافت سبد خرید

GET /api/cart/

اگر کاربر Cart نداشته باشد، سیستم به‌صورت خودکار آن را ایجاد می‌کند.

---

## اضافه کردن محصول

POST /api/cart/add/<product_id>/

نمونه درخواست:

{
  "quantity": 2
}

اگر quantity ارسال نشود، مقدار پیش‌فرض 1 است.

بررسی‌ها:
1. وجود محصول
2. در دسترس بودن محصول
3. معتبر بودن quantity
4. بیشتر بودن quantity از صفر
5. بیشتر نشدن تعداد از موجودی

---

## کم کردن محصول

DELETE /api/cart/remove/<product_id>/

اگر quantity بیشتر از ۱ باشد، یک واحد کم می‌شود.

اگر quantity برابر ۱ باشد، CartItem حذف می‌شود.

---

## خالی کردن سبد

DELETE /api/cart/clear/

پاسخ:

{
  "message": "Cart cleared successfully"
}

---

## مجموع سبد

GET /api/cart/total/

نمونه پاسخ:

{
  "total_items": 2,
  "total_quantity": 5,
  "total_price": "600000.00"
}

total_items تعداد انواع محصول است.

total_quantity مجموع تعداد محصولات است.

total_price مجموع قیمت محصولات است.

---

# ۴. سفارش‌ها

تمام APIهای سفارش نیاز به JWT دارند.

## لیست سفارش‌های کاربر

GET /api/orders/

فقط سفارش‌های کاربر واردشده نمایش داده می‌شوند.

---

## جزئیات سفارش

GET /api/orders/<id>/

کاربر فقط سفارش‌های خودش را مشاهده می‌کند.

---

## ایجاد سفارش

POST /api/orders/create/

فرآیند:

Cart
↓
بررسی خالی نبودن
↓
دریافت CartItemها
↓
قفل کردن محصولات
↓
بررسی availability
↓
بررسی stock
↓
ایجاد Order
↓
ایجاد OrderItem
↓
کاهش stock
↓
خالی کردن Cart

این عملیات داخل transaction انجام می‌شود.

محصولات با select_for_update() قفل می‌شوند تا مشکل race condition در موجودی کاهش پیدا کند.

سفارش جدید با وضعیت PENDING ساخته می‌شود.

قیمت OrderItem در زمان خرید ذخیره می‌شود و با تغییر قیمت محصول در آینده تغییر نمی‌کند.

---

## لغو سفارش

POST /api/orders/<id>/cancel/

فقط سفارش‌های PENDING قابل لغو هستند.

هنگام لغو:
1. سفارش قفل می‌شود.
2. موجودی محصولات برگردانده می‌شود.
3. وضعیت سفارش به CANCELLED تغییر می‌کند.

پاسخ:

{
  "message": "Order cancelled successfully."
}

---

# ۵. پرداخت

تمام APIهای پرداخت نیاز به JWT دارند.

روش پرداخت فعلی:

CASH

## ایجاد پرداخت

POST /api/payment/<order_id>/

فرآیند:

Order
↓
قفل کردن Order
↓
بررسی PENDING
↓
بررسی پرداخت قبلی
↓
محاسبه مبلغ
↓
ایجاد Payment
↓
is_paid = True
↓
Order = PAID

فقط سفارش‌های PENDING قابل پرداخت هستند.

پرداخت تکراری مجاز نیست.

---

# ۶. وضعیت سفارش

وضعیت‌های موجود:

PENDING
PAID
CANCELLED
DELIVERED

جریان فعلی:

PENDING
├──> PAID
└──> CANCELLED

DELIVERED در مدل وجود دارد، اما در API فعلی Endpointی برای تغییر سفارش به DELIVERED وجود ندارد.

---

# ۷. خلاصه احراز هویت

| API | احراز هویت |
|---|---|
| ثبت‌نام | عمومی |
| دریافت Token | عمومی |
| Refresh Token | عمومی |
| پروفایل | JWT |
| محصولات | عمومی |
| دسته‌بندی‌ها | عمومی |
| سبد خرید | JWT |
| سفارش‌ها | JWT |
| پرداخت | JWT |

---

# ۸. قوانین اصلی سیستم

1. اطلاعات شخصی Cart، Order و Payment فقط برای کاربر احراز هویت‌شده قابل دسترسی است.
2. کاربر فقط سفارش‌های خودش را می‌بیند.
3. قبل از اضافه کردن محصول، availability بررسی می‌شود.
4. تعداد محصول در Cart نمی‌تواند از stock بیشتر باشد.
5. سفارش از Cart خالی ایجاد نمی‌شود.
6. هنگام ایجاد سفارش، stock دوباره بررسی می‌شود.
7. محصولات هنگام ایجاد سفارش قفل می‌شوند.
8. ایجاد سفارش، کاهش stock و خالی کردن Cart داخل یک transaction انجام می‌شود.
9. فقط PENDING قابل لغو است.
10. لغو سفارش stock را برمی‌گرداند.
11. فقط PENDING قابل پرداخت است.
12. Payment تکراری مجاز نیست.
13. پرداخت موفق وضعیت Order را به PAID تغییر می‌دهد.
14. قیمت OrderItem قیمت زمان خرید را حفظ می‌کند.

---

# ۹. وضعیت تست پروژه

Django system check: PASS

Migration check: PASS

Automated tests: 63/63 PASS

پروژه در حال حاضر برای Development از SQLite استفاده می‌کند و احراز هویت آن با JWT انجام می‌شود.
