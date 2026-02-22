import os
import sys
import subprocess
import tempfile
import time
import threading
from pathlib import Path


def create_powershell_script():
    """Create the PowerShell script content for audio recording"""
    return """
param([string]$outPath)

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class MciAudio {
    [DllImport("winmm.dll", CharSet=CharSet.Auto)]
    public static extern int mciSendString(
        string command, StringBuilder buffer, int bufferSize, IntPtr callback);
}
"@

function Mci([string]$cmd) {
    $buf = New-Object System.Text.StringBuilder 256
    $r = [MciAudio]::mciSendString($cmd, $buf, 256, [IntPtr]::Zero)
    if ($r -ne 0) {
        [Console]::Error.WriteLine("MCI error $r for: $cmd")
    }
    return $r
}

$r = Mci "open new type waveaudio alias omp_rec"
if ($r -ne 0) { exit 1 }

Mci "set omp_rec channels 1 samplespersec 16000 bitspersample 16"

$r = Mci "record omp_rec"
if ($r -ne 0) {
    Mci "close omp_rec"
    exit 1
}

Write-Output "RECORDING"
[Console]::Out.Flush()

# Block until parent closes stdin or writes a line
try { [Console]::In.ReadLine() | Out-Null } catch {}

# Stop and save
Mci "stop omp_rec"
$saveCmd = 'save omp_rec "' + $outPath + '"'
$r = Mci $saveCmd
if ($r -ne 0) {
    [Console]::Error.WriteLine("Save failed for: $saveCmd")
}
Mci "close omp_rec"

if (Test-Path $outPath) {
    Write-Output "SAVED"
} else {
    Write-Error "Output file was not created: $outPath"
    exit 1
}
"""


class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.process = None
        self.temp_script_path = None

    def start_recording(self, output_path: str) -> bool:
        """Start recording audio to the specified file path"""
        if self.recording:
            print("Already recording")
            return False

        try:
            # Create temporary PowerShell script
            self.temp_script_path = os.path.join(
                tempfile.gettempdir(), f"omp-stt-record-{int(time.time())}.ps1"
            )

            with open(self.temp_script_path, "w") as f:
                f.write(create_powershell_script())

            # Start PowerShell process
            self.process = subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    self.temp_script_path,
                    output_path,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for recording to start (check for "RECORDING" in output)
            start_time = time.time()
            output = ""

            while time.time() - start_time < 8:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        output += line
                        if "RECORDING" in line:
                            self.recording = True
                            print("Recording started")
                            return True

                # Check if process exited
                if self.process.poll() is not None:
                    break

            if not self.recording:
                # Process failed to start properly
                stderr_output = ""
                if self.process.stderr:
                    stderr_output = self.process.stderr.read()
                print(f"PowerShell recording failed to start: {stderr_output}")
                self.cleanup()
                return False

        except Exception as e:
            print(f"Error starting recording: {e}")
            self.cleanup()
            return False

        return True

    def stop_recording(self) -> bool:
        """Stop the current recording"""
        if not self.recording or not self.process:
            print("Not currently recording")
            return False

        try:
            # Send stop command to PowerShell script
            if self.process.stdin:
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()
                self.process.stdin.close()

            # Wait for process to finish with timeout
            timeout = 8
            start_time = time.time()

            while self.process.poll() is None and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.process.poll() is None:
                # Force kill if still running
                self.process.kill()
                self.process.wait()

            # Clean up temp script
            self.cleanup()

            print("Recording stopped")
            return True

        except Exception as e:
            print(f"Error stopping recording: {e}")
            self.cleanup()
            return False

    def cleanup(self):
        """Clean up temporary files and processes"""
        try:
            if self.temp_script_path and os.path.exists(self.temp_script_path):
                os.remove(self.temp_script_path)
        except:
            pass

        self.recording = False
        self.process = None


def main():
    """Main function to demonstrate the recorder"""
    if len(sys.argv) != 2:
        print("Usage: python powershell_record.py <output_file.wav>")
        sys.exit(1)

    output_file = sys.argv[1]

    # Create recorder instance
    recorder = AudioRecorder()

    try:
        print(f"Starting recording to {output_file}")

        # Start recording
        if not recorder.start_recording(output_file):
            print("Failed to start recording")
            sys.exit(1)

        # Wait for user input to stop
        input("Press Enter to stop recording...")

        # Stop recording
        recorder.stop_recording()

        # Verify file exists and has content
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"Recording saved: {output_file} ({size} bytes)")
        else:
            print("Recording file was not created")

    except KeyboardInterrupt:
        print("\nStopping recording...")
        recorder.stop_recording()
    except Exception as e:
        print(f"Error: {e}")
        recorder.stop_recording()


if __name__ == "__main__":
    main()
