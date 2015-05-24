from mock import Mock, patch
from twisted.trial.unittest import TestCase

from apns.errorresponse import ErrorResponse
from apns.gatewayclient import (
    GatewayClient,
    GatewayClientFactory,
    GatewayClientNotSetError
)


MODULE = 'apns.gatewayclient.'


class GatewayClientTestCase(TestCase):

    def test_connection_made(self):
        client = GatewayClient()
        client.factory = Mock(hostname='opera.com', port=80)

        client.connectionMade()

        client.factory.connectionMade.assert_called_once_with(client)

    def test_send(self):
        client = GatewayClient()
        client.transport = Mock()
        notification = Mock()

        client.send(notification)

        client.transport.write.assert_called_once_with(
            notification.to_binary_string())

    @patch(MODULE + 'ErrorResponse.from_binary_string')
    def test_data_received(self, from_binary_string_mock):
        client = GatewayClient()
        client.factory = Mock()
        data = Mock()

        client.dataReceived(data)

        from_binary_string_mock.assert_called_once_with(data)
        client.factory.errorReceived.assert_called_once()
        self.assertIsInstance(client.factory.errorReceived.call_args[0][0],
                              ErrorResponse)


class GatewayClientFactoryTestCase(TestCase):
    CLASS = MODULE + 'GatewayClientFactory.'

    @patch(MODULE + 'ssl.PrivateCertificate.loadPEM', Mock())
    @patch(MODULE + 'GatewayClientFactory.ENDPOINTS', {'pub': ('foo', 'bar')})
    def setUp(self):
        self.factory = GatewayClientFactory('pub', __file__)

    def test_connection_made(self):
        client = Mock()

        self.factory.connectionMade(client)

        self.assertEqual(self.factory.client, client)

    @patch(CLASS + '_onConnectionLost')
    @patch(MODULE + 'ReconnectingClientFactory.clientConnectionFailed')
    def test_client_connection_failed(self, client_connection_failed_mock,
                                      on_connection_lost_mock):
        connector = Mock()
        reason = Mock()
        self.factory.clientConnectionFailed(connector, reason)

        on_connection_lost_mock.assert_called_once_with()
        client_connection_failed_mock.assert_called_once_with(self.factory,
                                                              connector,
                                                              reason)

    @patch(CLASS + '_onConnectionLost')
    @patch(MODULE + 'ReconnectingClientFactory.clientConnectionLost')
    def test_client_connection_lost(self, client_connection_lost_mock,
                                    on_connection_lost_mock):
        connector = Mock()
        reason = Mock()
        self.factory.clientConnectionLost(connector, reason)

        on_connection_lost_mock.assert_called_once_with()
        client_connection_lost_mock.assert_called_once_with(self.factory,
                                                            connector,
                                                            reason)

    def test_connected(self):
        self.assertFalse(self.factory.connected)
        self.factory.client = Mock()
        self.assertTrue(self.factory.connected)
        self.factory.client = None
        self.assertFalse(self.factory.connected)

    def test_send_client_not_set(self):
        with self.assertRaises(GatewayClientNotSetError):
            self.factory.send(Mock())

    def test_send_client_set(self):
        notification = Mock()
        client = Mock()
        self.factory.client = client

        self.factory.send(notification)

        self.factory.client.send.assert_called_once_with(notification)

    def test_on_connection_lost(self):
        self.factory.client = Mock()

        self.factory._onConnectionLost()

        self.assertIsNone(self.factory.client)

    def test_error_received(self):
        self.factory.onErrorReceived = Mock()
        error = Mock()

        self.factory.errorReceived(error)

        self.factory.onErrorReceived.assert_called_once_with(error)

    def test_error_received_no_callback(self):
        self.factory.onErrorReceived = None
        error = Mock()

        self.factory.errorReceived(error)
