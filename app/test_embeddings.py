import unittest
from app.embeddings import generate_embedding


class TestGenerateEmbedding(unittest.TestCase):
    def setUp(self):
        # Sample input text for testing
        self.sample_text = "This is a test sentence."

    def test_generate_embedding_output(self):
        # Generate the embedding for the sample text
        embedding = generate_embedding(self.sample_text)

        # Check if the output is a list
        self.assertIsInstance(embedding, list, "Output should be a list.")

        # Check if the list contains floating-point numbers
        self.assertTrue(
            all(isinstance(x, float) for x in embedding),
            "All elements in the output list should be floats.",
        )

        # Check if the embedding length is consistent
        expected_length = 384  # Typically the embedding length for this model
        self.assertEqual(
            len(embedding),
            expected_length,
            f"Embedding length should be {expected_length}.",
        )


if __name__ == "__main__":
    unittest.main()
