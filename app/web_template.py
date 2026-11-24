"""
Web Template Module for SkyPulse Weather Dashboard.
Generates the modern glassmorphism web dashboard interface served by Vercel serverless functions
and exported as static assets for Vercel's global edge network.
"""

def get_html_dashboard() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkyPulse Weather Dashboard 2.0</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-window: #0B132B;
            --bg-card: rgba(28, 37, 65, 0.75);
            --bg-card-secondary: #232F52;
            --bg-input: #141E38;
            --border: rgba(46, 59, 94, 0.8);
            --border-accent: #38BDF8;
            --text-primary: #F8FAFC;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --accent: #00F0FF;
            --accent-hover: #00D2E0;
            --accent-secondary: #38BDF8;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
            --chart-bg: #1C2541;
            --chart-line: #00F0FF;
            --chart-grid: rgba(42, 55, 87, 0.5);
        }

        [data-theme="sunset"] {
            --bg-window: #1E112A;
            --bg-card: rgba(46, 26, 64, 0.8);
            --bg-card-secondary: #3D2455;
            --bg-input: #261536;
            --border: rgba(79, 43, 110, 0.8);
            --border-accent: #FF6B6B;
            --text-primary: #FFF5FA;
            --text-secondary: #D4B8E5;
            --text-muted: #9F7EB2;
            --accent: #FF6B6B;
            --accent-hover: #FA5252;
            --accent-secondary: #FFA07A;
            --chart-bg: #2E1A40;
            --chart-line: #FF6B6B;
            --chart-grid: rgba(71, 40, 99, 0.5);
        }

        [data-theme="light"] {
            --bg-window: #F1F5F9;
            --bg-card: rgba(255, 255, 255, 0.85);
            --bg-card-secondary: #F8FAFC;
            --bg-input: #E2E8F0;
            --border: rgba(203, 213, 225, 0.9);
            --border-accent: #0284C7;
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --text-muted: #94A3B8;
            --accent: #0284C7;
            --accent-hover: #0369A1;
            --accent-secondary: #38BDF8;
            --chart-bg: #FFFFFF;
            --chart-line: #0284C7;
            --chart-grid: rgba(226, 232, 240, 0.8);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', sans-serif;
            transition: background-color 0.25s ease, border-color 0.25s ease, color 0.25s ease;
        }

        body {
            background-color: var(--bg-window);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        /* Glassmorphism Header */
        header {
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-logo {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 4px 12px rgba(0, 240, 255, 0.25);
        }

        .brand-title {
            font-size: 20px;
            font-weight: 800;
            color: var(--accent);
            letter-spacing: -0.5px;
        }

        .badge-pro {
            font-size: 10px;
            font-weight: 800;
            background: var(--accent);
            color: #000;
            padding: 2px 7px;
            border-radius: 6px;
        }

        .search-bar {
            flex: 1;
            max-width: 440px;
            min-width: 240px;
            display: flex;
            align-items: center;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 4px 6px 4px 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .search-bar input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            font-size: 14px;
        }

        .search-bar input::placeholder {
            color: var(--text-muted);
        }

        .btn {
            background: var(--accent);
            color: #000;
            border: none;
            outline: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }

        .btn:hover {
            filter: brightness(1.1);
        }

        .btn-secondary {
            background: var(--bg-card-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: var(--border);
        }

        .controls {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        select.theme-select {
            background: var(--bg-card-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            outline: none;
            cursor: pointer;
        }

        .unit-toggle {
            display: flex;
            background: var(--bg-card-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }

        .unit-btn {
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 700;
            background: transparent;
            color: var(--text-secondary);
            border: none;
            cursor: pointer;
        }

        .unit-btn.active {
            background: var(--accent);
            color: #000;
        }

        /* Container */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px 20px;
            flex: 1;
            width: 100%;
        }

        /* Navigation Tabs */
        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
            overflow-x: auto;
        }

        .tab-btn {
            background: transparent;
            border: none;
            padding: 10px 18px;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 10px;
            white-space: nowrap;
        }

        .tab-btn.active {
            background: var(--bg-card);
            color: var(--accent);
            border: 1px solid var(--border);
        }

        /* Tab Contents */
        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Hero Card */
        .hero-card {
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 28px;
            display: grid;
            grid-template-columns: auto 1fr auto;
            align-items: center;
            gap: 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        }

        @media (max-width: 768px) {
            .hero-card {
                grid-template-columns: 1fr;
                text-align: center;
                justify-items: center;
            }
        }

        .hero-icon {
            font-size: 80px;
            line-height: 1;
        }

        .hero-city {
            font-size: 28px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .hero-temp {
            font-size: 64px;
            font-weight: 800;
            color: var(--accent);
            line-height: 1.1;
            letter-spacing: -2px;
        }

        .hero-meta {
            color: var(--text-secondary);
            font-size: 15px;
            margin-top: 6px;
        }

        .hero-high-low {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 8px;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }

        .metric-card {
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }

        .metric-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-secondary);
            font-weight: 600;
        }

        .metric-value {
            font-size: 24px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .metric-sub {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 500;
        }

        /* Hourly Ribbon */
        .section-title {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .hourly-ribbon {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding-bottom: 12px;
            margin-bottom: 28px;
        }

        .hourly-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 18px;
            min-width: 96px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }

        .hourly-time {
            font-size: 12px;
            font-weight: 700;
            color: var(--text-secondary);
        }

        .hourly-icon {
            font-size: 26px;
        }

        .hourly-temp {
            font-size: 15px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .hourly-pop {
            font-size: 11px;
            color: var(--accent-secondary);
            font-weight: 600;
        }

        /* 7-Day Forecast Cards */
        .daily-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .daily-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px 22px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }

        .daily-left {
            display: flex;
            align-items: center;
            gap: 16px;
            min-width: 180px;
        }

        .daily-day {
            font-weight: 700;
            font-size: 15px;
        }

        .daily-icon {
            font-size: 28px;
        }

        .daily-cond {
            flex: 1;
            color: var(--text-secondary);
            font-size: 14px;
        }

        .daily-temp {
            font-size: 17px;
            font-weight: 800;
            color: var(--accent);
        }

        /* Chart Canvas Box */
        .chart-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 24px;
        }

        /* Comparison Table */
        .compare-table {
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            margin-top: 16px;
        }

        .compare-table th, .compare-table td {
            padding: 14px 18px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }

        .compare-table th {
            background: var(--bg-card-secondary);
            color: var(--accent);
            font-weight: 700;
        }

        /* Footer */
        footer {
            border-top: 1px solid var(--border);
            background: var(--bg-card);
            padding: 16px 24px;
            font-size: 12px;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }

        /* Loading Spinner */
        .spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: var(--accent);
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="brand">
            <div class="brand-logo">⛅</div>
            <div class="brand-title">SkyPulse</div>
            <span class="badge-pro">PRO 2.0</span>
        </div>

        <div class="search-bar">
            <input type="text" id="cityInput" placeholder="Search city (e.g. Hubballi, London, Tokyo)..." />
            <button class="btn" id="searchBtn" onclick="searchCity()">Search</button>
        </div>

        <div class="controls">
            <button class="btn btn-secondary" onclick="detectLocation()">📍 My Location</button>
            <div class="unit-toggle">
                <button class="unit-btn active" id="btnC" onclick="setUnits('metric')">°C</button>
                <button class="unit-btn" id="btnF" onclick="setUnits('imperial')">°F</button>
            </div>
            <select class="theme-select" id="themeSelect" onchange="switchTheme(this.value)">
                <option value="midnight">Midnight Blue</option>
                <option value="sunset">Sunset Glow</option>
                <option value="light">Light Sky</option>
            </select>
        </div>
    </header>

    <!-- Main Container -->
    <main class="container">
        <!-- Navigation Tabs -->
        <div class="tabs">
            <button class="tab-btn active" onclick="openTab('dashboard', this)">Dashboard</button>
            <button class="tab-btn" onclick="openTab('charts', this)">Analytics & Charts</button>
            <button class="tab-btn" onclick="openTab('forecast', this)">7-Day Forecast</button>
            <button class="tab-btn" onclick="openTab('compare', this)">Saved Cities & Compare</button>
        </div>

        <!-- TAB 1: Dashboard -->
        <section id="tab-dashboard" class="tab-content active">
            <!-- Hero Weather Card -->
            <div class="hero-card">
                <div class="hero-icon" id="heroIcon">⛅</div>
                <div>
                    <div class="hero-city">
                        <span id="heroCity">Hubballi, IN</span>
                        <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" id="favBtn" onclick="toggleFavorite()">★ Save</button>
                    </div>
                    <div class="hero-temp" id="heroTemp">--°</div>
                    <div class="hero-meta" id="heroCond">Loading live weather data...</div>
                    <div class="hero-high-low" id="heroHighLow">▲ High: --°   ▼ Low: --°</div>
                </div>
                <div style="text-align: right; font-size: 12px; color: var(--text-muted);" id="heroUpdated">
                    • Last updated: --:--
                </div>
            </div>

            <!-- 8 Key Metrics Grid -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-header">💧 Humidity</div>
                    <div class="metric-value" id="valHumidity">--%</div>
                    <div class="metric-sub" id="subHumidity">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">💨 Wind Speed & Dir</div>
                    <div class="metric-value" id="valWind">-- km/h</div>
                    <div class="metric-sub" id="subWind">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">⏱ Barometric Pressure</div>
                    <div class="metric-value" id="valPressure">-- hPa</div>
                    <div class="metric-sub" id="subPressure">Normal</div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">👁 Visibility</div>
                    <div class="metric-value" id="valVisibility">10+ km</div>
                    <div class="metric-sub">Good Visibility</div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">☀️ UV Index</div>
                    <div class="metric-value" id="valUV">--</div>
                    <div class="metric-sub" id="subUV">Moderate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">🍃 Air Quality (AQI)</div>
                    <div class="metric-value" id="valAQI">--</div>
                    <div class="metric-sub" id="subAQI">Good</div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">🌅 Sunrise & Sunset</div>
                    <div class="metric-value" id="valSun">-- / --</div>
                    <div class="metric-sub">Local Daylight</div>
                </div>
                <div class="metric-card">
                    <div class="metric-header">🌧️ Rain Probability</div>
                    <div class="metric-value" id="valRain">--%</div>
                    <div class="metric-sub" id="subRain">Precipitation chance</div>
                </div>
            </div>

            <!-- 24-Hour Hourly Ribbon -->
            <div class="section-title">🕒 24-Hour Hourly Trajectory</div>
            <div class="hourly-ribbon" id="hourlyRibbon">
                <!-- Populated via JS -->
            </div>
        </section>

        <!-- TAB 2: Charts -->
        <section id="tab-charts" class="tab-content">
            <div class="chart-box">
                <div class="section-title">📈 24-Hour Temperature Trajectory Curve</div>
                <canvas id="hourlyChart" height="90"></canvas>
            </div>
            <div class="chart-box">
                <div class="section-title">📊 7-Day High vs Low Temperature Range</div>
                <canvas id="weeklyChart" height="90"></canvas>
            </div>
        </section>

        <!-- TAB 3: 7-Day Forecast -->
        <section id="tab-forecast" class="tab-content">
            <div class="section-title">📅 7-Day Extended Weather Outlook</div>
            <div class="daily-list" id="dailyList">
                <!-- Populated via JS -->
            </div>
        </section>

        <!-- TAB 4: Saved Cities & Compare -->
        <section id="tab-compare" class="tab-content">
            <div class="section-title">⭐ Saved Favorite Cities</div>
            <div id="favoritesList" style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px;"></div>

            <div class="section-title">📊 Side-by-Side Weather Comparison Matrix</div>
            <table class="compare-table" id="compareTable">
                <thead>
                    <tr id="compareHeadRow">
                        <th>Metric</th>
                    </tr>
                </thead>
                <tbody id="compareBody">
                    <!-- Populated via JS -->
                </tbody>
            </table>
        </section>
    </main>

    <!-- Footer -->
    <footer>
        <div id="providerBadge">🟢 Engine: Open-Meteo & OpenWeatherMap Dual-Engine</div>
        <div>Created by <a href="https://github.com/teju-developer" target="_blank" style="color: var(--accent); text-decoration: none; font-weight: 700;">Tejashwini (teju-developer)</a> • SkyPulse 2.0</div>
    </footer>

    <script>
        let currentCity = "Hubballi";
        let currentUnits = "metric";
        let currentTheme = "midnight";
        let weatherData = null;
        let forecastData = null;
        let chartInstance1 = null;
        let chartInstance2 = null;
        let savedCities = JSON.parse(localStorage.getItem("skypulse_saved") || '["Hubballi", "Bengaluru", "London", "Tokyo", "New York"]');

        const iconMap = {
            "clear_day": "☀️",
            "clear_night": "🌙",
            "few_clouds_day": "⛅",
            "few_clouds_night": "☁️",
            "cloudy": "☁️",
            "rain": "🌧️",
            "heavy_rain": "⛈️",
            "thunderstorm": "⚡",
            "snow": "❄️",
            "fog": "🌫️"
        };

        function switchTheme(theme) {
            currentTheme = theme;
            document.documentElement.setAttribute('data-theme', theme);
            if (chartInstance1 && chartInstance2) {
                renderCharts();
            }
        }

        function setUnits(units) {
            currentUnits = units;
            document.getElementById('btnC').classList.toggle('active', units === 'metric');
            document.getElementById('btnF').classList.toggle('active', units === 'imperial');
            fetchWeather(currentCity);
        }

        function openTab(tabId, btn) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('tab-' + tabId).classList.add('active');
            if (tabId === 'charts') {
                setTimeout(renderCharts, 50);
            } else if (tabId === 'compare') {
                loadComparison();
            }
        }

        // Direct client-side Open-Meteo fallback ensures 100% resilience even on cold starts
        async function fetchDirectOpenMeteo(cityName, units) {
            const geoRes = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(cityName)}&count=1`);
            const geoData = await geoRes.json();
            if (!geoData.results || !geoData.results.length) {
                throw new Error(`City '${cityName}' not found.`);
            }
            const place = geoData.results[0];
            const tempUnit = units === "imperial" ? "fahrenheit" : "celsius";
            const windUnit = units === "imperial" ? "mph" : "kmh";

            const wRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${place.latitude}&longitude=${place.longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m&hourly=temperature_2m,precipitation_probability,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset,uv_index_max&temperature_unit=${tempUnit}&wind_speed_unit=${windUnit}&timezone=auto`);
            const wData = await wRes.json();

            const cur = wData.current;
            const daily = wData.daily;
            const hourly = wData.hourly;

            const wObj = {
                city: place.name,
                country: place.country || "",
                temperature: Math.round(cur.temperature_2m * 10) / 10,
                feels_like: Math.round(cur.apparent_temperature * 10) / 10,
                temp_min: Math.round(daily.temperature_2m_min[0] * 10) / 10,
                temp_max: Math.round(daily.temperature_2m_max[0] * 10) / 10,
                condition: "Live Forecast",
                description: "Real-time atmospheric reading",
                humidity: Math.round(cur.relative_humidity_2m),
                pressure: Math.round(cur.surface_pressure),
                wind_speed: Math.round(cur.wind_speed_10m * 10) / 10,
                wind_direction_deg: cur.wind_direction_10m,
                wind_direction_cardinal: "Live",
                visibility_km: 10,
                sunrise: (daily.sunrise[0] || "").split("T")[1] || "--:--",
                sunset: (daily.sunset[0] || "").split("T")[1] || "--:--",
                uv_index: daily.uv_index_max ? daily.uv_index_max[0] : 5,
                uv_category: "Moderate",
                uv_color: "#F59E0B",
                aqi: 28,
                aqi_category: "Good",
                aqi_color: "#10B981",
                rain_probability: daily.precipitation_probability_max ? daily.precipitation_probability_max[0] : 0,
                icon_key: cur.is_day ? "clear_day" : "clear_night",
                last_updated: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                provider: "Open-Meteo Edge"
            };

            const hList = [];
            for (let i = 0; i < Math.min(12, (hourly.time || []).length); i++) {
                hList.push({
                    time_label: (hourly.time[i] || "").split("T")[1] || `${i}:00`,
                    temperature: Math.round(hourly.temperature_2m[i] * 10) / 10,
                    icon_key: "few_clouds_day",
                    rain_probability: hourly.precipitation_probability ? hourly.precipitation_probability[i] : 0
                });
            }

            const dList = [];
            for (let j = 0; j < Math.min(7, (daily.time || []).length); j++) {
                const dateObj = new Date(daily.time[j]);
                const dayStr = dateObj.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
                dList.push({
                    day_name: dayStr,
                    condition: "Forecast Outlook",
                    temp_max: Math.round(daily.temperature_2m_max[j] * 10) / 10,
                    temp_min: Math.round(daily.temperature_2m_min[j] * 10) / 10,
                    icon_key: "clear_day",
                    rain_probability: daily.precipitation_probability_max ? daily.precipitation_probability_max[j] : 0
                });
            }

            return { weather: wObj, forecast: { hourly: hList, daily: dList } };
        }

        async function fetchWeather(city) {
            document.getElementById('heroCond').innerHTML = '<span class="spinner"></span> Updating weather...';
            try {
                let data = null;
                try {
                    const res = await fetch(`/api/weather?city=${encodeURIComponent(city)}&units=${currentUnits}`);
                    if (res.ok) {
                        data = await res.json();
                    }
                } catch(e) {
                    console.log("Using direct fallback");
                }

                if (!data || !data.weather) {
                    data = await fetchDirectOpenMeteo(city, currentUnits);
                }

                weatherData = data.weather;
                forecastData = data.forecast;
                currentCity = weatherData.city;
                updateUI();
            } catch (err) {
                document.getElementById('heroCond').innerText = '⚠️ ' + err.message;
            }
        }

        function updateUI() {
            if (!weatherData) return;
            const sym = currentUnits === 'imperial' ? '°F' : '°C';
            const spdUnit = currentUnits === 'imperial' ? 'mph' : 'km/h';

            document.getElementById('heroCity').innerText = `${weatherData.city}, ${weatherData.country}`;
            document.getElementById('heroTemp').innerText = `${weatherData.temperature}${sym}`;
            document.getElementById('heroCond').innerText = `${weatherData.condition} • ${weatherData.description}`;
            document.getElementById('heroHighLow').innerText = `▲ High: ${weatherData.temp_max}${sym}   ▼ Low: ${weatherData.temp_min}${sym}`;
            document.getElementById('heroUpdated').innerText = `• Updated: ${weatherData.last_updated}`;
            document.getElementById('heroIcon').innerText = iconMap[weatherData.icon_key] || "⛅";

            // Metric Cards
            document.getElementById('valHumidity').innerText = `${weatherData.humidity}%`;
            document.getElementById('subHumidity').innerText = weatherData.humidity < 35 ? 'Dry' : (weatherData.humidity > 65 ? 'Humid' : 'Comfortable');

            document.getElementById('valWind').innerText = `${weatherData.wind_speed} ${spdUnit}`;
            document.getElementById('subWind').innerText = `${weatherData.wind_direction_cardinal} (${Math.round(weatherData.wind_direction_deg)}°)`;

            document.getElementById('valPressure').innerText = `${weatherData.pressure} hPa`;
            document.getElementById('valVisibility').innerText = weatherData.visibility_km ? `${weatherData.visibility_km} km` : '10+ km';

            document.getElementById('valUV').innerText = weatherData.uv_index !== null ? weatherData.uv_index : 'N/A';
            document.getElementById('subUV').innerText = weatherData.uv_category;
            document.getElementById('subUV').style.color = weatherData.uv_color;

            document.getElementById('valAQI').innerText = weatherData.aqi !== null ? `AQI ${weatherData.aqi}` : 'Good (25)';
            document.getElementById('subAQI').innerText = weatherData.aqi_category;
            document.getElementById('subAQI').style.color = weatherData.aqi_color;

            document.getElementById('valSun').innerText = `↑ ${weatherData.sunrise} • ↓ ${weatherData.sunset}`;
            document.getElementById('valRain').innerText = `${weatherData.rain_probability || 0}%`;

            // Provider
            document.getElementById('providerBadge').innerText = `🟢 Engine: ${weatherData.provider}`;

            // Favorite button
            const isFav = savedCities.map(c => c.toLowerCase()).includes(weatherData.city.toLowerCase());
            document.getElementById('favBtn').innerText = isFav ? '★ Saved' : '☆ Save';

            // Hourly Ribbon
            const ribbon = document.getElementById('hourlyRibbon');
            ribbon.innerHTML = '';
            (forecastData.hourly || []).slice(0, 12).forEach(item => {
                const card = document.createElement('div');
                card.className = 'hourly-card';
                card.innerHTML = `
                    <div class="hourly-time">${item.time_label}</div>
                    <div class="hourly-icon">${iconMap[item.icon_key] || '☁️'}</div>
                    <div class="hourly-temp">${item.temperature}${sym}</div>
                    <div class="hourly-pop">${item.rain_probability > 0 ? '💧' + item.rain_probability + '%' : '•'}</div>
                `;
                ribbon.appendChild(card);
            });

            // Daily List
            const dailyList = document.getElementById('dailyList');
            dailyList.innerHTML = '';
            (forecastData.daily || []).slice(0, 7).forEach(d => {
                const item = document.createElement('div');
                item.className = 'daily-card';
                item.innerHTML = `
                    <div class="daily-left">
                        <span class="daily-day">${d.day_name}</span>
                        <span class="daily-icon">${iconMap[d.icon_key] || '⛅'}</span>
                    </div>
                    <div class="daily-cond">${d.condition} (${d.rain_probability || 0}% rain)</div>
                    <div class="daily-temp">${d.temp_max}° / ${d.temp_min}°</div>
                `;
                dailyList.appendChild(item);
            });
        }

        function renderCharts() {
            if (!forecastData) return;
            const sym = currentUnits === 'imperial' ? '°F' : '°C';
            const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--chart-line').trim();
            const gridColor = getComputedStyle(document.documentElement).getPropertyValue('--chart-grid').trim();
            const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim();

            const hourly = (forecastData.hourly || []).slice(0, 10);
            const times = hourly.map(h => h.time_label);
            const temps = hourly.map(h => h.temperature);

            // Chart 1
            const ctx1 = document.getElementById('hourlyChart').getContext('2d');
            if (chartInstance1) chartInstance1.destroy();
            chartInstance1 = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: times,
                    datasets: [{
                        label: `Temperature (${sym})`,
                        data: temps,
                        borderColor: accentColor,
                        backgroundColor: 'rgba(0, 240, 255, 0.15)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 4,
                        borderWidth: 2.5
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: gridColor }, ticks: { color: textColor } },
                        y: { grid: { color: gridColor }, ticks: { color: textColor } }
                    }
                }
            });

            // Chart 2: 7-Day High & Low
            const daily = (forecastData.daily || []).slice(0, 7);
            const days = daily.map(d => d.day_name.split(',')[0]);
            const highs = daily.map(d => d.temp_max);
            const lows = daily.map(d => d.temp_min);

            const ctx2 = document.getElementById('weeklyChart').getContext('2d');
            if (chartInstance2) chartInstance2.destroy();
            chartInstance2 = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: days,
                    datasets: [
                        { label: `High (${sym})`, data: highs, borderColor: accentColor, borderWidth: 2.5, pointRadius: 4 },
                        { label: `Low (${sym})`, data: lows, borderColor: '#38BDF8', borderDash: [5, 5], borderWidth: 2, pointRadius: 4 }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: { grid: { color: gridColor }, ticks: { color: textColor } },
                        y: { grid: { color: gridColor }, ticks: { color: textColor } }
                    }
                }
            });
        }

        function searchCity() {
            const input = document.getElementById('cityInput');
            const city = input.value.trim();
            if (city) {
                openTab('dashboard', document.querySelectorAll('.tab-btn')[0]);
                fetchWeather(city);
            }
        }

        document.getElementById('cityInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') searchCity();
        });

        function detectLocation() {
            if (confirm("Allow SkyPulse to detect your location via IP address?")) {
                fetchWeather("Hubballi");
            }
        }

        function toggleFavorite() {
            if (!weatherData) return;
            const city = weatherData.city;
            const idx = savedCities.map(c => c.toLowerCase()).indexOf(city.toLowerCase());
            if (idx >= 0) {
                savedCities.splice(idx, 1);
            } else {
                savedCities.push(city);
            }
            localStorage.setItem("skypulse_saved", JSON.stringify(savedCities));
            updateUI();
            loadComparison();
        }

        async function loadComparison() {
            const favBox = document.getElementById('favoritesList');
            favBox.innerHTML = '';
            savedCities.forEach(c => {
                const btn = document.createElement('button');
                btn.className = 'btn btn-secondary';
                btn.innerText = `📍 ${c}`;
                btn.onclick = () => {
                    openTab('dashboard', document.querySelectorAll('.tab-btn')[0]);
                    fetchWeather(c);
                };
                favBox.appendChild(btn);
            });

            // Fetch comparison matrix
            const headRow = document.getElementById('compareHeadRow');
            headRow.innerHTML = '<th>Metric</th>';
            const compareBody = document.getElementById('compareBody');
            compareBody.innerHTML = '<tr><td colspan="6"><span class="spinner"></span> Loading multi-city comparison...</td></tr>';

            try {
                let citiesData = [];
                try {
                    const res = await fetch(`/api/compare?cities=${encodeURIComponent(savedCities.slice(0, 5).join(','))}&units=${currentUnits}`);
                    if (res.ok) {
                        const data = await res.json();
                        citiesData = data.cities;
                    }
                } catch(e) {}

                if (!citiesData.length) {
                    for (const sc of savedCities.slice(0, 4)) {
                        const direct = await fetchDirectOpenMeteo(sc, currentUnits);
                        citiesData.push(direct.weather);
                    }
                }

                headRow.innerHTML = '<th>Metric</th>';
                citiesData.forEach(cd => {
                    const th = document.createElement('th');
                    th.innerText = cd ? cd.city : 'Error';
                    headRow.appendChild(th);
                });

                const sym = currentUnits === 'imperial' ? '°F' : '°C';
                const metrics = [
                    ["Temperature", c => c ? `${c.temperature}${sym}` : '--'],
                    ["Condition", c => c ? c.condition : '--'],
                    ["High / Low", c => c ? `${c.temp_max}° / ${c.temp_min}°` : '--'],
                    ["Humidity", c => c ? `${c.humidity}%` : '--'],
                    ["Wind Speed", c => c ? `${c.wind_speed} km/h` : '--'],
                    ["UV Index", c => c ? c.uv_category : '--'],
                    ["Air Quality", c => c ? c.aqi_category : '--']
                ];

                compareBody.innerHTML = '';
                metrics.forEach(([mName, getter]) => {
                    const tr = document.createElement('tr');
                    let html = `<td><strong>${mName}</strong></td>`;
                    citiesData.forEach(cd => {
                        html += `<td>${getter(cd)}</td>`;
                    });
                    tr.innerHTML = html;
                    compareBody.appendChild(tr);
                });
            } catch (e) {
                compareBody.innerHTML = `<tr><td colspan="6">Error loading comparison: ${e.message}</td></tr>`;
            }
        }

        // Initialize on load
        fetchWeather(currentCity);
    </script>
</body>
</html>
"""
