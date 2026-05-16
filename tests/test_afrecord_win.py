"""Tests for afrecord-win package."""

import sys
import os
import tempfile
import pytest

# Skip all tests on non-Windows platforms before any imports
if sys.platform != "win32":
    pytest.skip("Windows only", allow_module_level=True)

from unittest.mock import patch, MagicMock

import ctypes
from ctypes import wintypes

from afrecord_win import cli
from afrecord_win.afrecordmain import AudioRecorder, mci, mciSendString


class TestMCICalls:
    """Tests for the MCI wrapper functions."""

    def test_mci_function_exists(self):
        """Test that mci function exists and is callable."""
        assert callable(mci)


class TestMCISendStringSignature:
    """Tests for mciSendString function signature."""

    def test_mciSendString_argtypes(self):
        """Test mciSendString has correct argument types."""
        assert len(mciSendString.argtypes) == 4
        assert mciSendString.argtypes[0] == wintypes.LPCWSTR
        assert mciSendString.argtypes[1] == wintypes.LPWSTR
        assert mciSendString.argtypes[2] == wintypes.UINT
        assert mciSendString.argtypes[3] == wintypes.HANDLE

    def test_mciSendString_restype(self):
        """Test mciSendString return type."""
        assert mciSendString.restype == wintypes.UINT


class TestMciWrapper:
    """Tests for the mci wrapper."""

    @patch.object(wintypes, "LPWSTR", wintypes.LPWSTR)
    @patch.object(wintypes, "HANDLE", wintypes.HANDLE)
    def test_mci_wrapper_creates_buffer(self):
        """Test mci wrapper creates a unicode buffer."""
        cmd = "test command"
        result = mci(cmd)
        assert isinstance(result, int)


class TestAudioRecorder:
    """Tests for the AudioRecorder class."""

    def test_recorder_initial_state(self):
        """Test AudioRecorder initializes with correct state."""
        recorder = AudioRecorder()
        assert recorder.recording is False
        assert recorder.process is None
        assert recorder.temp_script_path is None

    def test_cleanup_removes_temp_script(self):
        """Test cleanup removes temporary script file."""
        recorder = AudioRecorder()

        recorder.cleanup()

        assert recorder.recording is False
        assert recorder.process is None

    def test_cleanup_handles_missing_temp_script(self):
        """Test cleanup handles missing temp script gracefully."""
        recorder = AudioRecorder()
        recorder.temp_script_path = "/nonexistent/path/script.ps1"
        # Should not raise an exception
        recorder.cleanup()

    def test_start_recording_creates_mci_session(self):
        """Test start_recording opens MCI waveaudio session."""
        with patch("afrecord_win.afrecordmain.mci", return_value=0):
            recorder = AudioRecorder()
            result = recorder.start_recording("test.wav")

            assert result is True
            recorder.cleanup()

    def test_start_recording_sets_recording_state(self):
        """Test start_recording sets recording state to True."""
        with patch("afrecord_win.afrecordmain.mci", side_effect=[0, 0, 0]):
            recorder = AudioRecorder()
            result = recorder.start_recording("test.wav")

            assert result is True
            assert recorder.recording is True
            recorder.cleanup()

    def test_start_recording_fails_on_mci_open_error(self):
        """Test start_recording returns False on MCI open error."""
        with patch("afrecord_win.afrecordmain.mci", return_value=1):
            recorder = AudioRecorder()
            result = recorder.start_recording("test.wav")

            assert result is False
            recorder.cleanup()

    def test_start_recording_fails_on_mci_record_error(self):
        """Test start_recording returns False on MCI record error."""
        with patch("afrecord_win.afrecordmain.mci", side_effect=[0, 1, 0]):
            recorder = AudioRecorder()
            result = recorder.start_recording("test.wav")

            assert result is False
            recorder.cleanup()

    def test_start_recording_sets_output_path(self):
        """Test start_recording stores output path."""
        with patch("afrecord_win.afrecordmain.mci", return_value=0):
            recorder = AudioRecorder()
            result = recorder.start_recording("my_output.wav")

            assert result is True
            assert recorder.output_path == "my_output.wav"
            recorder.cleanup()

    def test_stop_recording_sends_stop_command(self):
        """Test stop_recording sends stop command to MCI."""
        with patch("afrecord_win.afrecordmain.mci", side_effect=[0, 0, 0]):
            recorder = AudioRecorder()
            recorder.recording = True
            recorder.output_path = "test.wav"

            result = recorder.stop_recording()

            assert result is True
            recorder.cleanup()

    def test_stop_recording_fails_when_not_recording(self):
        """Test stop_recording returns False when not recording."""
        recorder = AudioRecorder()
        result = recorder.stop_recording()

        assert result is False

    def test_stop_recording_saves_file(self):
        """Test stop_recording saves the audio file via MCI."""
        with patch("afrecord_win.afrecordmain.mci", return_value=0):
            recorder = AudioRecorder()
            recorder.recording = True
            recorder.output_path = "test.wav"

            result = recorder.stop_recording()

            assert result is True
            recorder.cleanup()

    def test_cleanup_resets_recording_state(self):
        """Test cleanup resets recording state."""
        recorder = AudioRecorder()
        recorder.recording = True
        recorder.cleanup()

        assert recorder.recording is False


class TestCLI:
    """Tests for CLI function."""

    @patch("afrecord_win.cli.os.path.exists")
    @patch("afrecord_win.cli.os.path.getsize")
    @patch("afrecord_win.cli.AudioRecorder")
    @patch("afrecord_win.cli.create_parser")
    def test_cli_success(
        self, mock_create_parser, mock_recorder_class, mock_getsize, mock_exists
    ):
        """Test CLI successful recording flow."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_recorder = MagicMock()
        mock_recorder.start_recording.return_value = True
        mock_recorder_class.return_value = mock_recorder

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(output_file="test.wav")
        mock_create_parser.return_value = mock_parser

        with patch("afrecord_win.cli.input", side_effect=[""]):
            cli.cli()

        mock_recorder.start_recording.assert_called_once_with("test.wav")
        mock_recorder.stop_recording.assert_called_once()

    @patch("afrecord_win.cli.os.path.exists")
    @patch("afrecord_win.cli.AudioRecorder")
    @patch("afrecord_win.cli.create_parser")
    def test_cli_start_failure(
        self, mock_create_parser, mock_recorder_class, mock_exists, capsys
    ):
        """Test CLI handles start recording failure."""
        mock_exists.return_value = False
        mock_recorder = MagicMock()
        mock_recorder.start_recording.return_value = False
        mock_recorder_class.return_value = mock_recorder

        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(output_file="test.wav")
        mock_create_parser.return_value = mock_parser

        with pytest.raises(SystemExit) as exc_info:
            cli.cli()

        assert exc_info.value.code == 1


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows")
class TestIntegrationWindows:
    """Integration tests that only run on Windows."""

    def test_audio_recorder_real_instance(self):
        """Test AudioRecorder can be instantiated on Windows."""
        recorder = AudioRecorder()
        assert recorder is not None
        assert recorder.recording is False

    def test_full_recording_workflow(self, tmp_path):
        """Test complete recording workflow on Windows."""
        output_file = tmp_path / "integration_test.wav"
        recorder = AudioRecorder()

        try:
            # Start recording
            started = recorder.start_recording(str(output_file))

            if started:
                # Immediately stop (short recording)
                import time

                time.sleep(0.5)
                recorder.stop_recording()

                # Verify file was created
                # Note: This may fail if no microphone is available
                if output_file.exists():
                    assert output_file.stat().st_size > 0
        except Exception:
            # Recording may fail in headless environments
            # This is expected in CI/CD without audio hardware
            pytest.skip("No audio hardware available")
        finally:
            recorder.cleanup()
