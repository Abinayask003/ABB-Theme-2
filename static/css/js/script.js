// Mode toggle
const singleRadio = document.querySelector('input[value="single"]');
const batchRadio = document.querySelector('input[value="batch"]');
const singleInput = document.getElementById('single_input');
const batchInput = document.getElementById('batch_input');

singleRadio.addEventListener('change', () => {
  singleInput.style.display = 'block';
  batchInput.style.display = 'none';
});
batchRadio.addEventListener('change', () => {
  singleInput.style.display = 'none';
  batchInput.style.display = 'block';
});

// Voice input
const voiceBtn = document.getElementById("voiceBtn");
const textarea = document.querySelector("textarea[name='nl_instruction']");
let recognition;
let listening = false;

if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    textarea.value = transcript;
  };

  recognition.onstart = () => {
    voiceBtn.textContent = "⏹️"; // change icon when recording
    voiceBtn.classList.add("listening");
  };

  recognition.onend = () => {
    voiceBtn.textContent = "🎤"; // back to mic
    voiceBtn.classList.remove("listening");
    listening = false;
  };

  voiceBtn.addEventListener("click", () => {
    if (!listening) {
      recognition.start();
      listening = true;
    } else {
      recognition.stop();
    }
  });
} else {
  voiceBtn.style.display = "none";
  alert("Voice recognition not supported in this browser.");
}
