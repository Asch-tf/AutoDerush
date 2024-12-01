let startTime;
let elapsedTime = 0;
let timerInterval;
let lapCount = 0;

const minutesDisplay = document.getElementById('minutes');
const secondsDisplay = document.getElementById('seconds');
const millisecondsDisplay = document.getElementById('milliseconds');
const startButton = document.getElementById('startBtn');
const stopButton = document.getElementById('stopBtn');
const resetButton = document.getElementById('resetBtn');
const lapButton = document.getElementById('lapBtn');
const themeButton = document.getElementById('themeBtn');
const lapsList = document.getElementById('lapsList');

// Gestion du thème
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', newTheme);
    themeButton.textContent = newTheme === 'light' ? '🌙' : '☀️';
}

function startTimer() {
    startTime = Date.now() - elapsedTime;
    timerInterval = setInterval(updateTime, 10);
    startButton.disabled = true;
    stopButton.disabled = false;
    lapButton.disabled = false;
}

function stopTimer() {
    clearInterval(timerInterval);
    startButton.disabled = false;
    stopButton.disabled = true;
    lapButton.disabled = true;
}

function resetTimer() {
    clearInterval(timerInterval);
    elapsedTime = 0;
    lapCount = 0;
    displayTime(0);
    startButton.disabled = false;
    stopButton.disabled = false;
    lapButton.disabled = true;
    lapsList.innerHTML = '';
}

function updateTime() {
    elapsedTime = Date.now() - startTime;
    displayTime(elapsedTime);
}

function displayTime(time) {
    const minutes = Math.floor(time / (1000 * 60));
    const seconds = Math.floor((time % (1000 * 60)) / 1000);
    const milliseconds = Math.floor((time % 1000) / 10);

    minutesDisplay.textContent = padNumber(minutes);
    secondsDisplay.textContent = padNumber(seconds);
    millisecondsDisplay.textContent = padNumber(milliseconds);
}

function padNumber(number) {
    return number.toString().padStart(2, '0');
}

function addLap() {
    lapCount++;
    const lapTime = elapsedTime;
    const lapItem = document.createElement('li');
    lapItem.textContent = `Tour ${lapCount}: ${formatTime(lapTime)}`;
    lapsList.insertBefore(lapItem, lapsList.firstChild);
}

function formatTime(time) {
    const minutes = Math.floor(time / (1000 * 60));
    const seconds = Math.floor((time % (1000 * 60)) / 1000);
    const milliseconds = Math.floor((time % 1000) / 10);
    return `${padNumber(minutes)}:${padNumber(seconds)}:${padNumber(milliseconds)}`;
}

// Event Listeners
startButton.addEventListener('click', startTimer);
stopButton.addEventListener('click', stopTimer);
resetButton.addEventListener('click', resetTimer);
lapButton.addEventListener('click', addLap);
themeButton.addEventListener('click', toggleTheme);

// Initialisation
lapButton.disabled = true;
stopButton.disabled = true;
 