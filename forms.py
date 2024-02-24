from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from sapp_store.models import Category, Material
from sapp.models import SM


class FiltersForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects,
        required=False,
        empty_label="ГОСТ"
    )
    material = forms.ModelChoiceField(
        queryset=Material.objects,
        required=False,
        empty_label="Материал"
    )
    coverage = forms.ChoiceField(
        choices=(("", "Покрытие"),) + SM.iter_as_choices("C1", "c2"),
        # widget=forms.Select(attrs={"placeholder": "Покрытие"}),
        required=False,
    )
    sorting = forms.ChoiceField(
        choices=(("", "Сортировка"),) + SM.iter_as_choices("Name", "Price"),
        # widget=forms.Select(attrs={"placeholder": "Сортировка"}),
        required=False,
    )
    search = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Поиск"}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        helper = FormHelper()
        helper.form_class = "filter-form"
        self.helper = helper
        helper.layout = Layout(
            Row(
                Column("category", css_class="col col-lg-2 mx-lg-auto"),
                Column("material", css_class="col col-lg-2 mx-lg-auto"),
                Column("coverage", css_class="col col-lg-2 mx-lg-auto"),
                Column("sorting", css_class="col col-lg-2 mx-lg-auto"),
                Column("search", css_class="col col-lg-2 mx-lg-auto"),
            )
        )
    
    def get_cleaned_filters(self):
        filters = {}
        data = self.cleaned_data
        if data["category"]:
            filters["category"] = data["category"]
        if data["material"]:
            filters["material"] = data["material"]
        if data["search"]:
            filters["name__icontains"] = data["search"]
        return filters
        

    
