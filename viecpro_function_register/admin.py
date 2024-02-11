from django.contrib import admin

from .models import ToplevelFunction, AlternativeFunctionName

admin.site.register(ToplevelFunction)
admin.site.register(AlternativeFunctionName)
