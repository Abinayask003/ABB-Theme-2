// static/js/script.js
const singleRadio = document.querySelector('input[value="single"]');
const batchRadio = document.querySelector('input[value="batch"]');
const singleInput = document.getElementById('single_input');
const batchInput = document.getElementById('batch_input');
const micBtn = document.getElementById('mic-btn');
const textarea = document.querySelector('textarea[name="nl_instruction"]');

// Toggle input blocks
singleRadio.addEventListener('change', () => {
  singleInput.style.display = 'block';
  batchInput.style.display = 'none';
});
batchRadio.addEventListener('change', () => {
  singleInput.style.display = 'none';
  batchInput.style.display = 'block';
});

// 🎤 Speech recognition
if (micBtn) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;

    micBtn.addEventListener("click", () => {
      if (micBtn.classList.contains("listening")) {
        recognition.stop();
        micBtn.classList.remove("listening");
      } else {
        recognition.start();
        micBtn.classList.add("listening");
      }
    });

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      textarea.value = transcript;
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      alert("Speech recognition error: " + event.error);
      micBtn.classList.remove("listening");
    };

    recognition.onend = () => {
      micBtn.classList.remove("listening");
    };
  } else {
    micBtn.style.display = "none"; // hide mic if not supported
    console.warn("SpeechRecognition not supported in this browser.");
  }
}
