const form = document.getElementById("weather-form");
const cityInput = document.getElementById("city");
const resultNode = document.getElementById("result");
const submitBtn = document.getElementById("submit-btn");
const weatherCard = document.getElementById("weather-card");
const weatherCity = document.getElementById("w-city");
const weatherText = document.getElementById("w-text");
const weatherTemp = document.getElementById("w-temp");
const weatherHumidity = document.getElementById("w-humidity");
const weatherWind = document.getElementById("w-wind");
const weatherTime = document.getElementById("w-time");

function resetWeatherCard() {
  weatherCard.classList.add("hidden");
  weatherCity.textContent = "-";
  weatherText.textContent = "-";
  weatherTemp.textContent = "-";
  weatherHumidity.textContent = "-";
  weatherWind.textContent = "-";
  weatherTime.textContent = "-";
}

function renderWeatherCard(weather) {
  if (!weather) {
    resetWeatherCard();
    return;
  }

  weatherCard.classList.remove("hidden");
  weatherCity.textContent = [weather.resolved_name, weather.country].filter(Boolean).join(", ") || weather.city || "-";
  weatherText.textContent = weather.weather_text || "-";
  weatherTemp.textContent = weather.temperature_c != null ? `${weather.temperature_c} °C` : "-";
  weatherHumidity.textContent = weather.humidity_percent != null ? `${weather.humidity_percent} %` : "-";
  weatherWind.textContent = weather.wind_speed_kmh != null ? `${weather.wind_speed_kmh} km/h` : "-";
  weatherTime.textContent = weather.observation_time || "-";
}

resetWeatherCard();

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const city = cityInput.value.trim();
  if (!city) {
    resultNode.textContent = "请输入城市名";
    return;
  }

  submitBtn.disabled = true;
  resultNode.textContent = "查询中，请稍候...";
  resetWeatherCard();

  try {
    const response = await fetch("/api/weather-agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city }),
    });

    const data = await response.json();
    if (!response.ok) {
      resultNode.textContent = data.detail || "查询失败";
      return;
    }

    renderWeatherCard(data.weather);
    resultNode.textContent = data.reply || "未返回结果";
  } catch (error) {
    resultNode.textContent = `请求异常: ${error}`;
  } finally {
    submitBtn.disabled = false;
  }
});
