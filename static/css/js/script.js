// Toggle between Single and Batch modes
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

// Voice recognition
const voiceBtn = document.getElementById('voiceBtn');
const textarea = singleInput.querySelector('textarea');

let recognition;
let listening = false;

if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  recognition.onresult = (event) => {
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      }
    }
    if (finalTranscript.trim() !== '') {
      textarea.value += (textarea.value ? ' ' : '') + finalTranscript;
    }
  };

  recognition.onstart = () => {
    listening = true;
    voiceBtn.classList.add('listening');
  };

  recognition.onend = () => {
    listening = false;
    voiceBtn.classList.remove('listening');
  };

  recognition.onerror = (event) => {
    console.error('Speech recognition error', event);
    listening = false;
    voiceBtn.classList.remove('listening');
  };

  voiceBtn.addEventListener('click', () => {
    if (listening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  });

} else {
  voiceBtn.disabled = true;
  voiceBtn.title = "Speech Recognition not supported in this browser";
}
