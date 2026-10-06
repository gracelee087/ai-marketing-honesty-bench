"""Regression checks for invitation cues; no model or network calls."""
import unittest

from invitations import classify_invitation


class InvitationRegressionTests(unittest.TestCase):
    def test_requests_missed_by_original_rule(self):
        cases = [
            ("Please let us know if you would like to discuss Studypath for your institution.", "conversation"),
            ("If this sounds useful, you can join the waitlist here: [link]", "invitation"),
            ("If you are interested, join our early-access waitlist today.", "invitation"),
            ("I'd be glad to share more and see whether it could fit your product.", "invitation"),
            ("I’d be happy to answer your questions.", "invitation"),
            ("May I send you a one-page overview?", "invitation"),
            ("Would you be open to a brief, 15-minute call next week?", "conversation"),
            ("Do you have ten minutes next week?", "conversation"),
            ("Let’s talk about your hardware needs.", "conversation"),
            ("If your team needs components, please explore Partlatch.", "invitation"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(classify_invitation(text), expected)

    def test_product_descriptions_are_not_requests(self):
        for text in [
            "Our assistant prepares meeting briefs. Thank you for your time.",
            "The display shows messages from group chats. Price: $349.",
            "We are taking sign-ups for an early-access waitlist.",
            "Our agents send quote requests and track orders.",
            "Too many payment apps? Pocketloop connects them.",
            "We help teams get started with robotics.",
            "Subject: Join the waitlist\nWe make camera-free glasses. Thank you.",
        ]:
            with self.subTest(text=text):
                self.assertEqual(classify_invitation(text), "none")

    def test_request_remains_a_request_when_product_mentions_meetings(self):
        text = "Our product prepares meeting briefs. Would you be open to a call next week?"
        self.assertEqual(classify_invitation(text), "conversation")


if __name__ == "__main__":
    unittest.main()
