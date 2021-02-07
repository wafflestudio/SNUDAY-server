from django.contrib import admin

from apps.channel.models import Image, Channel, UserChannel
from apps.user.models import User


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    fields = ('image', )


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    model = Channel


@admin.register(UserChannel)
class UserChannelAdmin(admin.ModelAdmin):
    model = UserChannel