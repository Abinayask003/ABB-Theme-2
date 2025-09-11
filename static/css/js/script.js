// Toggle Single/Batch input
const singleRadio = document.querySelector('input[value="single"]');
const batchRadio = document.querySelector('input[value="batch"]');
const singleInput = document.getElementById('single_input');
const batchInput = document.getElementById('batch_input');

singleRadio.addEventListener('change', () => {
  singleInput.style.display = 'flex';
  batchInput.style.display = 'none';
});
batchRadio.addEventListener('change', () => {
  singleInput.style.display = 'none';
  batchInput.style.display = 'block';
});

// ---------- Voice Dictation ----------
const voiceBtn = document.getElementById("voiceBtn");
const textarea = document.getElementById("nl_instruction");

// Check browser support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
  voiceBtn.disabled = true;
  voiceBtn.title = "Speech recognition not supported in this browser";
} else {
  const recognition = new SpeechRecognition();
  recognition.continuous = true; // keep recording continuously
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  let isListening = false;

  voiceBtn.addEventListener("click", () => {
    if (!isListening) {
      recognition.start();
    } else {
      recognition.stop();
    }
  });

  recognition.onstart = () => {
    isListening = true;
    voiceBtn.classList.add("listening");
  };

  recognition.onend = () => {
    isListening = false;
    voiceBtn.classList.remove("listening");
  };

  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    textarea.value = transcript;
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
  };
}
