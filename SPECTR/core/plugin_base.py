class Plugin:
    name = "Unnamed Plugin"
    version = "1.0.0"
    description = ""
    author = ""

    def on_load(self, overlay, event_bus, config, game=None, status=None):
        pass

    def on_unload(self):
        pass

    def on_event(self, event, data):
        pass
