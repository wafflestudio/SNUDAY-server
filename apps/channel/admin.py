from django.contrib import admin

from apps.channel.models import Image, Channel, UserChannel, ManagerChannel


class ManagerInline(admin.TabularInline):
    model = ManagerChannel
    extra = 2  # how many rows to show


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    fields = ('image',)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    model = Channel
    inlines = [
        ManagerInline
    ]


@admin.register(UserChannel)
class UserChannelAdmin(admin.ModelAdmin):
    model = UserChannel
    list_display = ('channel', 'user',)


@admin.register(ManagerChannel)
class UserChannelAdmin(admin.ModelAdmin):
    model = ManagerChannel
    list_display = ('channel', 'user',)
