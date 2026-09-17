class BlogDatabaseRouter:

    blog_models = {
        "subscriptionplan",
        "billinghistory",
    }

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.blog_models:
            return "blog"

        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.blog_models:
            return "blog"

        return "default"

    def allow_migrate(
        self,
        db,
        app_label,
        model_name=None,
        **hints
    ):
        if model_name in self.blog_models:
            return db == "blog"

        return db == "default"