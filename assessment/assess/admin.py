from django.contrib import admin
from django.db.models import TextField
from django import forms
from django.utils.formats import localize
from assessment.assess import models


class InlineTextFieldMixin:
    formfield_overrides = {
        TextField: {'widget': forms.Textarea(attrs={'rows': 2, 'style': 'width:80%'})},
    }


class AssessmentSubjectInline(InlineTextFieldMixin, admin.TabularInline):
    model = models.get_assessment_subject_model()
    verbose_name_plural = "Assessment Subject"


class MetricScoreTabularInline(InlineTextFieldMixin, admin.TabularInline):
    model = models.MetricScore
    fields = ('metric', 'applicable', 'score', 'comments',)
    extra = 1


@admin.register(models.AssessmentRecord)
class AssessmentRecordAdmin(admin.ModelAdmin):
    list_display = ('subject', 'category', 'created', 'assessor', 'assessment_type', 'status')
    list_editable = ('status',)
    list_filter = ('status', 'assessment_type', 'category__activity', 'category__topic', 'assessor', )
    date_hierarchy = 'created'
    exclude = ('group_id', 'last_edited_by', 'created', 'last_edited')
    editable_fields = ('category', 'assessment_type', 'status', )
    readonly_fields = ('assessor', 'created', 'is_in_assessment_group', 'last_edited_by', 'last_edited')
    autocomplete_fields = ('category', )
    fieldsets = (
        (None, {
            'fields': tuple(editable_fields),
        }),
        ('About', {
            'classes': ('collapse',),
            'fields':  (('assessor', 'created'), ('last_edited_by', 'last_edited'), 'is_in_assessment_group'),
        }),
    )
    inlines = (AssessmentSubjectInline, MetricScoreTabularInline, )

    def save_model(self, request, obj, form, change):
        # record who made this edit
        obj.last_edited_by = request.user
        if not change:
            obj.assessor = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.AssessmentGroup)
class AssessmentSetAdmin(admin.ModelAdmin):
    list_display = ('subject', 'root', 'created', 'assessor', 'assessment_type', 'status')
    list_editable = ('status',)
    list_filter = ('status', 'assessment_type', 'activity', 'topic', 'assessor', )
    date_hierarchy = 'created'
    exclude = ('created',)
    editable_fields = ('activity', 'topic', 'assessment_type', 'status', )
    readonly_fields = ('subject', 'assessor', 'created', 'last_edited_by', 'localized_last_edited')
    fieldsets = (
        (None, {
            'fields': tuple(editable_fields),
        }),
        ('About', {
            'classes': ('collapse',),
            'fields':  (('assessor', 'created'), ('last_edited_by', 'localized_last_edited'), ),
        }),
    )

    def save_model(self, request, obj, form, change):
        # record who made this edit
        if not change:
            obj.assessor = request.user
        super().save_model(request, obj, form, change)

    def localized_last_edited(self, obj):
        """ Return the edit date of most recently edited Assessment in this group """
        return localize(obj.last_edited_assessment.last_edited)


class SupportingDocTabularInline(InlineTextFieldMixin, admin.TabularInline):
    model = models.SupportingDoc
    fields = ('document_type', 'document_location', 'description', 'url', 'file')
    extra = 1

    def has_attachment(self, instance):
        return bool(instance.file)
    has_attachment.short_description = 'Has Attachment?'


@admin.register(models.MetricScore)
class MetricScoreAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'metric', 'applicable', 'score', 'comments', )
    list_filter = ('applicable', 'metric', 'assessment__category__activity', 'assessment__category__topic', )
    fields = ('metric', 'assessment', 'applicable', 'score', 'comments', )
    autocomplete_fields = ('metric', )
    date_hierarchy = 'assessment__created'
    inlines = (SupportingDocTabularInline, )

    def save_model(self, request, obj, form, change):
        obj.clean()
        super().save_model(request, obj, form, change)
