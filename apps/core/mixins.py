class SerializerChoiceMixin:
    def get_serializer_class(self):
        if not hasattr(self, "serializer_classes"):
            raise ValueError("to use mixin, you should have serailzer_classes")
        if self.action in self.serializer_classes:
            return self.serializer_classes[self.action]
        else:
            return self.serializer_classes["default"]
