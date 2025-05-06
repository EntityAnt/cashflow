from django.contrib import admin
from django.contrib.auth.models import User, Group  # Стандартные модели Django
from .models import (
    Status,
    OperationType,
    Category,
    SubCategory,
    CashFlow
)

# Отменяем стандартную регистрацию User
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    fields = ('name',)
    ordering = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_filter = ('operation_type',)
    search_fields = ('name',)
    ordering = ('operation_type', 'name')
    inlines = [SubCategoryInline]


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'operation_type')
    list_filter = ('category', 'category__operation_type')
    search_fields = ('name', 'category__name')
    ordering = ('category', 'name')

    @admin.display(description='Тип операции')
    def operation_type(self, obj):
        return obj.category.operation_type


@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'status',
        'operation_type',
        'category',
        'subcategory',
        'amount',
        'comment_short'
    )
    list_filter = (
        'status',
        'operation_type',
        'category',
        'subcategory',
        'date'
    )
    search_fields = (
        'comment',
        'subcategory__name',
        'category__name'
    )
    date_hierarchy = 'date'
    ordering = ('-date',)
    fieldsets = (
        (None, {
            'fields': (
                'date',
                'status',
                'operation_type',
                'category',
                'subcategory',
                'amount'
            )
        }),
        ('Дополнительно', {
            'fields': ('comment',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Комментарий')
    def comment_short(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment


# Если нужно добавить Group в админку с кастомными настройками
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)