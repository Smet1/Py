from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, ListView
from myapp.models import BankModel, CustomerModel, AccountModel, TransactionsModel
from myapp.forms import UserRegistrationForm, UserAuthenticationForm, AddTransactionForm
import math
import datetime, time
import json
from django.db.models import F


def user_type(request):
    if not request.user.is_authenticated:
        usr_type = ''
        usr_id = ''
    else:
        usr_type = request.user
        usr_id = CustomerModel.objects.get(login=usr_type)

    print('data: {}, usr_id: {}'.format(usr_type, usr_id))
    return usr_type, usr_id


# Create your views here.
class Home(View):
    def get(self, request):
        data, usr_id = user_type(request)
        return render(request, 'main.html', {'usr_type': data, 'usr_id': usr_id})


class Bank(ListView):
    model = BankModel
    template_name = 'banks_main.html'
    context_object_name = 'banks'
    # paginate_by = 3

    def get(self, request, page=1):

        usr_type, usr_id = user_type(request)

        # Количество банков на странице
        elements_on_page = 2

        # Количество банков в строке
        elements_in_row = 1

        banks = BankModel.objects.all()
        pages_count = math.ceil(len(banks) / elements_on_page)

        start_index = (int(page) - 1) * elements_on_page
        end_index = start_index + elements_on_page
        banks = banks[start_index:end_index]

        index = 1
        rows = []
        row = []
        for bank in banks:
            row.append(bank)
            index += 1
            '''
            if index == elements_in_row:
                rows.append(row)
                row = []
                index = 1
            else:
                index += 1
            '''
        if len(row) > 0:
            rows.append(row)

        # page += 1
        return render(request, 'banks_main.html', {'banks': rows, 'page': page, 'pages_count': pages_count,
                                                   'usr_type': usr_type, 'usr_id': usr_id})
    '''def get(self, request):
        data = BankModel.objects.all()
        usr_type, usr_id = user_type(request)
        return render(request, 'banks_main.html', {'banks': data, 'usr_type': usr_type, 'usr_id': usr_id})'''


class BankInDetail(View):
    def get(self, request, id):
        data = BankModel.objects.get(idBanks=int(id))
        usr_type, usr_id = user_type(request)
        return render(request, 'bank_detail.html', {'banks': data, 'usr_type': usr_type, 'usr_id': usr_id})


class Customer(View):
    def get(self, request):
        data_cus = CustomerModel.objects.all()
        usr_type, usr_id = user_type(request)
        return render(request, 'customer_main.html', {'customers': data_cus, 'usr_type': usr_type, 'usr_id': usr_id})


class CustomerInDetail(View):
    def get(self, request):
        usr_type, usr_id = user_type(request)
        id = int(usr_id.idCustomer)
        data = CustomerModel.objects.get(idCustomer=int(id))
        data1 = AccountModel.objects.filter(customerId_FK=int(id))
        data_to = []
        data_from = []
        for x in data1:
            data_from += TransactionsModel.objects.filter(accountId_from=x.idAccounts)
            data_to += TransactionsModel.objects.filter(accountId_to=x.idAccounts)

        return render(request, 'customer_detail.html', {'customers': data, 'accts': data1, 'trans_to': data_to,
                                                        'trans_from': data_from, 'usr_type': usr_type,
                                                        'usr_id': usr_id})


class CustomerAccounts(View):
    @method_decorator(login_required(login_url='/auth/'))
    def get(self, request, id):  # передаю id счета
        usr_type, usr_id = user_type(request)
        data = AccountModel.objects.get(idAccounts=int(id))
        data_from = TransactionsModel.objects.filter(accountId_from=int(id))
        data_to = TransactionsModel.objects.filter(accountId_to=int(id))

        return render(request, 'accounts.html', {'accts': data, 'usr_type': usr_type, 'usr_id': usr_id,
                                                      'trans_to': data_to, 'trans_from': data_from})


# добавление транзакции, прилетает сверху из модалки
@csrf_exempt
def modal_transaction(request):
    if request.method == 'POST':
        time_1 = datetime.datetime.now()

        accountId_to = AccountModel.objects.get(idAccounts=int(request.POST.get('account_to')))
        accountId_from = AccountModel.objects.get(idAccounts=int(request.POST.get('account_from')))

        money = request.POST.get('money')
        currency = AccountModel.objects.get(idAccounts=int(request.POST.get('account_from'))).currency
        comments = request.POST.get('comments')

        if accountId_from.money < int(money):
            return HttpResponse(
                json.dumps({"nothing to see": "this isn't happening"}),
                content_type="application/json"
            )

        data = {
            'accountId_to': accountId_to.idAccounts,
            'accountId_from': accountId_from.idAccounts,
            'money': money,
            'currency': currency,
            'comments': comments,
            'time_t': time_1
        }
        transaction = AddTransactionForm(data)
        transaction.save()

        # снятие с аккаунта_from
        account_from = accountId_from
        account_from.money = F('money') - money
        account_from.save()

        # пополнение аккаунта_to
        account_to = accountId_to
        account_to.money = F('money') + money
        account_to.save()
        # получаю запись транзакции, т.к. id не вытащить
        ready_trans = TransactionsModel.objects.get(time_t=time_1)
        print('ready:  ', ready_trans)
        # Формируем json с отзывом для обновления страницы
        response_data = dict()
        response_data["idTransactions"] = ready_trans.idTransactions
        response_data["accountId_from"] = ready_trans.accountId_from.idAccounts
        response_data["fio_from"] = ready_trans.accountId_from.customerId_FK.fio
        response_data["accountId_to"] = ready_trans.accountId_to.idAccounts
        response_data["money"] = ready_trans.money
        response_data["currency"] = ready_trans.currency
        response_data["comments"] = ready_trans.comments
        response_data["time_t"] = time.asctime()

        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"nothing to see": "this isn't happening"}),
            content_type="application/json"
        )


class CustomerTransactions(View):
    @method_decorator(login_required(login_url='/auth/'))
    def get(self, request):
        usr_type, usr_id = user_type(request)
        data = TransactionsModel.objects.all()
        return render(request, 'transactions_main.html', {'trans': data, 'usr_type': usr_type, 'usr_id': usr_id})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/home/')


def registration1(request):
    errors = []
    if request.method == 'POST':
        username = request.POST.get('username')
        if not username:
            errors.append('Введите логин')
        elif len(username) < 4:
            errors.append('Длина пароля должна быть >=4')

        password = request.POST.get('password')
        if not password:
            errors.append('Введите пароль')
        elif len(password) < 3:
            errors.append('Длина пароля должна быть >=3')
        password_repeat = request.POST.get('password2')

        if password != password_repeat:
            errors.append('Пароли не совпадают')

        if not errors:
            return HttpResponseRedirect('/login/')

        return render(request, 'registration.html', {'errors': errors})


# TODO при необходимости заменить функции ниже на классы (декораторы будут исп по-другому и dispatch)

def reg_view(request):  # регистрация
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save(commit=True)

            user = User.objects.create_user(username=request.POST.get('login'), password=request.POST.get('password'),
                                            last_name=request.POST.get('fio'))

            #  user.first_name = request.POST.get('fio')
            user.save()
            return HttpResponseRedirect('/auth/')

    else:
        form = UserRegistrationForm()

    return render(request, 'registration.html', {'form': form})


def auth_view(request):  # авторизация
    errors = []
    if request.method == 'POST':
        form = UserAuthenticationForm(request.POST)
        print('check valid')

        if form.is_bound:
            print('form is valid', request.POST.get('login'), request.POST.get('password'))

            try:
                print('trying to get data')

                bd_data = CustomerModel.objects.get(login=request.POST.get('login'))

                print('получил бд', bd_data)

                if request.POST.get('password') == bd_data.password:
                    print('авторизация этого пользователя')

                    user = authenticate(username=request.POST.get('login'), password=request.POST.get('password'))
                    print('success - ', user)
                    login(request, user)
                    return HttpResponseRedirect('/home/')

                else:
                    errors.append('неправильный пароль')

            except CustomerModel.DoesNotExist:
                errors.append('неправильный логин')

    else:
        form = UserAuthenticationForm()

    # print(form.errors.as_data())
    print(errors)
    return render(request, 'authentication.html', {'form': form, 'errors': errors})


def add_transaction(request):
    print('add_open')
    data, usr_id = user_type(request)
    print(usr_id)
    acc_info = AccountModel.objects.filter(customerId_FK=int(usr_id.idCustomer))
    errors = []
    time_1 = datetime.datetime.now()

    if request.method == 'POST':
        print('request = POST')

        accountId_to = AccountModel.objects.get(idAccounts=int(request.POST.get('accountId_to')))
        accountId_from = AccountModel.objects.get(idAccounts=int(request.POST.get('accountId_from')))

        money = request.POST.get('money')
        currency = AccountModel.objects.get(idAccounts=int(request.POST.get('accountId_from'))).currency
        comments = request.POST.get('comments')

        data = {
            'accountId_to': accountId_to.idAccounts,
            'accountId_from': accountId_from.idAccounts,
            'money': money,
            'currency': currency,
            'comments': comments,
            'time_t': time_1
        }
        transaction = AddTransactionForm(data)

        if accountId_from.money < int(money):
            errors.append('недостаточно средств на счету')

        if transaction.is_valid() and not errors:
            transaction.save()
            # снятие с аккаунта_from
            account_from = accountId_from
            account_from.money = F('money') - money
            account_from.save()

            # пополнение аккаунта_to
            account_to = accountId_to
            account_to.money = F('money') + money
            account_to.save()

            return HttpResponseRedirect('/transactions/')

    else:
        transaction = AddTransactionForm()

    return render(request, 'transactions_add_1.html', {'form': transaction, 'acc': acc_info, 'errors': errors})
