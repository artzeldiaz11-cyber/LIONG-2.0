from django.shortcuts import redirect, render
from myapp.models import Admin, Employee, Requisition, Requisition_Item, Products, InventoryBalance, StockIn, StockOut, RequisitionStatusHistory
from django.contrib import messages
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from datetime import date
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.db.models import Q



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

    emp = Employee.objects.filter(employee_id=emp_id, admin_id=acc_id).first()
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

    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    inventory_products = InventoryBalance.objects.select_related('product').all()

    products = []
    for inv in inventory_products:
        products.append({
            "product_id": inv.product.product_id,
            "name": inv.product.name,
            "unit": inv.unit,
            "available_qty": inv.quantity_unit
        })
    
    # Get requisitions made by this employee
    employee = Employee.objects.filter(contact_value=current_admin.email).first()
    if employee:
        requisitions = Requisition.objects.filter(employee=employee).order_by('-date_requested')
    else:
        requisitions = Requisition.objects.none()

    # Handle POST (form submission)
    if request.method == "POST":
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        remarks = request.POST.get('remarks', '')

        all_items = []
        for pid, qty in zip(product_ids, quantities):
            if pid and qty and float(qty) > 0:
                all_items.append(('existing', pid, qty))
        
        if not all_items:
            messages.error(request, "Please select at least one product with quantity greater than 0.")
        else:
            if not employee:
                messages.error(request, "Employee record not found. Please contact administrator.")
                return redirect('request')
            
            requisition = Requisition.objects.create(
                employee=employee,
                remarks=remarks
            )
            
            for item in all_items:
                product = Products.objects.get(product_id=item[1])
                Requisition_Item.objects.create(
                    requisition=requisition,
                    product=product,
                    quantity=item[2]
                )
            
            messages.success(request, f"Requisition #{requisition.requisition_id} submitted successfully! Waiting for approval.")
            return redirect('request')

    return render(request, "liong/request.html", {
        "products": products,
        "requisitions": requisitions,
        "today": now().date(),
        "current_user": current_admin
    })





def employeeDashboard(request):
    return render(request, "liong/employeeDashboard.html")




# ---------------------------------------------------------------
# ADMIN DASHBOARD - SIMPLE APPROVE/DENY ONLY (NO STOCK CHECK)
# ---------------------------------------------------------------
def requestApproval(request):
    """Admin view - shows all requisitions, only Approve/Deny actions"""
    if 'acc_id' not in request.session:
        return redirect('admin_login')

    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    # For admin, show ALL requisitions
    requisitions = (
        Requisition.objects
        .select_related('employee')
        .prefetch_related('requisition_item_set__product')
        .order_by('-date_requested')
    )

    # Counts for admin dashboard
    status_counts = {
        'pending_approval': requisitions.filter(status='Pending Approval').count(),
        'partially_approved_pending_purchase': requisitions.filter(status='Partially Approved – Pending Purchase').count(),
        'pending_purchase': requisitions.filter(status='Pending Purchase').count(),
        'approved': requisitions.filter(status='Approved').count(),
        'denied': requisitions.filter(status='Denied').count(),
    }

    return render(request, "liong/requestApproval.html", {
        "requisitions": requisitions,
        "status_counts": status_counts,
        "current_admin": current_admin
    })


@require_POST
@transaction.atomic
def approve_requisition(request, requisition_id):
    """ADMIN ACTION: Simple approve - NO STOCK CHECK, always approves"""
    if 'acc_id' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('admin_login')

    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    # Only super_admin can approve
    if current_admin.role != 'super_admin':
        messages.error(request, "You are not authorized to approve requisitions.")
        return redirect('requestApproval')

    requisition = get_object_or_404(Requisition, pk=requisition_id)
    
    # Can only approve Pending Approval requisitions
    if requisition.status != 'Pending Approval':
        messages.error(request, f"Requisition #{requisition.requisition_id} is already processed.")
        return redirect('requestApproval')

    old_status = requisition.status
    
    # ADMIN RULE: Always approve, NO stock check
    requisition.status = "Approved"
    
    # Set approved quantities equal to requested quantities
    items = Requisition_Item.objects.filter(requisition=requisition)
    for item in items:
        item.approved_quantity = item.quantity
        item.save()
    
    # DO NOT deduct from inventory here - inventory will handle that
    
    # Log status change
    log_status_change(requisition, old_status, requisition.status, request)
    requisition.save()

    messages.success(request, f"Requisition #{requisition.requisition_id} approved.")
    return redirect('requestApproval')


@require_POST
def deny_requisition(request, requisition_id):
    """ADMIN ACTION: Simple deny"""
    if 'acc_id' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('admin_login')

    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    # Only super_admin can deny
    if current_admin.role != 'super_admin':
        messages.error(request, "You are not authorized to deny requisitions.")
        return redirect('requestApproval')

    requisition = get_object_or_404(Requisition, pk=requisition_id)
    
    # Can only deny Pending Approval requisitions
    if requisition.status != 'Pending Approval':
        messages.error(request, f"Requisition #{requisition.requisition_id} is already processed.")
        return redirect('requestApproval')

    old_status = requisition.status
    requisition.status = "Denied"
    requisition.save()

    # Log status change
    log_status_change(requisition, old_status, requisition.status, request)

    messages.success(request, f"Requisition #{requisition.requisition_id} denied.")
    return redirect('requestApproval')


def admin_requisition_view(request, req_id):
    """ADMIN VIEW: Modal for admin dashboard (simple view)"""
    req = get_object_or_404(Requisition, pk=req_id)
    items = Requisition_Item.objects.filter(requisition=req).select_related('product')

    # Show items without stock check
    for item in items:
        item.requested_qty = item.quantity

    return render(request, "liong/partials/admin_requisition_modal.html", {
        "req": req,
        "items": items
    })


# ---------------------------------------------------------------
# INVENTORY DASHBOARD - HANDLES STOCK MANAGEMENT
# ---------------------------------------------------------------
def inventory_approved_requisitions(request):
    """Inventory view - shows ONLY approved requisitions for stock management"""
    if 'acc_id' not in request.session:
        return redirect('admin_login')

    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])

    # Inventory sees ONLY approved requisitions
    requisitions = (
        Requisition.objects
        .filter(status='Approved')  # ONLY approved ones
        .select_related('employee')
        .prefetch_related('requisition_item_set__product')
        .order_by('-date_requested')
    )

    return render(request, "liong/inventory_approved_requisitions.html", {
        "requisitions": requisitions,
        "current_admin": current_admin
    })


@require_POST
@transaction.atomic
def inventory_partial_approve(request, requisition_id):
    """INVENTORY ACTION: Check stock and approve partially if needed"""
    if 'acc_id' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('admin_login')

    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    # Only super_admin (acting as inventory) can do this
    if current_admin.role != 'super_admin':
        messages.error(request, "You are not authorized for inventory actions.")
        return redirect('inventory_approved_requisitions')

    requisition = get_object_or_404(Requisition, pk=requisition_id)
    
    # Can only process Approved requisitions
    if requisition.status != 'Approved':
        messages.error(request, f"Requisition #{requisition.requisition_id} is not approved.")
        return redirect('inventory_approved_requisitions')

    old_status = requisition.status
    items = Requisition_Item.objects.filter(requisition=requisition).select_related('product')
    partial = False
    recommendation = ""
    total_deducted = 0

    for item in items:
        product = item.product
        requested_qty = item.quantity

        # Get inventory
        try:
            inv_balance = InventoryBalance.objects.get(product=product)
            available_stock = inv_balance.quantity_unit
        except InventoryBalance.DoesNotExist:
            available_stock = 0

        if available_stock <= 0:
            # No stock at all
            partial = True
            item.approved_quantity = 0  # Can't give any
            recommendation += f"{product.name}: No stock available. Need to purchase {requested_qty}. "
        
        elif requested_qty > available_stock:
            # Partial stock available
            partial = True
            item.approved_quantity = available_stock  # Give what we have
            remaining = requested_qty - available_stock
            recommendation += f"{product.name}: Only {available_stock} available. Need to purchase {remaining}. "
            
            # Deduct available stock
            inv_balance.quantity_unit = 0
            inv_balance.save()
            total_deducted += available_stock
        
        else:
            # Full stock available
            item.approved_quantity = requested_qty  # Give full amount
            
            # Deduct from inventory
            inv_balance.quantity_unit -= requested_qty
            inv_balance.save()
            total_deducted += requested_qty

        item.save()

    # Update requisition status based on inventory check
    if partial:
        requisition.status = "Partially Approved – Pending Purchase"
        requisition.recommendation = recommendation
        messages.warning(request, f"Requisition #{requisition.requisition_id} partially fulfilled. Stock deducted: {total_deducted}. Purchase needed.")
    else:
        # Fully fulfilled from stock
        requisition.status = "Approved"  # Still approved, but now fulfilled
        messages.success(request, f"Requisition #{requisition.requisition_id} fully fulfilled from stock. Total deducted: {total_deducted}.")

    # Log status change
    log_status_change(requisition, old_status, requisition.status, request)
    requisition.save()

    return redirect('inventory_approved_requisitions')


@require_POST
@transaction.atomic
def inventory_fulfill_from_stock(request, requisition_id):
    """INVENTORY ACTION: Try to fulfill from available stock"""
    if 'acc_id' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('admin_login')

    current_admin = Admin.objects.get(acc_id=request.session['acc_id'])
    
    if current_admin.role != 'super_admin':
        messages.error(request, "You are not authorized for inventory actions.")
        return redirect('inventory_approved_requisitions')

    requisition = get_object_or_404(Requisition, pk=requisition_id)
    
    # Can only process approved or partially approved requisitions
    if requisition.status not in ['Approved', 'Partially Approved – Pending Purchase']:
        messages.error(request, f"Requisition #{requisition.requisition_id} cannot be fulfilled.")
        return redirect('inventory_approved_requisitions')

    old_status = requisition.status
    items = Requisition_Item.objects.filter(requisition=requisition).select_related('product')
    can_fully_fulfill = True
    total_deducted = 0

    # First check if we can fully fulfill
    for item in items:
        try:
            inv_balance = InventoryBalance.objects.get(product=item.product)
            if inv_balance.quantity_unit < item.quantity:
                can_fully_fulfill = False
                break
        except InventoryBalance.DoesNotExist:
            can_fully_fulfill = False
            break

    if can_fully_fulfill:
        # Fully fulfill from stock
        for item in items:
            inv_balance = InventoryBalance.objects.get(product=item.product)
            inv_balance.quantity_unit -= item.quantity
            inv_balance.save()
            total_deducted += item.quantity
            item.approved_quantity = item.quantity
            item.save()
        
        requisition.status = "Approved"
        messages.success(request, f"Requisition #{requisition.requisition_id} fully fulfilled from stock. Total deducted: {total_deducted}.")
    else:
        # Mark for purchase
        requisition.status = "Pending Purchase"
        messages.info(request, f"Requisition #{requisition.requisition_id} marked for purchase (insufficient stock).")

    # Log status change
    log_status_change(requisition, old_status, requisition.status, request)
    requisition.save()

    return redirect('inventory_approved_requisitions')


def inventory_requisition_view(request, req_id):
    """INVENTORY VIEW: Modal for inventory dashboard (detailed view with stock info)"""
    req = get_object_or_404(Requisition, pk=req_id)
    items = Requisition_Item.objects.filter(requisition=req).select_related('product')

    # Get approval history
    approval_history = RequisitionStatusHistory.objects.filter(
        requisition=req
    ).order_by('-changed_at')

    # Check inventory balance with details
    for item in items:
        try:
            bal = InventoryBalance.objects.get(product=item.product)
            item.available_qty = bal.quantity_unit
            item.has_stock = bal.quantity_unit >= item.quantity
            item.shortage = max(0, item.quantity - bal.quantity_unit)
        except:
            item.available_qty = 0
            item.has_stock = False
            item.shortage = item.quantity

    return render(request, "liong/partials/inventory_requisition_modal.html", {
        "req": req,
        "items": items,
        "approval_history": approval_history
    })


# ---------------------------------------------------------------
# SHARED FUNCTIONS
# ---------------------------------------------------------------
def log_status_change(req, old_status, new_status, request):
    """Shared function to log status changes"""
    try:
        admin_id = request.session.get('acc_id')
        if not admin_id:
            print("No admin_id in session")
            return
            
        admin_user = Admin.objects.get(pk=admin_id)
        
        RequisitionStatusHistory.objects.create(
            requisition=req,
            old_status=old_status,
            new_status=new_status,
            changed_by=admin_user
        )
        print(f"Status change logged: {old_status} -> {new_status} for requisition {req.requisition_id}")
        
    except Admin.DoesNotExist:
        print(f"Admin with id {admin_id} does not exist")
    except Exception as e:
        print(f"Error logging status change: {str(e)}")





































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