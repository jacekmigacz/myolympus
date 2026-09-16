# Nested Namespace Extraction in Flask Config

## Problem Statement

Flask's `Config.get_namespace()` method extracts a subset of configuration keys that share a common prefix and returns them as a flat dictionary. However, Flask's own `Config.from_prefixed_env()` already uses double underscores (`__`) to represent nested dictionary structures when **loading** configuration from environment variables.

Your task is to extend `get_namespace()` to support **outputting** nested dictionaries using the same `__` convention, so that the loading and extraction patterns are symmetrical.

## Requirements

Add a `nested` parameter to `Config.get_namespace()`:

```python
def get_namespace(
    self,
    namespace: str,
    lowercase: bool = True,
    trim_namespace: bool = True,
    nested: bool = False,
) -> dict[str, t.Any]:
```

### Behavior when `nested=False` (default)

Existing behavior must be preserved exactly. No changes to the current output.

### Behavior when `nested=True`

1. The namespace prefix is always trimmed (the `trim_namespace` parameter is ignored when `nested=True`).

2. After trimming the namespace prefix, keys containing `__` (double underscore) are split into segments. Each segment becomes a level in a nested dictionary.

3. If `lowercase=True`, all key segments at every nesting level are lowercased.

4. If a key has no `__` separator, it is placed at the top level of the result (same as flat mode with `trim_namespace=True`).

5. **Conflict resolution:** If a key exists both as a flat value and as a namespace prefix for nested keys, the nested dictionary takes precedence and the flat value is discarded.

6. Keys are processed in sorted order to ensure deterministic output.

## Examples

```python
from flask import Flask

app = Flask(__name__)

app.config.update({
    'DATABASE_HOST': 'localhost',
    'DATABASE_PORT': 5432,
    'DATABASE_OPTIONS__POOL_SIZE': 5,
    'DATABASE_OPTIONS__TIMEOUT': 30,
    'DATABASE_OPTIONS__SSL__ENABLED': True,
    'DATABASE_OPTIONS__SSL__CERT': '/path/to/cert',
})

# Flat mode (default, unchanged behavior):
app.config.get_namespace('DATABASE_')
# {'host': 'localhost', 'port': 5432,
#  'options__pool_size': 5, 'options__timeout': 30,
#  'options__ssl__enabled': True, 'options__ssl__cert': '/path/to/cert'}

# Nested mode:
app.config.get_namespace('DATABASE_', nested=True)
# {
#     'host': 'localhost',
#     'port': 5432,
#     'options': {
#         'pool_size': 5,
#         'timeout': 30,
#         'ssl': {
#             'enabled': True,
#             'cert': '/path/to/cert',
#         }
#     }
# }

# Nested mode without lowercase:
app.config.get_namespace('DATABASE_', lowercase=False, nested=True)
# {
#     'HOST': 'localhost',
#     'PORT': 5432,
#     'OPTIONS': {
#         'POOL_SIZE': 5,
#         'TIMEOUT': 30,
#         'SSL': {
#             'ENABLED': True,
#             'CERT': '/path/to/cert',
#         }
#     }
# }
```

### Conflict example

```python
app.config.update({
    'CACHE_BACKEND': 'redis',
    'CACHE_BACKEND__HOST': 'localhost',
    'CACHE_BACKEND__PORT': 6379,
})

app.config.get_namespace('CACHE_', nested=True)
# {'backend': {'host': 'localhost', 'port': 6379}}
# Note: the flat value 'redis' for CACHE_BACKEND is discarded
# because CACHE_BACKEND also serves as a namespace prefix.
```

## Constraints

- You may only modify `src/flask/config.py`.
- The method signature must remain backward-compatible (all new parameters must have defaults that preserve existing behavior).
- Do not add any new dependencies.

## File to modify

`src/flask/config.py` — specifically the `Config.get_namespace()` method.
