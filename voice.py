from vosk import Model, KaldiRecognizer
import pyaudio
import json

# Load the model
model = Model("model")  # Make sure this points to your extracted folder
rec = KaldiRecognizer(model, 16000)

# Setup microphone stream
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=8000)
stream.start_stream()

print("Listening... Speak into the mic.\n")

# Process audio in real time
while True:
    data = stream.read(4000, exception_on_overflow=False)
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        print(result.get("text", ""))
    # You can also access partial results:
    # else:
    #     print(json.loads(rec.PartialResult())["partial"])
