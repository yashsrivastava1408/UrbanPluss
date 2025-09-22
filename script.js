document.addEventListener('DOMContentLoaded', () => {
    // --- API & Configuration ---
    const DATA_API_URL = 'http://localhost:5001/api/traffic-data';
    const START_API_URL = 'http://localhost:5001/api/start-analysis';
    const YELLOW_LIGHT_DURATION = 3; 

    // --- DOM Element References ---
    const loadingOverlay = document.getElementById('loading-overlay');
    const loginPage = document.getElementById('login-page');
    const appContainer = document.getElementById('app-container');
    const loginForm = document.getElementById('login-form');
    
    const pages = document.querySelectorAll('.page');
    const navLinks = document.querySelectorAll('.nav-link');

    // Dashboard elements
    const timeEl = document.getElementById('current-time');
    const totalVehiclesEl = document.getElementById('total-vehicles');
    const laneStatusEl = document.getElementById('lane-active-status');
    const laneACard = document.getElementById('lane-A-card');
    const laneAVehiclesEl = document.getElementById('lane-A-count');
    const laneATimerEl = document.getElementById('lane-A-timer');
    const laneAProgressEl = document.getElementById('lane-A-progress');
    const laneBCard = document.getElementById('lane-B-card');
    const laneBVehiclesEl = document.getElementById('lane-B-count');
    const laneBTimerEl = document.getElementById('lane-B-timer');
    const laneBProgressEl = document.getElementById('lane-B-progress');
    const redLight = document.getElementById('light-red');
    const yellowLight = document.getElementById('light-yellow');
    const greenLight = document.getElementById('light-green');
    const startWebcamBtn = document.getElementById('start-webcam-btn');
    const startPrerecordedBtn = document.getElementById('start-prerecorded-btn');

    // --- State Management ---
    let dashboardState = {
        activeLane: 'A',
        lightColor: 'green',
        countdown: 0,
        initialDuration: 0,
        latestData: null,
        analysisStarted: false,
        intervals: {
            dataFetch: null,
            cycle: null,
            clock: null,
        }
    };
    
    // --- Page Navigation & Control ---
    function showPage(pageIdToShow) {
        pages.forEach(page => {
            if (page.id === pageIdToShow) {
                page.classList.remove('hidden');
                page.style.animation = 'page-fade-in 0.5s ease-out forwards';
            } else {
                if (!page.classList.contains('hidden')) {
                     page.style.animation = 'page-fade-out 0.5s ease-in forwards';
                     setTimeout(() => page.classList.add('hidden'), 500);
                }
            }
        });

        if (pageIdToShow === 'dashboard-page') {
            startDashboard();
        } else {
            stopDashboard();
        }

        navLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === `#${pageIdToShow.replace('-page', '')}`);
        });
    }
    
    function handleLogin(e) {
        e.preventDefault();
        loadingOverlay.classList.remove('hidden');
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
            loginPage.style.animation = 'page-fade-out 0.5s ease-in forwards';
            setTimeout(() => {
                loginPage.classList.add('hidden');
                appContainer.classList.remove('hidden');
                showPage('home-page');
            }, 500);
        }, 2000); 
    }

    // --- Dashboard Specific Logic ---
    function startDashboard() {
        if (dashboardState.intervals.clock) return;
        updateClock(); 
        dashboardState.intervals.clock = setInterval(updateClock, 1000);
    }

    function stopDashboard() {
        if (!dashboardState.intervals.clock) return;
        Object.keys(dashboardState.intervals).forEach(key => {
            clearInterval(dashboardState.intervals[key]);
            dashboardState.intervals[key] = null;
        });
        laneStatusEl.textContent = 'Waiting for source...';
        totalVehiclesEl.textContent = 'Total Vehicles: 0';
        dashboardState.analysisStarted = false;
    }
    
    function updateClock() {
        timeEl.textContent = new Date().toLocaleTimeString('en-US');
    }

    async function startAnalysis(source) {
        clearInterval(dashboardState.intervals.dataFetch);
        clearInterval(dashboardState.intervals.cycle);
        
        console.log(`Requesting analysis with source: ${source}`);
        laneStatusEl.textContent = 'Initializing analysis...';
        
        try {
            const response = await fetch(START_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: source })
            });
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            
            console.log(await response.json());
            dashboardState.analysisStarted = true;
            await fetchTrafficData(); 
            
            dashboardState.intervals.dataFetch = setInterval(fetchTrafficData, 5000);
            dashboardState.intervals.cycle = setInterval(runTrafficCycle, 1000);

        } catch (error) {
            console.error('Error starting analysis:', error);
            laneStatusEl.textContent = 'Failed to start analysis.';
            dashboardState.analysisStarted = false;
        }
    }

    async function fetchTrafficData() {
        if (!dashboardState.analysisStarted) return;
        try {
            const response = await fetch(DATA_API_URL);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            dashboardState.latestData = data;

            totalVehiclesEl.textContent = `Total Vehicles: ${data.total_vehicles}`;
            laneAVehiclesEl.textContent = `${data.lane_A.vehicle_count} Vehicles`;
            laneATimerEl.textContent = `Green Allotted: ${data.lane_A.green_light_duration}s`;
            laneBVehiclesEl.textContent = `${data.lane_B.vehicle_count} Vehicles`;
            laneBTimerEl.textContent = `Green Allotted: ${data.lane_B.green_light_duration}s`;
            
        } catch (error) {
            console.error("Failed to fetch traffic data:", error);
        }
    }
    
    function runTrafficCycle() {
        if (!dashboardState.analysisStarted || !dashboardState.latestData) return;

        if (dashboardState.countdown <= 0) {
            if (dashboardState.lightColor === 'green') {
                dashboardState.lightColor = 'yellow';
                dashboardState.countdown = YELLOW_LIGHT_DURATION;
                dashboardState.initialDuration = YELLOW_LIGHT_DURATION;
            } else if (dashboardState.lightColor === 'yellow') {
                dashboardState.activeLane = dashboardState.activeLane === 'A' ? 'B' : 'A';
                dashboardState.lightColor = 'green';
                
                const newDuration = (dashboardState.activeLane === 'A')
                    ? dashboardState.latestData.lane_A.green_light_duration
                    : dashboardState.latestData.lane_B.green_light_duration;
                    
                dashboardState.countdown = newDuration;
                dashboardState.initialDuration = newDuration || 10;
            }
        }
        updateVisuals();
        dashboardState.countdown--;
    }

    function updateVisuals() {
        if (!dashboardState.analysisStarted) return;
        const colorName = dashboardState.lightColor.charAt(0).toUpperCase() + dashboardState.lightColor.slice(1);
        laneStatusEl.textContent = `Lane ${dashboardState.activeLane}: ${colorName} (${dashboardState.countdown}s)`;
        redLight.classList.toggle('red', dashboardState.lightColor === 'red');
        yellowLight.classList.toggle('yellow', dashboardState.lightColor === 'yellow');
        greenLight.classList.toggle('green', dashboardState.lightColor === 'green');
        laneACard.classList.toggle('active-lane', dashboardState.activeLane === 'A' && dashboardState.lightColor === 'green');
        laneBCard.classList.toggle('active-lane', dashboardState.activeLane === 'B' && dashboardState.lightColor === 'green');

        let progressPercent = 0;
        if (dashboardState.lightColor === 'green' && dashboardState.initialDuration > 0) {
             progressPercent = (dashboardState.countdown / dashboardState.initialDuration) * 100;
        }
        if (dashboardState.activeLane === 'A') {
            laneAProgressEl.style.width = `${progressPercent}%`;
            laneBProgressEl.style.width = '0%';
        } else {
            laneBProgressEl.style.width = `${progressPercent}%`;
            laneAProgressEl.style.width = '0%';
        }
    }

    // --- Initializations & Event Listeners ---
    loginForm.addEventListener('submit', handleLogin);

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = e.target.getAttribute('href').substring(1) + '-page';
            showPage(targetId);
        });
    });

    startWebcamBtn.onclick = () => startAnalysis('webcam');
    startPrerecordedBtn.onclick = () => startAnalysis('prerecorded');
});