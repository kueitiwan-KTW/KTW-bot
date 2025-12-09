import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from bot import HotelBot

class TestPastBlocking(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.bot = HotelBot("knowledge_base.json", "persona.md")
        self.bot.gmail_helper = MagicMock()
        self.bot.validator_model = MagicMock() # Mock the LLM

    def test_past_order_blocked(self):
        # Setup specific past date
        fake_body = "Thank you for booking. Check-in: 2020-01-01. Order ID: 12345"
        self.bot.gmail_helper.search_order.return_value = {
            "subject": "Booking Confirmed",
            "body": fake_body
        }
        
        # Mock LLM saying "YES" (it is past)
        mock_response = MagicMock()
        mock_response.text = "YES"
        self.bot.validator_model.generate_content.return_value = mock_response

        # Execute
        result = self.bot.check_order_status("12345")
        
        # Verify
        print(f"Result: {result}")
        self.assertEqual(result.get("status"), "blocked")
        self.assertEqual(result.get("reason"), "privacy_protection")

    def test_future_order_allowed(self):
        # Setup future date
        fake_body = "Thank you for booking. Check-in: 2099-01-01. Order ID: 67890"
        self.bot.gmail_helper.search_order.return_value = {
            "subject": "Booking Confirmed",
            "body": fake_body
        }
        
        # Mock LLM saying "NO" (it is NOT past)
        mock_response = MagicMock()
        mock_response.text = "NO"
        self.bot.validator_model.generate_content.return_value = mock_response

        # Execute
        result = self.bot.check_order_status("67890")
        
        # Verify
        print(f"Result: {result}")
        self.assertEqual(result.get("status"), "found")
        self.assertIn("email_body", result)

if __name__ == "__main__":
    unittest.main()
