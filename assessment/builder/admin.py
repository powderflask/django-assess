from django.contrib import admin
from django.utils.text import slugify
from django.db.models import TextField
from django import forms

from ordered_model.admin import OrderedModelAdmin, OrderedTabularInline, OrderedInlineModelAdminMixin
from . import models


class TextFieldMixin:
    formfield_overrides = {
        TextField : {'widget' : forms.Textarea(attrs={'rows' : 4, 'style' : 'width:90%'})},
    }

class InlineTextFieldMixin:
    formfield_overrides = {
        TextField : {'widget' : forms.Textarea(attrs={'rows' : 2, 'style' : 'width:80%'})},
    }


@admin.register(models.Activity)
class ActivityAdmin(TextFieldMixin, OrderedModelAdmin):
    list_display = ('label', 'slug', 'status', 'move_up_down_links')
    list_editable = ('status',)
    prepopulated_fields = {"slug" : ("label",)}


@admin.register(models.Topic)
class TopicAdmin(TextFieldMixin, OrderedModelAdmin):
    list_display = ('label', 'slug', 'status', 'move_up_down_links')
    list_editable = ('status',)
    prepopulated_fields = {"slug" : ("label",)}


class ReferenceDocumentTabularInline(InlineTextFieldMixin, OrderedTabularInline):
    model = models.ReferenceDocument
    fields = ('label', 'description', 'url', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)
    extra = 1


class AssessmentQuestionTabularInline(InlineTextFieldMixin, OrderedTabularInline):
    model = models.AssessmentQuestion
    verbose_name_plural = "Qeustions"
    fields = ('label', 'description', 'status', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)
    extra = 1


@admin.register(models.AssessmentCategory)
class AssessmentCategoryAdmin(TextFieldMixin, OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = ('label', 'activity', 'topic', 'num_questions', 'status')
    list_editable = ('status',)
    list_filter = ('status', 'activity', 'topic', )
    ordering = ('topic__order', 'activity__order',)
    prepopulated_fields = {"slug" : ("label", )}
    search_fields = ('label', 'activity__label', 'topic__label', )
    inlines = (AssessmentQuestionTabularInline, ReferenceDocumentTabularInline )

    def num_questions(self, cat):
        return cat.question_count()
    num_questions.short_description = '# Questions'

    def save_model(self, request, obj, form, change):
        # don't overwrite manually set label or slug
        if form.cleaned_data['label'] == "":
            obj.label = models.AssessmentCategory.get_default_label(form.cleaned_data['activity'], form.cleaned_data['topic'])
        if form.cleaned_data['slug'] == "":
            obj.slug = slugify(obj.label)
        super().save_model(request, obj, form, change)


class AssessmentMetricTabularInline(InlineTextFieldMixin, OrderedTabularInline):
    model = models.AssessmentMetric
    verbose_name_plural = 'Metrics'
    fields = ('label', 'description', 'choices', 'status', 'order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)
    extra = 1


@admin.register(models.ReferenceDocument)
class ReferenceDocumentAdmin(TextFieldMixin, OrderedInlineModelAdminMixin, OrderedModelAdmin):
    list_display = ('label', 'category', 'url', 'move_up_down_links')
    list_filter = ('category__activity', 'category__topic', )


@admin.register(models.AssessmentQuestion)
class AssessmentQuestionAdmin(TextFieldMixin, OrderedInlineModelAdminMixin, OrderedModelAdmin):
    list_display = ('label', 'category', 'num_metrics', 'status', 'move_up_down_links')
    list_editable = ('status',)
    list_filter = ('status', 'category__activity', 'category__topic', )
    ordering=('category__activity__order', 'category__topic__order', )
    autocomplete_fields = ('category', )
    search_fields = ('label', 'category__label', )
    inlines = (AssessmentMetricTabularInline, )

    def num_metrics(self, cat):
        return cat.metric_count()
    num_metrics.short_description = '# Metrics'


@admin.register(models.AssessmentMetric)
class AssessmentMetricAdmin(TextFieldMixin, OrderedModelAdmin):
    list_display = ('label', 'question', 'choices', 'status', 'move_up_down_links')
    list_editable = ('status',)
    list_filter = ('status', 'question__category__activity', 'question__category__topic', )
    autocomplete_fields = ('question', )
    search_fields = ('label', 'question__label', 'question__category__label' )


@admin.register(models.MetricChoicesType)
class MetricChoicesTypeAdmin(admin.ModelAdmin):
    list_display = ('label',  'choice_map')
