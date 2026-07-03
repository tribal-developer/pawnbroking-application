from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import CustomerForm
from .models import Customer


@login_required
def customer_list(request):
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(
            Q(full_name__icontains=query)
            | Q(phone_number__icontains=query)
            | Q(id_proof_number__icontains=query)
        )
    return render(request, 'customers/customer_list.html', {'customers': customers, 'query': query})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    loans = customer.loans.all().select_related('item')
    return render(request, 'customers/customer_detail.html', {'customer': customer, 'loans': loans})


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.full_name}' registered.")
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Register New Customer'})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer details updated.")
            return redirect('customers:detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customers/customer_form.html', {'form': form, 'title': f'Edit {customer.full_name}'})
