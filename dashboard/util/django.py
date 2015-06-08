from django.db import connection
from django.db.models import sql


def bulk_insert_returning_ids(new_objects):
    """bulk_insert() does not set ids as per Django ticket #19527. However, postgres does
    support this, so we implement this manually in this function."""
    new_objects = list(new_objects)

    if not new_objects:
        return None

    if connection.vendor == "postgresql":
        model = new_objects[0].__class__
        query = sql.InsertQuery(model)
        query.insert_values(model._meta.fields[1:], new_objects)
        raw_sql, params = query.sql_with_params()[0]
        returning = "RETURNING {pk.column} AS {pk.name}".format(pk=model._meta.pk)
        new_objects = list(model.objects.raw("%s %s" % (raw_sql, returning), params))
    else:
        # Do naive O(n) approach
        for new_obj in new_objects:
            new_obj.save()

    return new_objects