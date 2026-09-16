"""Tests for Config.get_namespace() with nested parameter."""

import pytest
from flask import Flask


@pytest.fixture
def app():
    return Flask(__name__)


class TestGetNamespaceFlat:
    """Verify existing behavior is not broken."""

    def test_basic_flat(self, app):
        app.config['IMAGE_STORE_TYPE'] = 'fs'
        app.config['IMAGE_STORE_PATH'] = '/var/app/images'
        app.config['IMAGE_STORE_BASE_URL'] = 'http://img.example.com'
        result = app.config.get_namespace('IMAGE_STORE_')
        assert result == {
            'type': 'fs',
            'path': '/var/app/images',
            'base_url': 'http://img.example.com',
        }

    def test_flat_no_lowercase(self, app):
        app.config['DB_HOST'] = 'localhost'
        app.config['DB_PORT'] = 5432
        result = app.config.get_namespace('DB_', lowercase=False)
        assert result == {'HOST': 'localhost', 'PORT': 5432}

    def test_flat_no_trim(self, app):
        app.config['DB_HOST'] = 'localhost'
        result = app.config.get_namespace('DB_', trim_namespace=False)
        assert result == {'db_host': 'localhost'}

    def test_flat_default_nested_false(self, app):
        app.config['X_A__B'] = 1
        result = app.config.get_namespace('X_')
        assert result == {'a__b': 1}


class TestGetNamespaceNested:
    """Test new nested=True functionality."""

    def test_simple_nested(self, app):
        app.config['DATABASE_HOST'] = 'localhost'
        app.config['DATABASE_PORT'] = 5432
        result = app.config.get_namespace('DATABASE_', nested=True)
        assert result == {'host': 'localhost', 'port': 5432}

    def test_one_level_nesting(self, app):
        app.config['DB_OPTIONS__POOL_SIZE'] = 5
        app.config['DB_OPTIONS__TIMEOUT'] = 30
        result = app.config.get_namespace('DB_', nested=True)
        assert result == {
            'options': {
                'pool_size': 5,
                'timeout': 30,
            }
        }

    def test_deep_nesting(self, app):
        app.config['S_A__B__C__D'] = 'deep'
        result = app.config.get_namespace('S_', nested=True)
        assert result == {'a': {'b': {'c': {'d': 'deep'}}}}

    def test_mixed_flat_and_nested(self, app):
        app.config['DATABASE_HOST'] = 'localhost'
        app.config['DATABASE_PORT'] = 5432
        app.config['DATABASE_OPTIONS__POOL_SIZE'] = 5
        app.config['DATABASE_OPTIONS__TIMEOUT'] = 30
        app.config['DATABASE_OPTIONS__SSL__ENABLED'] = True
        app.config['DATABASE_OPTIONS__SSL__CERT'] = '/path/to/cert'
        result = app.config.get_namespace('DATABASE_', nested=True)
        assert result == {
            'host': 'localhost',
            'port': 5432,
            'options': {
                'pool_size': 5,
                'timeout': 30,
                'ssl': {
                    'enabled': True,
                    'cert': '/path/to/cert',
                },
            },
        }

    def test_nested_no_lowercase(self, app):
        app.config['DB_OPTIONS__POOL_SIZE'] = 5
        app.config['DB_HOST'] = 'localhost'
        result = app.config.get_namespace('DB_', lowercase=False, nested=True)
        assert result == {
            'HOST': 'localhost',
            'OPTIONS': {
                'POOL_SIZE': 5,
            },
        }

    def test_nested_ignores_trim_namespace(self, app):
        app.config['DB_HOST'] = 'localhost'
        result_trimmed = app.config.get_namespace(
            'DB_', trim_namespace=True, nested=True
        )
        result_not_trimmed = app.config.get_namespace(
            'DB_', trim_namespace=False, nested=True
        )
        assert result_trimmed == result_not_trimmed == {'host': 'localhost'}

    def test_conflict_nested_wins(self, app):
        app.config['CACHE_BACKEND'] = 'redis'
        app.config['CACHE_BACKEND__HOST'] = 'localhost'
        app.config['CACHE_BACKEND__PORT'] = 6379
        result = app.config.get_namespace('CACHE_', nested=True)
        assert result == {
            'backend': {
                'host': 'localhost',
                'port': 6379,
            }
        }

    def test_conflict_flat_value_discarded(self, app):
        app.config['X_A'] = 'flat_value'
        app.config['X_A__B'] = 'nested_value'
        result = app.config.get_namespace('X_', nested=True)
        assert 'a' in result
        assert isinstance(result['a'], dict)
        assert result['a']['b'] == 'nested_value'

    def test_no_matching_keys(self, app):
        app.config['OTHER_KEY'] = 'value'
        result = app.config.get_namespace('DB_', nested=True)
        assert result == {}

    def test_single_key(self, app):
        app.config['APP_DEBUG'] = True
        result = app.config.get_namespace('APP_', nested=True)
        assert result == {'debug': True}

    def test_deterministic_order(self, app):
        app.config['NS_Z'] = 3
        app.config['NS_A'] = 1
        app.config['NS_M'] = 2
        result = app.config.get_namespace('NS_', nested=True)
        assert result == {'a': 1, 'm': 2, 'z': 3}

    def test_non_string_values_preserved(self, app):
        app.config['T_INT'] = 42
        app.config['T_FLOAT'] = 3.14
        app.config['T_BOOL'] = True
        app.config['T_NONE'] = None
        app.config['T_LIST'] = [1, 2, 3]
        app.config['T_DICT'] = {'a': 1}
        result = app.config.get_namespace('T_', nested=True)
        assert result == {
            'int': 42,
            'float': 3.14,
            'bool': True,
            'none': None,
            'list': [1, 2, 3],
            'dict': {'a': 1},
        }

    def test_nested_intermediate_creation(self, app):
        app.config['S_A__X'] = 1
        app.config['S_B__Y'] = 2
        result = app.config.get_namespace('S_', nested=True)
        assert result == {'a': {'x': 1}, 'b': {'y': 2}}

    def test_only_uppercase_source_keys(self, app):
        app.config['db_host'] = 'should_not_appear'
        app.config['DB_HOST'] = 'localhost'
        result = app.config.get_namespace('DB_', nested=True)
        assert result == {'host': 'localhost'}


class TestGetNamespaceSignature:
    """Verify backward compatibility of the method signature."""

    def test_default_params(self, app):
        app.config['X_KEY'] = 'val'
        result = app.config.get_namespace('X_')
        assert result == {'key': 'val'}

    def test_keyword_only_nested(self, app):
        app.config['X_KEY'] = 'val'
        result = app.config.get_namespace('X_', nested=False)
        assert result == {'key': 'val'}
