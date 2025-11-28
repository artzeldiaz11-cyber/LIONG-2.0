from django.shortcuts import redirect, render
from myapp.models import Admin, Employee, Requisition, Requisition_Item, Products, InventoryBalance, StockIn, StockOut
from django.contrib import messages
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from datetime import date
from django.utils import timezone

from decimal import Decimal


# Create your views here.
def dashboard(request):
    return render(request, "liong/dashBoard.html")



def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(f"DEBUG: Login attempt for: {email}")  # Debug line

        try:
            admin = Admin.objects.get(email=email)
            print(f"DEBUG: Admin found - Role: {admin.role}, ID: {admin.acc_id}")  # Debug line

            # Plain-text password comparison
            if password == admin.password:
                # Check if this is an employee and verify their status
                if admin.role == 'employee':
                    print(f"DEBUG: This is an employee account")  # Debug line
                    
                    # METHOD 1: Find employee by admin foreign key (most reliable)
                    employee_by_admin = Employee.objects.filter(admin=admin).first()
                    if employee_by_admin:
                        print(f"DEBUG: Employee found by admin FK: {employee_by_admin.employee_name}, Status: {employee_by_admin.status}")  # Debug line
                        if employee_by_admin.status != 'active':
                            print(f"DEBUG: Employee is INACTIVE - blocking login")  # Debug line
                            messages.error(request, 'Your account has been deactivated. Please contact administrator.')
                            return render(request, 'liong/login.html')
                    else:
                        # METHOD 2: Find by contact value (email or phone)
                        employee_by_contact = Employee.objects.filter(contact_value=email).first()
                        if employee_by_contact:
                            print(f"DEBUG: Employee found by contact: {employee_by_contact.employee_name}, Status: {employee_by_contact.status}")  # Debug line
                            if employee_by_contact.status != 'active':
                                print(f"DEBUG: Employee is INACTIVE - blocking login")  # Debug line
                                messages.error(request, 'Your account has been deactivated. Please contact administrator.')
                                return render(request, 'liong/login.html')
                        else:
                            print(f"DEBUG: No employee record found for this admin")  # Debug line
                            # If no employee record found at all, allow login as fallback
                            pass

                # Set session
                request.session['acc_id'] = admin.acc_id
                request.session['admin_role'] = admin.role

                # Add success message

                # Redirect based on role after showing message
                if admin.role == 'super_admin':
                    return redirect('adminDashboard')
                elif admin.role == 'department_admin':
                    return redirect('department_dashboard')
                elif admin.role == 'inventory_admin':
                    return redirect('inventory_dashboard')
                elif admin.role == 'employee':
                    return redirect('employeeDashboard')
                else:
                    return redirect('admin_login')
            else:
                messages.error(request, 'Incorrect password')

        except Admin.DoesNotExist:
            messages.error(request, 'Account not found')

    return render(request, 'liong/login.html')


def index(request):
    return render(request, "liong/index.html")



def normalRequest(request):
    return render(request, "liong/normalRequest.html")



def adminDashboard(request):
    return render(request, "liong/adminDashboard.html")



def addEmployees(request):
    if 'acc_id' not in request.session:
        return redirect('admin_login')

    admin = Admin.objects.get(acc_id=request.session['acc_id'])

    if request.method == "POST":
        name = request.POST.get("employeeName")
        contact_type = request.POST.get("contactType")
        contact_value = request.POST.get("employeeContact")
        role = request.POST.get("employeeRole")
        date_joined = request.POST.get("employeeDate")

        role_in_db = request.POST.get("employeeRole") 
        # Create employee first
        employee = Employee.objects.create(
            admin=admin,  # This links the employee to the current admin
            employee_name=name,
            contact_type=contact_type,
            contact_value=contact_value,
            position=role_in_db,
            date_joined=date_joined,
            status='active'
        )

        # Only create admin account if we have valid credentials
        if contact_type == 'email' or (contact_type == 'phone' and '@' not in contact_value):
            # Check if login already exists
            if not Admin.objects.filter(email=contact_value).exists():
                default_password = get_random_string(length=8)
                
                admin_account = Admin.objects.create(
                    name=employee.employee_name,
                    email=contact_value,  # Use the contact value as email
                    password=default_password,
                    role=role_in_db,
                    department=employee.department
                )

                messages.success(
                    request,
                    f"Employee added successfully! Login: {contact_value}, Temp password: {default_password}"
                )
            else:
                messages.warning(
                    request,
                    f"Employee added but login already exists for: {contact_value}"
                )
        else:
            messages.success(request, "Employee added successfully! (No login account created)")

        return redirect("addEmployees")

    employees = Employee.objects.filter(admin=admin, status='active')
    return render(request, "liong/addEmployees.html", {"employees": employees})





def removeEmployee(request, emp_id):
    acc_id = request.session.get('acc_id')

    emp = Employee.objects.filter(employee_id=emp_id, acc_id=acc_id).first()
    if emp:
        # Soft delete - set status to inactive instead of deleting
        emp.status = 'inactive'
        emp.save()
        messages.success(request, "Employee deactivated successfully")
    else:
        messages.error(request, "Employee not found or unauthorized.")

    return redirect("addEmployees")




def request(request):
    if 'acc_id' not in request.session:
        return redirect('admin_login')

    # Get current user (employee)
    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    # Get products for the form
    products = Products.objects.all()
    
    # Get requisitions made by this employee
    employee = Employee.objects.filter(contact_value=current_admin.email).first()
    if employee:
        requisitions = Requisition.objects.filter(employee=employee).order_by('-date_requested')
    else:
        requisitions = Requisition.objects.none()

    if request.method == "POST":
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        new_product_names = request.POST.getlist('new_product_name[]')
        new_product_units = request.POST.getlist('new_product_unit[]')
        new_product_quantities = request.POST.getlist('new_product_quantity[]')
        remarks = request.POST.get('remarks', '')

        # Combine existing products and new products
        all_items = []
        
        # Process existing products
        for pid, qty in zip(product_ids, quantities):
            if pid and qty and float(qty) > 0:
                all_items.append(('existing', pid, qty))
        
        # Process new products
        for name, unit, qty in zip(new_product_names, new_product_units, new_product_quantities):
            if name and unit and qty and float(qty) > 0:
                all_items.append(('new', name.strip(), unit, qty))
        
        if not all_items:
            messages.error(request, "Please select at least one product with quantity greater than 0.")
        else:
            # Find the employee record for the current user
            employee = Employee.objects.filter(contact_value=current_admin.email).first()
            if not employee:
                messages.error(request, "Employee record not found. Please contact administrator.")
                return redirect('request')
            
            # Get a department admin to assign as admin_dep
            department_admin = Admin.objects.filter(role='department_admin', department=employee.department).first()
            if not department_admin:
                department_admin = Admin.objects.filter(role='department_admin').first()
            
            # Create the requisition
            requisition = Requisition.objects.create(
                employee=employee,
                remarks=remarks
            )
            
            # Track newly created products for success message
            newly_created_products = []
            
            for item in all_items:
                if item[0] == 'existing':  # Existing product
                    try:
                        product = Products.objects.get(product_id=item[1])
                        Requisition_Item.objects.create(
                            requisition=requisition,
                            product=product,
                            quantity=item[2]
                        )
                    except Products.DoesNotExist:
                        continue
                else:  # New product
                    # Check if product already exists (case-insensitive)
                    existing_product = Products.objects.filter(name__iexact=item[1]).first()
                    
                    if existing_product:
                        # Use existing product
                        product = existing_product
                    else:
                        # Create new product
                        product = Products.objects.create(
                            name=item[1],
                            unit=item[2]
                        )
                        newly_created_products.append(item[1])
                    
                    Requisition_Item.objects.create(
                        requisition=requisition,
                        product=product,
                        quantity=item[3]
                    )
            
            # Success message
            success_message = f"Requisition #{requisition.requisition_id} submitted successfully! Waiting for approval."
            if newly_created_products:
                success_message += f" New products added: {', '.join(newly_created_products)}"
            
            messages.success(request, success_message)
            return redirect('request')

    return render(request, "liong/request.html", {
        "products": products,
        "requisitions": requisitions,
        "today": now().date(),
        "current_user": current_admin
    })


def employeeDashboard(request):
    return render(request, "liong/employeeDashboard.html")


def requestApproval(request):
    if 'acc_id' not in request.session:
        return redirect('admin_login')
    
    # Get the current admin
    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    # Get requisitions based on admin role
    if current_admin.role == 'department_admin':
        # Department admin sees requisitions for their department
        requisitions = Requisition.objects.filter(
            admin_dep=current_admin
        ).select_related('employee').prefetch_related('requisition_item_set__product').order_by('-date_requested')
    else:
        # Other admins see all requisitions
        requisitions = Requisition.objects.select_related('employee').prefetch_related('requisition_item_set__product').order_by('-date_requested')
    
    # Count requisitions by status for statistics
    status_counts = {
        'pending': requisitions.filter(status='Pending').count(),
        'approved': requisitions.filter(status='Approved_Dep').count(),
        'denied': requisitions.filter(status='Denied').count(),
        'forwarded': requisitions.filter(status='Forwarded_Inv').count(),
    }
    
    return render(request, "liong/requestApproval.html", {
        "requisitions": requisitions,
        "status_counts": status_counts,
        "current_admin": current_admin
    })

def approve_requisition(request, requisition_id):
    if 'acc_id' not in request.session:
        return redirect('admin_login')
    
    try:
        requisition = Requisition.objects.get(requisition_id=requisition_id)
        
        # Check if the current admin has permission to approve this requisition
        if requisition.acc_id != request.session['acc_id']:
            messages.error(request, 'You are not authorized to approve this requisition.')
            return redirect('requestApproval')
        
        # Check stock availability before approving
        can_approve = True
        low_stock_items = []
        
        for item in requisition.requisition_item_set.all():
            try:
                balance = InventoryBalance.objects.get(product_id=item.product.product_id)
                if balance.quantity_unit < item.quantity:
                    can_approve = False
                    low_stock_items.append(f"{item.product.name} (Available: {balance.quantity_unit}, Requested: {item.quantity})")
            except InventoryBalance.DoesNotExist:
                can_approve = False
                low_stock_items.append(f"{item.product.name} (No stock data)")
        
        if not can_approve:
            messages.error(request, f'Cannot approve requisition. Insufficient stock: {", ".join(low_stock_items)}')
            return redirect('requestApproval')
        
        requisition.status = 'Approved_Dep'
        requisition.save()
        
        messages.success(request, f'Requisition #{requisition_id} approved successfully!')
        
    except Requisition.DoesNotExist:
        messages.error(request, 'Requisition not found.')
    
    return redirect('requestApproval')

def deny_requisition(request, requisition_id):
    if 'acc_id' not in request.session:
        return redirect('admin_login')
    
    try:
        requisition = Requisition.objects.get(requisition_id=requisition_id)
        
        # Check if the current admin has permission to deny this requisition
        if requisition.acc_id != request.session['acc_id']:
            messages.error(request, 'You are not authorized to deny this requisition.')
            return redirect('requestApproval')
        
        requisition.status = 'Denied'
        requisition.save()
        
        messages.success(request, f'Requisition #{requisition_id} denied.')
        
    except Requisition.DoesNotExist:
        messages.error(request, 'Requisition not found.')
    
    return redirect('requestApproval')

def forward_requisition(request, requisition_id):
    if 'acc_id' not in request.session:
        return redirect('admin_login')
    
    try:
        requisition = Requisition.objects.get(requisition_id=requisition_id)
        
        # Check if the current admin has permission to forward this requisition
        if requisition.acc_id != request.session['acc_id']:
            messages.error(request, 'You are not authorized to forward this requisition.')
            return redirect('requestApproval')
        
        requisition.status = 'Forwarded_Inv'
        requisition.save()
        
        messages.success(request, f'Requisition #{requisition_id} forwarded to inventory department.')
        
    except Requisition.DoesNotExist:
        messages.error(request, 'Requisition not found.')
    
    return redirect('requestApproval')










def inventory_dashboard(request):
    # Only inventory admins can access
    if request.session.get('admin_role') != 'inventory_admin':
        return redirect('admin_login')

    # Fetch all inventory balances with totals
    balances = InventoryBalance.objects.select_related('product').all()

    # Calculate analytics
    total_products = balances.count()
    low_stock_count = 0
    out_of_stock_count = 0
    healthy_stock_count = 0
    
    low_stock_products = []
    
    for b in balances:
        # Calculate current quantity
        b.current_quantity = b.quantity_unit or 0
        b.min_stock = b.min_stock or 0
        
        # Calculate deficit
        b.deficit = max(0, b.min_stock - b.current_quantity) if b.min_stock > 0 else 0
        
        # Categorize stock status
        if b.current_quantity == 0:
            out_of_stock_count += 1
            low_stock_products.append(b)
        elif b.current_quantity <= b.min_stock:
            low_stock_count += 1
            low_stock_products.append(b)
        else:
            healthy_stock_count += 1

    # Get recent activity (last 10 stock in/out records)
    recent_stock_in = StockIn.objects.select_related('product').order_by('-date_in')[:5]
    recent_stock_out = StockOut.objects.select_related('product').order_by('-date_out')[:5]
    
    recent_activity = []
    
    for stock_in in recent_stock_in:
        recent_activity.append({
            'type': 'in',
            'description': f'Stock in: {stock_in.product.name}',
            'quantity': f'+{stock_in.quantity}',
            'timestamp': stock_in.date_in
        })
    
    for stock_out in recent_stock_out:
        recent_activity.append({
            'type': 'out',
            'description': f'Stock out: {stock_out.product.name}',
            'quantity': f'-{stock_out.quantity}',
            'timestamp': stock_out.date_out
        })
    
    # Sort by timestamp (most recent first)
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:5]

    return render(request, 'liong/inventory_dashboard.html', {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'healthy_stock_count': healthy_stock_count,
        'low_stock_products': low_stock_products,
        'recent_activity': recent_activity
    })

# -------------------------
# STOCK IN
# -------------------------
def stock_in_view(request):
    if request.session.get('admin_role') != 'inventory_admin':
        return redirect('admin_login')

    products = Products.objects.all()

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity') or 0
        quantity_meters = request.POST.get('quantity_meters') or 0
        quantity_klg = request.POST.get('quantity_klg') or 0
        date_in = request.POST.get('date_in') or date.today()

        # Validate - removed unit check since it comes from product
        if not product_id:
            messages.error(request, "Please select a product.")
            return redirect('stock_in')

        try:
            product = Products.objects.get(pk=product_id)
            unit = product.unit  # Get unit from the product itself
        except Products.DoesNotExist:
            messages.error(request, "Product not found.")
            return redirect('stock_in')

        admin = Admin.objects.get(pk=request.session.get('acc_id'))

        # Create StockIn record
        StockIn.objects.create(
            product=product,
            unit=unit,  # Use the unit from the product
            quantity=float(quantity),
            quantity_meters=float(quantity_meters),
            quantity_klg=float(quantity_klg),
            date_in=date_in,
            acc=admin
        )

        # Update InventoryBalance
        balance, created = InventoryBalance.objects.get_or_create(
            product=product,
            defaults={
                'unit': unit,  # Use the unit from the product
                'quantity_unit': 0,
                'quantity_meters': 0,
                'quantity_klg': 0
            }
        )

        balance.quantity_unit = (balance.quantity_unit or 0) + float(quantity)
        balance.quantity_meters = (balance.quantity_meters or 0) + float(quantity_meters)
        balance.quantity_klg = (balance.quantity_klg or 0) + float(quantity_klg)
        balance.last_updated = timezone.now()
        balance.save()

        messages.success(request, f"{quantity} {unit} added to {product.name}.")
        return redirect('stock_in')

    return render(request, 'liong/stock_in.html', {'products': products})   


# -------------------------
# ADD PRODUCT
# -------------------------
def add_product(request):
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        unit = request.POST.get('unit')

        if not item_name or not unit:
            messages.error(request, "Please enter product name and select unit.")
            return redirect('stock_in')

        Products.objects.create(name=item_name, unit=unit)
        messages.success(request, f'Product "{item_name}" added successfully!')
        return redirect('stock_in')

    # If GET request (shouldn't happen from modal)
    return redirect('stock_in')
    

# -------------------------
# STOCK OUT
# -------------------------
from decimal import Decimal

def stock_out_view(request):
    if request.session.get('admin_role') != 'inventory_admin':
        return redirect('admin_login')

    # Fetch all products with inventory balance
    balances = InventoryBalance.objects.select_related('product').all()
    
    # Prepare product data for JS
    products = {}
    for b in balances:
        products[str(b.product.product_id)] = {
            'item_name': b.product.name,
            'unit_type': b.unit,
            'quantity_unit': float(b.quantity_unit),
            'quantity_meters': float(b.quantity_meters),
            'quantity_klg': float(b.quantity_klg)
        }

    if request.method == "POST":
        try:
            product_id = int(request.POST.get("product") or 0)
        except ValueError:
            messages.error(request, "Invalid product selected.")
            return redirect("stock_out")

        # Convert form values to Decimal
        qty_unit = Decimal(request.POST.get("quantity") or 0)
        qty_meters = Decimal(request.POST.get("quantity_meters") or 0)
        qty_klg = Decimal(request.POST.get("quantity_klg") or 0)
        date_out = request.POST.get("date_out") or timezone.now().date()

        try:
            balance = InventoryBalance.objects.get(product_id=product_id)
            unit_type = balance.unit  # Get unit from inventory balance
        except InventoryBalance.DoesNotExist:
            messages.error(request, "Product does not exist in inventory balance.")
            return redirect("stock_out")

        # Check stock availability
        if qty_unit > balance.quantity_unit or \
           qty_meters > balance.quantity_meters or \
           qty_klg > balance.quantity_klg:
            messages.error(request, "Not enough stock available!")
            return redirect("stock_out")

        # Deduct stock using Decimal operations
        balance.quantity_unit -= qty_unit
        balance.quantity_meters -= qty_meters
        balance.quantity_klg -= qty_klg
        balance.save()

        # Save stock-out record
        StockOut.objects.create(
            product_id=product_id,
            unit=unit_type,
            quantity=qty_unit,
            quantity_meters=qty_meters,
            quantity_klg=qty_klg,
            date_out=date_out,
            acc=request.session.get("acc_id")
        )

        messages.success(request, "Stock-out recorded successfully!")
        return redirect("stock_out")

    # Recent stock out
    recent_stock_out = StockOut.objects.select_related('product').order_by('-stock_out_id')[:10]

    return render(request, "liong/stock_out.html", {
        "products": balances,  # use balances for <select> options
        "products_json": products,  # for JS
        "recent_stock_out": recent_stock_out
    })
# -------------------------
# BALANCE
# -------------------------
def balance(request):
    if request.session.get('admin_role') != 'inventory_admin':
        return redirect('admin_login')

    balances = InventoryBalance.objects.select_related('product').all()
    return render(request, 'liong/balance.html', {'balances': balances})


# -------------------------
# LOGOUT
# -------------------------
def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')