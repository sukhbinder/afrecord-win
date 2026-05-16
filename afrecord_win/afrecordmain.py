import ctypes
import os
import sys
from ctypes import wintypes

winmm = ctypes.WinDLL("winmm.dll")

mciSendString = winmm.mciSendStringW
mciSendString.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.UINT,
    wintypes.HANDLE,
]

mciSendString.restype = wintypes.UINT


def mci(cmd):
    buffer = ctypes.create_unicode_buffer(256)
    result = mciSendString(cmd, buffer, 256, None)
    if result != 0:
        print(f"MCI error {result} for: {cmd}", file=sys.stderr)
    return result


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
            if mci("open new type waveaudio alias omp_rec") != 0:
                return False

            buffer = ctypes.create_unicode_buffer(256)
            mciSendString(
                "set omp_rec channels 1 samplepersec 16000 bitspersample 16",
                buffer,
                256,
                None,
            )

            if mci("record omp_rec") != 0:
                mci("close omp_rec")
                return False

            print("RECORDING")
            sys.stdout.flush()

            self.output_path = output_path
            self.recording = True

        except Exception as e:
            print(f"Error starting recording: {e}")
            self.cleanup()
            return False

        return True

    def stop_recording(self) -> bool:
        """Stop the current recording"""
        if not self.recording:
            print("Not currently recording")
            return False

        try:
            mci("stop omp_rec")
            save_cmd = f'save omp_rec "{self.output_path}"'
            if mci(save_cmd) != 0:
                print(f"Save failed for : {save_cmd}", file=sys.stderr)
                return False

            mci("close omp_rec")
            self.cleanup()
            print("Recording stopped")
            return True

        except Exception as e:
            print(f"Error stopping recording: {e}")
            self.cleanup()
            return False

    def cleanup(self):
        """Clean up temporary files and processes"""
        self.recording = False


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
