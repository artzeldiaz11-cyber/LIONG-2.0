from django.db import models

class Admin(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('department_admin', 'Department Admin'),
        ('inventory_admin', 'Inventory Admin'),
        ('employee', 'Employee'),
    ]

    acc_id = models.AutoField(primary_key=True)  # match your PostgreSQL PK
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.role})"

    class Meta:
        db_table = 'account'


class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    admin = models.ForeignKey(Admin, db_column='acc_id', on_delete=models.CASCADE)
    employee_name = models.CharField(max_length=100)
    contact_type = models.CharField(max_length=10, default="N/A")
    contact_value = models.CharField(max_length=100, default="N/A")
    position = models.CharField(max_length=50, blank=True, null=True)
    department = models.CharField(max_length=50, blank=True, null=True)
    date_joined = models.DateField()
    date_added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10, 
        choices=[('active', 'Active'), ('inactive', 'Inactive')], 
        default='active'
    )

    class Meta:
        db_table = "employee"

    def __str__(self):
        return self.employee_name

class Products(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    stock = models.IntegerField(default=0)

    class Meta:
        db_table = "products"

    def __str__(self):
        return self.name


class Requisition(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved_Dep', 'Approved_Dep'),
        ('Denied', 'Denied'),
        ('Forwarded_Inv', 'Forwarded_Inv')
    ]

    requisition_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date_requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "requisition"

    def __str__(self):
        return f"REQ-{self.requisition_id} | {self.employee.employee_name}"


class Requisition_Item(models.Model):
    id = models.AutoField(primary_key=True)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "requisition_item"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"



class InventoryBalance(models.Model):
    balance_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    unit = models.CharField(max_length=20)
    opening_inventory = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_meters = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_klg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    procurement_suggestion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.unit}"

    class Meta:
        db_table = 'inventory_balance'  # Explicit table name
# models.py (add below InventoryBalance)

class StockIn(models.Model):
    stock_in_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    unit = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_meters = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_klg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_in = models.DateField()
    acc = models.ForeignKey(Admin, on_delete=models.CASCADE, db_column='acc_id', null=True)

    class Meta:
        db_table = 'stock_in'

    def __str__(self):
        return f"{self.product.item_name} - {self.quantity} {self.unit} (In)"

class StockOut(models.Model):
    stock_out_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    unit = models.CharField(max_length=20)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_meters = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_klg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_out = models.DateField()
    acc = models.ForeignKey(Admin, on_delete=models.CASCADE, db_column='acc_id', null=True)

    class Meta:
        db_table = 'stock_out'

    def __str__(self):
        return f"{self.product.item_name} - {self.quantity} {self.unit} (Out)"