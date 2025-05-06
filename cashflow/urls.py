from django.urls import path
from .views import (
    CashFlowListView,
    CashFlowCreateView,
    # CashFlowUpdateView,
    CashFlowDeleteView,
    get_subcategories,
    # DictionaryManageView
)
from cashflow.apps import CashflowConfig

app_name = CashflowConfig.name

urlpatterns = [
    # Главная страница со списком записей
    path('', CashFlowListView.as_view(), name='cashflow-list'),

    # CRUD операции для записей ДДС
    path('create/', CashFlowCreateView.as_view(), name='cashflow-create'),
    # path('<int:pk>/edit/', CashFlowUpdateView.as_view(), name='cashflow-update'),
    path('<int:pk>/delete/', CashFlowDeleteView.as_view(), name='cashflow-delete'),

    # API endpoint для динамической загрузки подкатегорий
    path('get-subcategories/<int:category_id>/', get_subcategories, name='get-subcategories'),

    # Управление справочниками
    # path('dictionaries/', DictionaryManageView.as_view(), name='dictionaries-manage'),

    # Дополнительные маршруты...
]