// Grid Configuration
const grid = document.getElementById('grid');

function calculateGridDimensions() {
    const headerHeight = 100;
    const footerHeight = 200;
    const cellHeight = 80;
    
    const availableHeight = window.innerHeight - (headerHeight + footerHeight);
    const rows = Math.floor(availableHeight / cellHeight);
    const gridSize = window.innerWidth >= 1200 ? 24 : 
                    window.innerWidth >= 1024 ? 18 : 12;

    return { rows, gridSize };
}

// Progress Tracking
let activeNumber = null;
const progressTracking = {
    '01': 0, '02': 0, '03': 0, '04': 0, '05': 0
};

function createGridCell() {
    const div = document.createElement('div');
    div.textContent = Math.floor(Math.random() * 10);
    
    // Add random animations
    if(Math.random() < 0.2) div.classList.add('b-20');
    else if(Math.random() < 0.4) div.classList.add('l-20');
    
    if(Math.random() < 0.3) div.classList.add('d-1');
    else if(Math.random() < 0.6) div.classList.add('d-1_5');
    
    if(Math.random() < 0.2) div.classList.add('du-2');
    else if(Math.random() < 0.6) div.classList.add('du-8');
    
    // Add data attribute to track if cell has been clicked
    div.setAttribute('data-clicked', 'false');
    div.onclick = handleGridClick;
    return div;
}

function handleGridClick() {
    if(!activeNumber) return;
    
    // Check if cell has already been clicked
    if(this.getAttribute('data-clicked') === 'true') return;
    
    const numberIndex = activeNumber.textContent;
    const clickedNumber = this.textContent;
    
    const requiredNumber = {
        '01': '1',
        '02': '2',
        '03': '3',
        '04': '4',
        '05': '5'
    };

    // Changed from 10 to 5
    if(clickedNumber === requiredNumber[numberIndex] && progressTracking[numberIndex] < 5) {
        progressTracking[numberIndex]++;
        updateProgress(numberIndex);
        
        this.setAttribute('data-clicked', 'true');
        
        let newNumber;
        do {
            newNumber = Math.floor(Math.random() * 10).toString();
        } while(newNumber === clickedNumber);
        
        this.style.opacity = '0';
        setTimeout(() => {
            this.textContent = newNumber;
            this.style.opacity = '1';
        }, 200);
    }
}

function updateProgress(numberIndex) {
    const index = parseInt(numberIndex) - 1;
    // Changed from 10 to 5
    const progress = (progressTracking[numberIndex] / 5) * 100;
    const progressBar = document.querySelectorAll('.progress-bar')[index];
    const progressFill = progressBar.querySelector('.progress-fill');
    const progressText = progressBar.querySelector('span');
    
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${Math.floor(progress)}%`;

    updateTotalProgress();
}

function updateTotalProgress() {
    const totalProgress = Object.values(progressTracking).reduce((a, b) => a + b, 0);
    // Changed from 50 to 25 (5 sections × 5 clicks each = 25 total clicks needed)
    const headerProgress = Math.floor((totalProgress / 25) * 100);
    document.querySelector('.header-percent').textContent = `${headerProgress}%`;

    if(totalProgress === 25) {
        showCompletion();
    }
}


function showCompletion() {
    // Create completion overlay
    const overlay = document.createElement('div');
    overlay.className = 'completion-overlay';
    
    // Create completion container
    const completionContainer = document.createElement('div');
    completionContainer.className = 'completion-logo';
    
    // Create COMPLETED text
    const completedText = document.createElement('span');
    completedText.className = 'completion-text';
    completedText.textContent = 'COMPLETED';
    
     const flagContainer = document.createElement('div');
    flagContainer.className = 'completion-flag-container';
    
    // Create flag
    const flag = document.createElement('div');
    flag.className = 'completion-flag';

    // Encoded flag
    const decode = (str) => {
        return decodeURIComponent(escape(atob(str)));
    };
    
    const encodedFlag = "SU5Te1czbENvTTNfVDBfMW5zMG1uaWg0Y0tfMjAyNSEhfQ==";
    flag.textContent = decode(encodedFlag);
    
    // Assemble the elements
    flagContainer.appendChild(flag);
    completionContainer.appendChild(completedText);
    completionContainer.appendChild(flagContainer);
    overlay.appendChild(completionContainer);
    document.body.appendChild(overlay);
}


function initializeGrid() {
    grid.innerHTML = '';
    const { rows, gridSize } = calculateGridDimensions();
    const totalCells = rows * gridSize;

    for(let i = 0; i < totalCells; i++) {
        grid.appendChild(createGridCell());
    }

    grid.style.gridTemplateColumns = `repeat(${gridSize}, 1fr)`;
}

// Event Listeners
document.querySelectorAll('.number').forEach(number => {
    number.onclick = function() {
        if(activeNumber) {
            activeNumber.style.backgroundColor = '';
            activeNumber.style.color = '';
        }
        activeNumber = this;
        this.style.backgroundColor = '#ff4d4d';
        this.style.color = '#1a0505';
    };
});

// Hover Effect
document.addEventListener("mousemove", function(event) {
    const footer = document.querySelector('footer');
    if(event.pageY >= footer.getBoundingClientRect().top) return;

    document.querySelectorAll("#grid div").forEach(div => {
        const rect = div.getBoundingClientRect();
        const distance = Math.hypot(
            event.pageX - (rect.left + rect.width/2),
            event.pageY - (rect.top + rect.height/2)
        );

        const animationClasses = Array.from(div.classList)
            .filter(className => ['b-20', 'l-20', 'd-1', 'd-1_5', 'du-2', 'du-8']
            .includes(className));

        div.className = animationClasses.join(' ');

        if (distance < 50) {
            div.classList.add('hover-effect');
        } else if (distance < 80) {
            div.classList.add('hover-effect-medium');
        } else if (distance < 120) {
            div.classList.add('hover-effect-light');
        }
    });
});

// Resize handler with debounce
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(initializeGrid, 100);
});

// Initial grid creation
initializeGrid();

