from test.common_helper import CommonDatabaseMock
from test.unit.web_interface.base import WebInterfaceTest


class DbMock(CommonDatabaseMock):

    @staticmethod
    def search_query_cache(offset=0, limit=0):  # pylint: disable=unused-argument
        return [('cache_id', 'search_title', ['rule_1', 'rule_2'])]

    @staticmethod
    def get_total_cached_query_count():
        return 1


class TestBrowseBinarySearchHistory(WebInterfaceTest):

    @classmethod
    def setup_class(cls, *_, **__):
        super().setup_class(db_mock=DbMock)

    def test_browse_binary_search_history(self):
        rv = self.test_client.get('/database/browse_binary_search_history')
        assert b'search_title' in rv.data
        assert b'rule_1' in rv.data
        assert b'cache_id' in rv.data
