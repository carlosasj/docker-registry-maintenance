# docker-registry-maintenance

This is the repository to [carlosaschjr/docker-registry-maintenance](https://hub.docker.com/r/carlosaschjr/docker-registry-maintenance/) image.

This image is heavily based on [andrey-pohilko's work](https://github.com/andrey-pohilko/registry-cli)

## Motivation

I had seted up a docker registry to my company that receive images from repositories integrated with a CI/CD solution, so it has a lot of images created every week, and since we store them on S3 our bill was growing a bit quicker than we liked.

We searched for a solution, and the best one was [andrey-pohilko/registry-cli](https://github.com/andrey-pohilko/registry-cli), but it just run one "batch delete" at time, and the authentication overhead was huge.

This script aims to provide a simple yaml configuration to declare how long each image tag would exist on the registry, with a bit less overhead with the authentication.

## Environment Variables

- `SCHEDULE`: a schedule expression to run the script, according to [this doc](https://godoc.org/github.com/robfig/cron#hdr-CRON_Expression_Format) (if not set the script will run just once, then the container will be stopped)
- `CONFIG_FILE`: the path inside the container that you did mount the yaml config file
- `REGISTRY_USER`: a username to login on the registry
- `REGISTRY_PASSWORD`: the password to login on the registry

## Configuration (config-cleanup.yml)

### `global`

Inside the `global` (required) key you can describe how to connect to your registry and other things.

#### `global.login`

`String`, required

Your username and password to log into your Docker Registry, with the format `'username:password'`. I recommend keep this as `!env $REGISTRY_USER:$REGISTRY_PASSWORD` and set the `REGISTRY_USER` and `REGISTRY_PASSWORD` environment variables with a docker secret or other secure way.

#### `global.host`

`String`, required

Your registry URL, with the format `protocol://domain` (e.g. `https://my-registry.domain.com`).

#### `global.dry-run`

`Boolean`, default `false`

In case you want to know which tags are going to be deleted, without deleting them.

#### `global.no-validate-ssl`

`Boolean`, default `false`

Avoid errors about invalid or self-signed SSL certificates

#### `global.digest-method`

`String`, default `'HEAD'`

Use `HEAD` for standard docker registry or `GET` for NEXUS

#### `global.debug`

`Boolean`, default `false`

Print debug messages (ironically, may cause some errors).

### `default_other_images`

Inside the `default_other_images` (optinoal) you can describe the behavior to all images that are not declared inside the key `delete_images`.

#### `default_other_images.num`

`Integer`, default `10`

Set the number of tags to keep.

#### `default_other_images.tags-like`

`List[String]`

Specify tags to be deleted using a list of regexp based names.

#### `default_other_images.keep-tags`

`List[String]`

Specify tags that **shoud not** be deleted (each item will be treated "as is").

#### `default_other_images.keep-tags-like`

`List[String]`

Specify tags that **shoud not** be deleted (each item will be treated as a regex).

#### `default_other_images.delete-by-hours`

`Integer`

Delete all tags by age in hours for the particular image. Note that deleting by age will not prevent more recent tags from being deleted if there are more than `default_other_images.num` tags. (You probably would prefer the key `keep-by-hours` below).

#### `default_other_images.keep-by-hours`

`Integer`

Delete all tags by age in hours for the particular image, but keep images within less than this value, even if there are more than `default_other_images.num` tags.

#### `default_other_images.dry-run`

`Boolean`, default `false`

In case you want to know which tags are going to be deleted, without deleting them.

### `delete_images`

Inside the `delete_images` (optinoal) you can describe a list with behaviors/rules to some images. Each item can have the same keys as `default_other_images` (`num`, `dry-run`...), but also **must** contain a key `image`.

#### `delete_images.*.image`

`String`, required

The name of the image that the rest of the rule applies.

## IMPORTANT

After removing the tags, run the garbage collector on your registry host:

```bash
   docker-compose -f [path_to_your_docker_compose_file] run \
       registry bin/registry garbage-collect \
       /etc/docker/registry/config.yml
```

or if you are not using docker-compose:

```bash
   docker run registry:2 bin/registry garbage-collect \
       /etc/docker/registry/config.yml
```

for more detail on garbage collection [read here](https://docs.docker.com/registry/garbage-collection/).

## Environment Variables inside config-cleanup.yml file

You can indicate special "parsers" on the `config-cleanup.yml` file so it will try to grab the value from an Environment Variablen and maybe cast to another type. Use:

- `!env $VARIABLE`: grab `$VARIABLE` value as string
- `!env_bool $VARIABLE`: grab `$VARIABLE` value as boolean (case insensitive) *
- `!env_int $VARIABLE`: grab `$VARIABLE` value as integer

`*`: use `true`, `t`, `yes`, `1` (case insensitive) to describe Truthy values; use `false`, `f`, `no`, `0` (case insensitive) to describe Falsy values.

Please, don't try to mix "constant" values with environment variables inside the same key.

#### Examples:

```yaml
# Your environment:
#   REGISTRY_USER=foo
#   REGISTRY_PASSWORD=bar
#   DRY_RUN=0
#   KEEP_NUM=42

global:
  ...
  login: !env $REGISTRY_USER:$REGISTRY_PASSWORD
  dry-run: !env_bool $DRY_RUN
  num: !env_int $KEEP_NUM

# The key `global.login` will evaluate to 'foo:bar'
# The key `global.dry-run` will evaluate to false
# The key `global.num` will evaluate to 42
```
