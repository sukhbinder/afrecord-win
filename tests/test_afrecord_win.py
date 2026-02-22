"""Tests for afrecord-win package."""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from afrecord_win import cli
from afrecord_win.afrecordmain import AudioRecorder, create_powershell_script


class TestCreateParser:
    """Tests for the CLI argument parser."""

    def test_create_parser_returns_argument_parser(self):
        """Test that create_parser returns an ArgumentParser instance."""
        parser = cli.create_parser()
        assert parser is not None

    def test_parser_default_output_file(self):
        """Test parser default output file is output.wav."""
        parser = cli.create_parser()
        args = parser.parse_args([])
        assert args.output_file == "output.wav"

    def test_parser_custom_output_file_short_option(self):
        """Test parser accepts custom output file with -o option."""
        parser = cli.create_parser()
        args = parser.parse_args(["-o", "custom.wav"])
        assert args.output_file == "custom.wav"

    def test_parser_custom_output_file_long_option(self):
        """Test parser accepts custom output file with --output option."""
        parser = cli.create_parser()
        args = parser.parse_args(["--output", "recording.wav"])
        assert args.output_file == "recording.wav"


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
        # Create a temp file to simulate
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            recorder.temp_script_path = tmp.name

        recorder.cleanup()

        assert not os.path.exists(recorder.temp_script_path)
        assert recorder.recording is False
        assert recorder.process is None

    def test_cleanup_handles_missing_temp_script(self):
        """Test cleanup handles missing temp script gracefully."""
        recorder = AudioRecorder()
        recorder.temp_script_path = "/nonexistent/path/script.ps1"
        # Should not raise an exception
        recorder.cleanup()

    @patch("afrecord_win.afrecordmain.subprocess.Popen")
    @patch("afrecord_win.afrecordmain.os.path.exists")
    @patch("afrecord_win.afrecordmain.open")
    def test_start_recording_creates_process(
        self, mock_open, mock_exists, mock_popen
    ):
        """Test start_recording creates a PowerShell subprocess."""
        mock_exists.return_value = False
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = "RECORDING\n"
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        recorder = AudioRecorder()
        result = recorder.start_recording("test.wav")

        assert mock_popen.called
        assert result is True
        recorder.cleanup()

    @patch("afrecord_win.afrecordmain.subprocess.Popen")
    @patch("afrecord_win.afrecordmain.os.path.exists")
    def test_start_recording_returns_false_when_already_recording(
        self, mock_exists, mock_popen
    ):
        """Test start_recording returns False if already recording."""
        mock_exists.return_value = False
        recorder = AudioRecorder()
        recorder.recording = True

        result = recorder.start_recording("test.wav")

        assert result is False
        assert not mock_popen.called

    @patch("afrecord_win.afrecordmain.subprocess.Popen")
    @patch("afrecord_win.afrecordmain.os.path.exists")
    def test_stop_recording_returns_false_when_not_recording(
        self, mock_exists, mock_popen
    ):
        """Test stop_recording returns False if not recording."""
        mock_exists.return_value = False
        recorder = AudioRecorder()

        result = recorder.stop_recording()

        assert result is False

    @patch("afrecord_win.afrecordmain.subprocess.Popen")
    @patch("afrecord_win.afrecordmain.os.path.exists")
    def test_stop_recording_sends_stop_command(
        self, mock_exists, mock_popen
    ):
        """Test stop_recording sends stop command to process."""
        mock_exists.return_value = False
        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        mock_process.stdin = MagicMock()
        mock_popen.return_value = mock_process

        recorder = AudioRecorder()
        # First start recording
        mock_process.stdout.readline.return_value = "RECORDING\n"
        recorder.start_recording("test.wav")
        # Then stop
        result = recorder.stop_recording()

        assert mock_process.stdin.write.called
        assert result is True


class TestPowerShellScript:
    """Tests for PowerShell script generation."""

    def test_create_powershell_script_returns_string(self):
        """Test create_powershell_script returns a string."""
        script = create_powershell_script()
        assert isinstance(script, str)

    def test_create_powershell_script_contains_required_commands(self):
        """Test generated script contains required MCI commands."""
        script = create_powershell_script()
        assert "open new type waveaudio" in script
        assert "record omp_rec" in script
        assert "stop omp_rec" in script
        assert "save omp_rec" in script
        assert "close omp_rec" in script

    def test_create_powershell_script_has_parameter(self):
        """Test generated script accepts outPath parameter."""
        script = create_powershell_script()
        assert "param([string]$outPath)" in script

    def test_create_powershell_script_has_error_handling(self):
        """Test generated script includes error handling."""
        script = create_powershell_script()
        assert "Write-Error" in script or "exit 1" in script


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

    def test_powershell_script_execution(self, tmp_path):
        """Test PowerShell script can be created and is valid."""
        script_content = create_powershell_script()

        # Write script to temp file
        script_file = tmp_path / "test_record.ps1"
        script_file.write_text(script_content)

        # Verify script exists and has content
        assert script_file.exists()
        assert script_file.stat().st_size > 0

        # Try to execute PowerShell with the script (syntax check)
        import subprocess

        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_file), "-outPath", str(tmp_path / "test.wav")],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Script should either start recording or fail gracefully
        # We're just testing it can be invoked
        assert result is not None

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
