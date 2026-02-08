
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import bot
import shutil

class TestManimGeneration(unittest.TestCase):
    def setUp(self):
        # Setup dummy config
        self.channel_id = "test_channel_123"
        self.matrix = [1.0, 0.0, 0.0, 1.0]
        bot.update_user_data(self.channel_id, self.matrix)

    def test_create_manim_scene(self):
        print("Testing video generation...")
        success = bot.create_manim_scene(self.channel_id)
        self.assertTrue(success, "Manim scene creation failed")
        
        # Manim outputs to media/videos/transformation/1080p60/
        media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "videos", "transformation", "1080p60")
        output_path = os.path.join(media_dir, f"output_{self.channel_id}.mp4")
        
        self.assertTrue(os.path.exists(output_path), f"Output video not found at {output_path}")
        
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)
            
        media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
        if os.path.exists(media_dir):
            shutil.rmtree(media_dir)

if __name__ == '__main__':
    unittest.main()
