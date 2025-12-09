import unittest
from unittest.mock import MagicMock, patch
from bot import HotelBot

class TestHotelBotIntegration(unittest.TestCase):
    def setUp(self):
        # Mock the file loading to avoid dependency on actual files during unit test if needed
        # But here we want to test with actual files if possible, or mock them.
        # Let's use the actual files since they exist.
        self.bot = HotelBot("knowledge_base.json", "persona.md")

    def test_find_answer_known(self):
        # Test known question
        answer = self.bot.find_answer("入住時間")
        self.assertIsNotNone(answer)
        self.assertIn("15:00", answer)

    def test_find_answer_unknown(self):
        # Test unknown question
        answer = self.bot.find_answer("火星怎麼去")
        self.assertIsNone(answer)

    def test_generate_response_known(self):
        response = self.bot.generate_response("請問幾點可以入住？")
        print(f"\nTest Response (Known): {response}")
        self.assertIn("【客服回覆】", response)
        self.assertIn("15:00", response)

    def test_generate_response_unknown(self):
        response = self.bot.generate_response("隨便亂打的問題")
        print(f"\nTest Response (Unknown): {response}")
        self.assertIn("需要進一步為您確認", response)

if __name__ == '__main__':
    unittest.main()
