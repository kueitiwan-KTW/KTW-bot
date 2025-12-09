import unittest
from unittest.mock import MagicMock
from bot import HotelBot

class TestFailSafe(unittest.TestCase):
    def setUp(self):
        self.bot = HotelBot("knowledge_base.json", "persona.md")
        self.bot.gmail_helper = MagicMock()
        self.bot.validator_model = MagicMock()

    def test_validation_exception_blocks_access(self):
        # Setup fake order
        self.bot.gmail_helper.search_order.return_value = {
            "subject": "Booking", "body": "Secret Info"
        }
        
        # Simulate Exception in Validator
        self.bot.validator_model.generate_content.side_effect = Exception("API Timeout")
        
        # Execute
        result = self.bot.check_order_status("12345")
        
        # Verify
        print(f"Exception Result: {result}")
        self.assertEqual(result.get("status"), "blocked")
        self.assertIn("System Alert", result.get("message"))

    def test_ambiguous_result_blocks_access(self):
         # Setup fake order
        self.bot.gmail_helper.search_order.return_value = {
            "subject": "Booking", "body": "Secret Info"
        }
        
        # Simulate Garbled Response
        mock_response = MagicMock()
        mock_response.text = "I am not sure"
        self.bot.validator_model.generate_content.return_value = mock_response
        self.bot.validator_model.generate_content.side_effect = None # Clear previous side effect
        
        # Execute
        result = self.bot.check_order_status("12345")
        
        # Verify
        print(f"Ambiguous Result: {result}")
        self.assertEqual(result.get("status"), "blocked")
       

if __name__ == "__main__":
    unittest.main()
