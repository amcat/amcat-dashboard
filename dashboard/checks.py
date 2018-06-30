from django.core.checks import Error, register, Warning
import dashboard
import pathlib


# these paths will be checked for existence. Warnings are raised if any are missing.
PO_PATHS = [
    'locale/nl/LC_MESSAGES/django.po',
    'locale/nl/LC_MESSAGES/djangojs.po',
    'dashboard/locale/nl/LC_MESSAGES/django.po',
    'dashboard/locale/nl/LC_MESSAGES/djangojs.po'
]


@register()
def translations_check(app_configs, **kwargs):
    """ Checks if the given translation files are where they're expected to be. """
    errors = []
    root = pathlib.Path(dashboard.__file__).parents[1]

    for path in PO_PATHS:
        po_path = root / path
        mo_path = root / (path[:-3] + ".mo")

        if not po_path.is_file():
            errors.append(
                Warning(
                    'Translation sources are missing or outdated.',
                    hint="Translations went missing. This shouldn't happen.",
                    obj="'{!s}'".format(po_path),
                    id='dashboard.W001',
                )
            )

        if not mo_path.is_file() or mo_path.stat().st_mtime < po_path.stat().st_mtime:
            errors.append(
                Warning(
                    'Translation binaries are missing or outdated.',
                    hint='To solve this, run `manage.py compilemessages`',
                    obj="'{!s}'".format(po_path),
                    id='dashboard.W002',
                )
            )


    return errors

