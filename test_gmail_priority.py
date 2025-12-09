import unittest
from unittest.mock import MagicMock
from gmail_helper import GmailHelper

class TestGmailSearch(unittest.TestCase):
    def setUp(self):
        self.mock_service = MagicMock()
        self.helper = GmailHelper(MagicMock())
        self.helper.service = self.mock_service

    def test_search_prioritizes_subject(self):
        order_id = "12345"
        
        # Mock Search List Result (2 messages)
        self.mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg_summary'}, {'id': 'msg_target'}]
        }
        
        # Mock Get Message Details
        def get_message_side_effect(userId, id):
            if id == 'msg_summary':
                return {
                    'id': 'msg_summary',
                    'snippet': 'Summary of orders...',
                    'payload': {
                        'headers': [{'name': 'Subject', 'value': 'Weekly Report'}],
                        'body': {'data': ''} # Base64 ignored for this test
                    }
                }
            elif id == 'msg_target':
                return {
                    'id': 'msg_target',
                    'snippet': 'Booking Confirmed...',
                    'payload': {
                        'headers': [{'name': 'Subject', 'value': f'Booking {order_id} Confirmed'}],
                        'body': {'data': ''}
                    }
                }
            return None

        # Chain the mock for .get().execute()
        # This is tricky with chained mocks. Let's start simple.
        mock_messages_resource = self.mock_service.users().messages()
        mock_messages_resource.list.return_value.execute.return_value = {
            'messages': [{'id': 'msg_summary'}, {'id': 'msg_target'}]
        }
        
        # We need to mock the .get(id=...).execute() call which happens inside the loop
        # Since it's called with different arguments, we use side_effect on the execute method?
        # No, the arguments are passed to .get(), not .execute().
        # We need to mock the return value of .get() to be an object whose .execute() returns different things based on what .get() was called with?
        # Easier strategy: Mock .get() to return a new mock object, and set side_effect on THAT object's execute.
        
        # Actually, simpler manual mock for the whole service structure might be better if MagicMock gets messy.
        # But let's try configuring the side_effect of the .get() method.
        
        def get_req_mock(userId, id):
            req = MagicMock()
            if id == 'msg_summary':
                req.execute.return_value = {
                    'id': 'msg_summary',
                    'snippet': 'Summary',
                    'payload': {'headers': [{'name': 'Subject', 'value': 'Weekly Report'}]} # No ID in subject
                }
            elif id == 'msg_target':
                req.execute.return_value = {
                    'id': 'msg_target',
                    'snippet': 'Target',
                    'payload': {'headers': [{'name': 'Subject', 'value': f'Booking {order_id}'}]} # ID in subject
                }
            return req

        mock_messages_resource.get.side_effect = get_req_mock

        # Execute
        result = self.helper.search_order(order_id)
        
        # Verify
        print(f"Result Subject: {result['subject']}")
        self.assertEqual(result['id'], 'msg_target')
        self.assertIn(order_id, result['subject'])

if __name__ == "__main__":
    unittest.main()
