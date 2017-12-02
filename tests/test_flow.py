# -*- coding: utf-8 -*-
"""Full flow tests (blockchain op to transport)

   Basic idea is to setup yo's different components but not follow the real blockchain

"""

import pytest
import json
import uuid
from yo.services import blockchain_follower
from yo.services import notification_sender
from yo.services import api_server
from yo import config
from yo.transports import base_transport


@pytest.fixture(autouse=True)
def add_mock_transport_type(monkeypatch):
    from yo.db import TRANSPORT_TYPES
    transport_types_set = set(TRANSPORT_TYPES)
    transport_types_set.add('mock')
    monkeypatch.setattr(api_server, 'TRANSPORT_TYPES', transport_types_set)


class MockApp:
    def __init__(self, db):
        self.db = db
        self.config = config.YoConfigManager(None)


class MockTransport(base_transport.BaseTransport):
    def __init__(self):
        self.received_by_user = {}

    def send_notification(self, to_subdata=None, to_username=None, notify_type=None, data=None):
        print((to_subdata, to_username, notify_type, data))
        self.received_by_user[to_username] = (to_subdata, notify_type, data)


# FIXME disabled while notification sending is reworked
async def vote_flow(sqlite_db):
    """Tests vote events get through to a transport
    """
    mock_vote_op = {'trx_id': str(uuid.uuid4()),
                    'op': ('vote', {'permlink': 'test-post',
                                    'author': 'testupvoted',
                                    'voter': 'testupvoter',
                                    'weight': 10000})}

    # boilerplate stuff
    yo_db = sqlite_db
    yo_app = MockApp(yo_db)
    sender = notification_sender.YoNotificationSender(db=yo_db, yo_app=yo_app)
    mock_tx = MockTransport()
    sender.configured_transports = {}
    sender.configured_transports['mock'] = mock_tx
    API = api_server.YoAPIServer()
    follower = blockchain_follower.YoBlockchainFollower(db=yo_db, yo_app=yo_app)

    # configure testupvoted and testupvoter users to use mock transport for votes
    transports_obj = {'mock': {'notification_types': ['vote'], 'sub_data': ''}}
    await API.api_set_transports(username='testupvoted', transports=transports_obj, context=dict(yo_db=sqlite_db))
    await API.api_set_transports(username='testupvoter', transports=transports_obj, context=dict(yo_db=sqlite_db))

    # handle the mock vote op
    await follower.notify(mock_vote_op)

    # since we don't run stuff in the background in test suite, manually
    # invoke the notification sender
    await sender.api_trigger_notifications()

    print(mock_tx.received_by_user.items())

    # test it got through to our mock transport for testupvoted only
    assert 'testupvoted' in mock_tx.received_by_user.keys()
    assert not ('testupvoter' in mock_tx.received_by_user.keys())


@pytest.mark.skip(reason='Will currently fail, should be fixed in other branch')
@pytest.mark.asyncio
async def test_follow_flow(sqlite_db):
    """Tests follow events get through to a transport
    """
    mock_follow_op = {'trx_id': str(uuid.uuid4()),
                      'op': ('custom_json', {'required_auths': (),
                                             'required_posting_auths': 'testfollower',
                                             'id': 'follow',
                                             'json': ('follow', {'follower ': 'testfollower',
                                                                 'following': 'testfollowed',
                                                                 'what': ('blog')})
                                             })}

    # boilerplate stuff
    yo_db = sqlite_db
    yo_app = MockApp(yo_db)
    sender = notification_sender.YoNotificationSender(db=yo_db, yo_app=yo_app)
    mock_tx = MockTransport()
    sender.configured_transports = {}
    sender.configured_transports['mock'] = mock_tx
    API = api_server.YoAPIServer()
    follower = blockchain_follower.YoBlockchainFollower(db=yo_db, yo_app=yo_app)

    # configure testupvoted and testupvoter users to use mock transport for follows
    transports_obj = {'mock': {'notification_types': ['follow'], 'sub_data': ''}}
    await API.api_set_transports(username='testfollower', transports=transports_obj, context=dict(yo_db=sqlite_db))
    await API.api_set_transports(username='testfollowed', transports=transports_obj, context=dict(yo_db=sqlite_db))

    # handle the mock follow op
    await follower.notify(mock_follow_op)

    # since we don't run stuff in the background in test suite, manually
    # invoke the notification sender
    await sender.api_trigger_notifications()

    print(mock_tx.received_by_user.items())

    # test it got through to our mock transport for testupvoted only
    assert 'testfollowed' in mock_tx.received_by_user.keys()
    assert not ('testfollower' in mock_tx.received_by_user.keys())
