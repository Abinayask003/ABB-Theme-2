// Mode switch (single/batch)
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

// 🎤 Voice recognition
const textarea = document.querySelector('#single_input textarea');

// Create mic button dynamically inside textarea container
const micBtn = document.createElement('button');
micBtn.id = 'voiceBtn';
micBtn.classList.add('mic-btn');
micBtn.innerHTML = '🎤';
document.querySelector('#single_input').classList.add('input-with-mic');
document.querySelector('#single_input').appendChild(micBtn);

// Initialize SpeechRecognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
  console.warn('Browser does not support Speech Recognition API.');
  micBtn.disabled = true;
} else {
  const recognition = new SpeechRecognition();
  recognition.continuous = true; // continuous dictation
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  let finalTranscript = '';

  recognition.onstart = () => {
    micBtn.classList.add('listening');
  };

  recognition.onend = () => {
    micBtn.classList.remove('listening');
    // Auto-restart if user clicked stop by mistake
    if (micBtn.dataset.listening === 'true') {
      recognition.start();
    }
  };

  recognition.onresult = (event) => {
    let interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript + ' ';
      } else {
        interimTranscript += transcript;
      }
    }
    textarea.value = finalTranscript + interimTranscript;
  };

  // Mic button click
  micBtn.addEventListener('click', () => {
    if (micBtn.dataset.listening === 'true') {
      // stop
      micBtn.dataset.listening = 'false';
      recognition.stop();
    } else {
      // start
      micBtn.dataset.listening = 'true';
      recognition.start();
    }
  });
}
