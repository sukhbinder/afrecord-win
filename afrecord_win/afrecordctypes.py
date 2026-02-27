import ctypes
import sys
import time
from ctypes import wintypes

# Load winmm.dll
winmm = ctypes.WinDLL("winmm.dll")

# Define mciSendStringW
mciSendString = winmm.mciSendStringW
mciSendString.argtypes = [
    wintypes.LPCWSTR,  # command string
    wintypes.LPWSTR,  # return buffer
    wintypes.UINT,  # buffer size
    wintypes.HANDLE,  # callback (unused)
]
mciSendString.restype = wintypes.UINT


def mci(cmd):
    buffer = ctypes.create_unicode_buffer(256)
    result = mciSendString(cmd, buffer, 256, None)
    if result != 0:
        print(f"MCI error {result} for: {cmd}", file=sys.stderr)
    return result


def record_audio(out_path):
    if mci("open new type waveaudio alias omp_rec") != 0:
        return False

    mci("set omp_rec channels 1 samplespersec 16000 bitspersample 16")

    if mci("record omp_rec") != 0:
        mci("close omp_rec")
        return False

    print("RECORDING")
    sys.stdout.flush()

    try:
        input()  # Wait until Enter pressed (like ReadLine)
    except EOFError:
        pass

    mci("stop omp_rec")

    save_cmd = f'save omp_rec "{out_path}"'
    if mci(save_cmd) != 0:
        print(f"Save failed for: {save_cmd}", file=sys.stderr)

    mci("close omp_rec")

    return True


if __name__ == "__main__":
    output_file = "output.wav"
    if record_audio(output_file):
        print("SAVED")
    else:
        print("Recording failed")
