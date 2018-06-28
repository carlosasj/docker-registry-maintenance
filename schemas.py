from schema import Schema, Optional, Or

_default = {
    Optional('num'): int,
    Optional('tags-like'): [str],
    Optional('keep-tags'): [str],
    Optional('keep-tags-like'): [str],
    Optional('delete-by-hours'): [str],
    Optional('keep-by-hours'): int,
    Optional('dry-run'): bool,
}

_default2 = _default.copy()
_default2['image'] = str

default_other_images_schema = Schema(_default, ignore_extra_keys=True)
image_to_delete_schema = Schema(_default2, ignore_extra_keys=True)

yaml_schema = Schema({
    Optional('delete_images'): [image_to_delete_schema],
    Optional('default_other_images'): default_other_images_schema,
    'global': {
        Optional('debug'): bool,
        Optional('dry-run'): bool,
        Optional('no-validate-ssl'): bool,
        Optional('digest-method'): Or('GET', 'HEAD'),
        'login': str,
        'host': str,
    }
}, ignore_extra_keys=True)
