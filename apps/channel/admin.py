from django.contrib import admin

from apps.channel.models import Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    fields = ('image', )
