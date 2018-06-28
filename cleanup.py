import argparse
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import sys
import yaml
from schema import SchemaError
from schemas import yaml_schema
from registry import (Registry, get_auth_schemes, get_tags, get_tags_like,
                      get_newer_tags, natural_keys, CONST_KEEP_LAST_VERSIONS,
                      delete_tags, delete_tags_by_age)
from os.path import expandvars


def cast_bool(val):
    list_true = ['true', 't', 'yes', '1']
    list_false = ['false', 'f', 'no', '0']

    val = str(val).lower()

    if val in list_true:
        return True
    elif val in list_false:
        return False
    else:
        raise ValueError(
            '"{}" is not a valid value to cast as "bool"'.format(val))


yaml.add_constructor('!env', lambda _, node: expandvars(node.value))
yaml.add_constructor('!env_bool',
                     lambda _, node: cast_bool(expandvars(node.value)))
yaml.add_constructor('!env_int', lambda _, node: int(expandvars(node.value)))


def apply_delete(image_name, config, global_dry_run, registry):
    print("---------------------------------")
    print("Image: {0}".format(image_name))
    all_tags_list = registry.list_tags(image_name)

    if not all_tags_list:
        print("  no tags!")
        return

    keep_last_versions = config.get('num', CONST_KEEP_LAST_VERSIONS)
    tags_list = get_tags(all_tags_list,
                         image_name,
                         config.get('tags-like', []))

    # add tags to "tags_to_keep" list, if we have regexp "tags_to_keep"
    # entries or a number of hours for "keep_by_hours":
    keep_tags = []
    if config.get('keep-tags-like', []):
        keep_tags.extend(get_tags_like(config['keep-tags-like'], tags_list))
    if config.get('keep-by-hours', False):
        keep_tags.extend(get_newer_tags(registry, image_name,
                                        config['keep-by-hours'], tags_list))
    keep_tags = list(set(keep_tags))  # Eliminate duplicates

    tags_list_to_delete = (
        sorted(tags_list, key=natural_keys)[:-keep_last_versions])

    # A manifest might be shared between different tags. Explicitly add those
    # tags that we want to preserve to the keep_tags list, to prevent
    # any manifest they are using from being deleted.
    tags_list_to_keep = (
        [tag for tag in tags_list if tag not in tags_list_to_delete])
    keep_tags.extend(tags_list_to_keep)

    delete_tags(
        registry,
        image_name,
        global_dry_run or config.get('dry-run', False),
        tags_list_to_delete,
        keep_tags,
    )

    # delete tags by age in hours
    if config.get('delete-by-hours', False):
        keep_tags.extend(config.get('keep-tags', []))
        delete_tags_by_age(
            registry,
            image_name,
            global_dry_run or config.get('dry-run', False),
            config['delete-by-hours'],
            keep_tags,
        )


def main_loop(args, data):
    data_global = data['global']
    global_dry_run = data_global.get('dry-run', False)

    if data_global.get('no-validate-ssl', False):
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    registry = Registry.create(data_global['host'],
                               data_global['login'],
                               data_global.get('no-validate-ssl', False),
                               data_global.get('digest-method', 'HEAD'))

    registry.auth_schemes = get_auth_schemes(registry, '/v2/_catalog')
    image_list = registry.list_images()
    image_list = {image_name: False for image_name in image_list}

    delete_images_list = data.get('delete_images', [])
    if len(delete_images_list):
        for item in delete_images_list:
            if item['image'] in image_list:
                apply_delete(item['image'], item, global_dry_run, registry)
                image_list[item['image']] = True

    default_other_images = data.get('default_other_images', None)
    if default_other_images:
        other_images = (
            [name for name, executed in image_list.items() if not executed])
        if len(other_images):
            for item in other_images:
                apply_delete(item,
                             default_other_images,
                             global_dry_run,
                             registry)


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Delete tags from Docker registry based on a Config File",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("""
IMPORTANT: after removing the tags, run the garbage collector
           on your registry host:

   docker-compose -f [path_to_your_docker_compose_file] run \\
       registry bin/registry garbage-collect \\
       /etc/docker/registry/config.yml

or if you are not using docker-compose:

   docker run registry:2 bin/registry garbage-collect \\
       /etc/docker/registry/config.yml

for more detail on garbage collection read here:
   https://docs.docker.com/registry/garbage-collection/
                """))
    parser.add_argument(
        '-c', '--config',
        help="Config file",
        required=True,
        metavar="config-cleanup.yml")

    return parser.parse_args(args)


if __name__ == "__main__":
    args = parse_args()
    data = None
    with open(args.config) as f:
        data = yaml.load(f.read())

    try:
        yaml_schema.validate(data)
        main_loop(args, data)
    except SchemaError as exc:
        sys.exit(exc.code)
    except KeyboardInterrupt:
        print("Ctrl-C pressed, quitting")
        exit(1)
