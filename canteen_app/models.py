from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    roll_no = models.CharField(max_length=30, unique=True)
    ROLE_CHOICES = (('student','Student'),('faculty','Faculty'),('admin','Admin'))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.roll_no} - {self.get_full_name() or self.username}"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class MenuItem(models.Model):
    itemid = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20)   # Veg / Nonveg / Packaged
    portion = models.CharField(max_length=100, blank=True, null=True)
    availability = models.CharField(max_length=80, default='All Day')
    price = models.FloatField(default=0.0)
    preference_score = models.FloatField(default=0.0)
    active = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.itemid} - {self.name}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(MenuItem, through='OrderItem')
    total_price = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self): return f"Order {self.id} by {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
