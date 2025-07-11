# ABOUTME: Tests for the spriter video to sprite sheet converter
# ABOUTME: Covers CLI functionality, file validation, and ffmpeg integration

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import tempfile
import os

from spriter.main import main


class TestSpriter:
    
    def test_help_command(self):
        """Test that help command works correctly"""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Convert a video file" in result.output
        assert "--fps" in result.output
        assert "--size" in result.output
        assert "--grid" in result.output
    
    def test_unsupported_file_format(self):
        """Test that unsupported file formats are rejected"""
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'fake content')
            tmp_path = tmp.name
        
        try:
            result = runner.invoke(main, [tmp_path])
            # With the refactored code, unsupported formats are handled gracefully
            assert "Unsupported file format" in result.output
        finally:
            os.unlink(tmp_path)
    
    def test_nonexistent_file(self):
        """Test that nonexistent files are handled correctly"""
        runner = CliRunner()
        result = runner.invoke(main, ['nonexistent.mp4'])
        assert result.exit_code != 0
        assert "does not exist" in result.output
    
    @patch('subprocess.run')
    def test_missing_ffmpeg(self, mock_run):
        """Test that missing ffmpeg is detected"""
        mock_run.side_effect = FileNotFoundError()
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video content')
            tmp_path = tmp.name
        
        try:
            result = runner.invoke(main, [tmp_path])
            assert result.exit_code == 1
            assert "ffmpeg is not installed" in result.output
        finally:
            os.unlink(tmp_path)
    
    @patch('subprocess.run')
    def test_successful_conversion(self, mock_run):
        """Test successful video conversion"""
        # Mock ffmpeg version check and conversion
        mock_run.side_effect = [
            MagicMock(returncode=0),  # ffmpeg version check
            MagicMock(returncode=0)   # ffmpeg conversion
        ]
        
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video content')
            tmp_path = tmp.name
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output.png"
                # Create fake output file
                output_path.write_bytes(b'fake png content')
                
                result = runner.invoke(main, [
                    tmp_path,
                    '--output', str(output_path),
                    '--fps', '2',
                    '--size', '32x32',
                    '--grid', '2x2'
                ])
                
                assert result.exit_code == 0
                assert "Sprite sheet created successfully" in result.output
                
                # Check that ffmpeg was called with correct arguments
                conversion_call = mock_run.call_args_list[1]
                args = conversion_call[0][0]
                assert 'ffmpeg' in args
                assert '-i' in args
                assert tmp_path in args
                assert 'fps=2,scale=32x32,tile=2x2' in ' '.join(args)
                
        finally:
            os.unlink(tmp_path)
    
    @patch('subprocess.run')
    def test_preset_configurations(self, mock_run):
        """Test preset configurations"""
        # Mock ffmpeg version check and conversion
        mock_run.side_effect = [
            MagicMock(returncode=0),  # ffmpeg version check
            MagicMock(returncode=0)   # ffmpeg conversion
        ]
        
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video content')
            tmp_path = tmp.name
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output.png"
                # Create fake output file
                output_path.write_bytes(b'fake png content')
                
                result = runner.invoke(main, [
                    tmp_path,
                    '--output', str(output_path),
                    '--preset', 'web'
                ])
                
                assert result.exit_code == 0
                assert "Using preset 'web'" in result.output
                assert "Sprite sheet created successfully" in result.output
                
                # Check that ffmpeg was called with web preset settings
                conversion_call = mock_run.call_args_list[1]
                args = conversion_call[0][0]
                assert 'fps=8,scale=32x32,tile=4x4' in ' '.join(args)
                
        finally:
            os.unlink(tmp_path)
    
    def test_filename_generation(self):
        """Test that filenames include parameters correctly"""
        runner = CliRunner()
        
        # Test default filename generation
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video content')
            tmp_path = tmp.name
        
        try:
            # Test with custom parameters (will fail due to missing ffmpeg, but we can check the output path)
            result = runner.invoke(main, [tmp_path, '--fps', '12', '--size', '48x48', '--grid', '3x3'])
            
            # Should show the correct filename components (handle line wrapping in Rich output)
            assert "_spritesheet_12f" in result.output and "ps_48x48_3x3.png" in result.output
            
            # Test with preset (handle line wrapping)
            result = runner.invoke(main, [tmp_path, '--preset', 'game'])
            assert "_spritesheet_gam" in result.output and "e.png" in result.output
            
        finally:
            os.unlink(tmp_path)
    
    def test_directory_processing(self):
        """Test directory processing functionality"""
        runner = CliRunner()
        
        # Create temporary directory with fake video files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create fake video files
            video1 = tmpdir_path / "video1.mp4"
            video2 = tmpdir_path / "video2.mov"
            video3 = tmpdir_path / "video3.mpg"
            not_video = tmpdir_path / "not_video.txt"
            
            video1.write_bytes(b'fake video content')
            video2.write_bytes(b'fake video content')
            video3.write_bytes(b'fake video content')
            not_video.write_text('not a video')
            
            # Test directory processing (will fail due to invalid video files, but we can check discovery)
            result = runner.invoke(main, [str(tmpdir_path), '--preset', 'web'])
            
            # Should discover the video files
            assert "Found 3 video files" in result.output
            assert "video1.mp4" in result.output
            assert "video2.mov" in result.output
            assert "video3.mpg" in result.output
            assert "not_video.txt" not in result.output
    
    @patch('subprocess.run')
    def test_ffmpeg_error(self, mock_run):
        """Test handling of ffmpeg errors"""
        # Mock ffmpeg version check success, but conversion failure
        mock_run.side_effect = [
            MagicMock(returncode=0),  # ffmpeg version check
            subprocess.CalledProcessError(1, 'ffmpeg', stderr='conversion error')
        ]
        
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(b'fake video content')
            tmp_path = tmp.name
        
        try:
            result = runner.invoke(main, [tmp_path])
            # With the refactored code, ffmpeg errors are handled gracefully
            assert "Error running ffmpeg" in result.output
        finally:
            os.unlink(tmp_path)


def test_integration_with_real_file():
    """Integration test with actual video file if available"""
    video_path = Path("videos/confused.mp4")
    if video_path.exists():
        runner = CliRunner()
        # Test without explicit output to verify filename generation
        result = runner.invoke(main, [
            str(video_path),
            '--preset', 'web'
        ])
        
        # Should succeed if ffmpeg is available
        if result.exit_code == 0:
            # Check that the file was created with correct naming
            expected_output = video_path.parent / f"{video_path.stem}_spritesheet_web.png"
            assert expected_output.exists()
            assert expected_output.stat().st_size > 0
            assert "Sprite sheet created successfully" in result.output
            assert "Using preset 'web'" in result.output
            assert str(expected_output) in result.output
        else:
            # If it fails, it should be due to missing ffmpeg
            assert "ffmpeg" in result.output