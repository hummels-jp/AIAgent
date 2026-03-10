const form = document.getElementById("route-form");
const originInput = document.getElementById("origin");
const destinationInput = document.getElementById("destination");
const replyNode = document.getElementById("agent-reply");
const routeListNode = document.getElementById("route-list");
const submitBtn = document.getElementById("submit-btn");
const dataSourceNode = document.getElementById("data-source");
const mapLocateInput = document.getElementById("map-locate-input");
const mapLocateBtn = document.getElementById("map-locate-btn");

const appConfig = window.APP_CONFIG || {};
const mapboxApiKey = appConfig.mapboxApiKey || "";
const mapillaryApiKey = appConfig.mapillaryApiKey || "";

let map;
let polylines = [];
let markers = [];
let currentRoutes = [];
let routePaths = [];
let selectedRouteIndex = 0;
let pickedOriginMarker = null;
let pickedDestinationMarker = null;
let locateMarker = null;

const colors = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ea580c"];

function updateDataSourceBadge(text) {
  dataSourceNode.textContent = `数据来源：${text}`;
}

function formatLatLng(latlng) {
  return `${latlng.lat.toFixed(6)},${latlng.lng.toFixed(6)}`;
}

function setPointAsEndpoint(kind, latlng) {
  const value = formatLatLng(latlng);
  const markerTitle = kind === "origin" ? "起点(鼠标)" : "终点(鼠标)";
  const markerLabel = kind === "origin" ? "起" : "终";

  if (kind === "origin") {
    originInput.value = value;
    if (pickedOriginMarker) {
      pickedOriginMarker.setLatLng(latlng);
    } else {
      pickedOriginMarker = L.marker(latlng, { title: markerTitle }).addTo(map);
      pickedOriginMarker.bindTooltip(markerLabel, { permanent: true, direction: "top", offset: [0, -10] });
    }
  } else {
    destinationInput.value = value;
    if (pickedDestinationMarker) {
      pickedDestinationMarker.setLatLng(latlng);
    } else {
      pickedDestinationMarker = L.marker(latlng, { title: markerTitle }).addTo(map);
      pickedDestinationMarker.bindTooltip(markerLabel, { permanent: true, direction: "top", offset: [0, -10] });
    }
  }

  map.closePopup();
  autoSubmitIfReady();
}

function clearUserPlacedMarkers() {
  if (pickedOriginMarker) {
    map.removeLayer(pickedOriginMarker);
    pickedOriginMarker = null;
  }
  if (pickedDestinationMarker) {
    map.removeLayer(pickedDestinationMarker);
    pickedDestinationMarker = null;
  }
  if (locateMarker) {
    map.removeLayer(locateMarker);
    locateMarker = null;
  }
}

function autoSubmitIfReady() {
  const origin = originInput.value.trim();
  const destination = destinationInput.value.trim();
  if (!origin || !destination) return;
  if (submitBtn.disabled) return;

  updateDataSourceBadge("起终点已设置，自动计算中");
  form.requestSubmit();
}

async function geocodeAddress(query) {
  if (!query) return null;

  if (mapboxApiKey) {
    const mapboxUrl = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${encodeURIComponent(
      mapboxApiKey
    )}&limit=1&language=zh`;
    const res = await fetch(mapboxUrl);
    if (res.ok) {
      const data = await res.json();
      const feature = (data.features || [])[0];
      if (feature && Array.isArray(feature.center) && feature.center.length === 2) {
        return { lat: feature.center[1], lng: feature.center[0], label: feature.place_name || query };
      }
    }
  }

  const nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`;
  const res = await fetch(nominatimUrl, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return null;
  const data = await res.json();
  const item = (data || [])[0];
  if (!item) return null;
  return {
    lat: Number(item.lat),
    lng: Number(item.lon),
    label: item.display_name || query,
  };
}

async function locateMapByAddress() {
  const query = mapLocateInput.value.trim();
  if (!query) {
    updateDataSourceBadge("请输入定位地址");
    return;
  }

  mapLocateBtn.disabled = true;
  const oldText = mapLocateBtn.textContent;
  mapLocateBtn.textContent = "定位中...";

  try {
    const point = await geocodeAddress(query);
    if (!point || Number.isNaN(point.lat) || Number.isNaN(point.lng)) {
      updateDataSourceBadge("定位失败：未找到地址");
      return;
    }

    const latlng = { lat: point.lat, lng: point.lng };
    map.setView(latlng, 15, { animate: true });

    if (locateMarker) {
      locateMarker.setLatLng(latlng);
      locateMarker.bindTooltip(`定位: ${point.label}`, { direction: "top", offset: [0, -10] });
    } else {
      locateMarker = L.marker(latlng, { title: "定位点" }).addTo(map);
      locateMarker.bindTooltip(`定位: ${point.label}`, { direction: "top", offset: [0, -10] });
    }
    locateMarker.openTooltip();
    updateDataSourceBadge("地址定位成功");
  } catch (error) {
    updateDataSourceBadge(`定位异常: ${error}`);
  } finally {
    mapLocateBtn.disabled = false;
    mapLocateBtn.textContent = oldText;
  }
}

function clearMapObjects() {
  polylines.forEach((line) => map.removeLayer(line));
  markers.forEach((marker) => map.removeLayer(marker));
  polylines = [];
  markers = [];
  routePaths = [];
}

function decodePolyline(encoded) {
  if (!encoded || typeof encoded !== "string") return [];

  let index = 0;
  let lat = 0;
  let lng = 0;
  const coordinates = [];

  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    coordinates.push([lat / 1e5, lng / 1e5]);
  }

  return coordinates;
}

function renderRouteList(routes) {
  if (!routes || routes.length === 0) {
    routeListNode.textContent = "暂无路线";
    return;
  }

  routeListNode.innerHTML = routes
    .map((route, idx) => {
      const transitLines = route.steps
        .filter((step) => step.mode === "TRANSIT" && step.transit)
        .map((step) => `${step.transit.vehicle_name || "交通"} ${step.transit.line_name || ""}`.trim())
        .join(" → ");

      return `
        <article class="route-card ${idx === selectedRouteIndex ? "active" : ""}" data-route-index="${idx}">
          <h3>方案 ${idx + 1}：${route.summary || "公交地铁换乘"}</h3>
          <div class="meta">时长：${route.duration_text || "-"} ｜ 距离：${route.distance_text || "-"} ｜ 票价：${route.fare || "未知"}</div>
          <div class="meta">出发：${route.start_address || "-"}</div>
          <div class="meta">到达：${route.end_address || "-"}</div>
          <div class="lines">线路：${transitLines || "请查看地图与步骤"}</div>
          <a class="route-link" href="/static/route-detail.html" data-route-index="${idx}" target="_blank" rel="noopener noreferrer">查看地图与线路详情</a>
        </article>
      `;
    })
    .join("");
}

function openRouteDetail(index) {
  const route = currentRoutes[index];
  if (!route) return;

  const key = `route-detail-${Date.now()}-${index}`;
  const payload = {
    index,
    route,
    source: dataSourceNode.textContent || "",
    mapillaryApiKey,
    query: {
      origin: originInput.value.trim(),
      destination: destinationInput.value.trim(),
    },
  };

  try {
    localStorage.setItem(key, JSON.stringify(payload));
  } catch (error) {
    alert(`无法保存路线详情数据：${error}`);
    return;
  }

  const url = `/static/route-detail.html?key=${encodeURIComponent(key)}`;
  window.open(url, "_blank", "noopener,noreferrer");
}

function renderRouteMarkers(route) {
  markers.forEach((marker) => map.removeLayer(marker));
  markers = [];

  if (!route || !route.steps || route.steps.length === 0) return;
  const firstStep = route.steps[0];
  const lastStep = route.steps[route.steps.length - 1];

  if (firstStep.polyline) {
    const startPath = decodePolyline(firstStep.polyline);
    if (startPath.length > 0) {
      const marker = L.marker(startPath[0], { title: "起点" });
      marker.bindTooltip("起", { permanent: true, direction: "top", offset: [0, -10] });
      marker.addTo(map);
      markers.push(marker);
    }
  }

  if (lastStep.polyline) {
    const endPath = decodePolyline(lastStep.polyline);
    if (endPath.length > 0) {
      const marker = L.marker(endPath[endPath.length - 1], { title: "终点" });
      marker.bindTooltip("终", { permanent: true, direction: "top", offset: [0, -10] });
      marker.addTo(map);
      markers.push(marker);
    }
  }
}

function applyRouteSelection(index, shouldFitBounds = false) {
  if (!currentRoutes.length || !polylines.length) return;

  selectedRouteIndex = index;
  polylines.forEach((line, i) => {
    const active = i === selectedRouteIndex;
    line.setStyle({
      opacity: active ? 0.95 : 0.25,
      weight: active ? 7 : 4,
    });
  });

  document.querySelectorAll(".route-card").forEach((card) => {
    const idx = Number(card.dataset.routeIndex);
    card.classList.toggle("active", idx === selectedRouteIndex);
  });

  const activeRoute = currentRoutes[selectedRouteIndex];
  renderRouteMarkers(activeRoute);

  if (shouldFitBounds) {
    const path = routePaths[selectedRouteIndex] || [];
    if (path.length > 0) {
      map.fitBounds(path, { padding: [30, 30] });
    }
  }
}

function renderRoutesOnMap(routes) {
  if (!map) return;

  clearMapObjects();
  currentRoutes = routes || [];
  selectedRouteIndex = 0;

  const allPoints = [];

  routes.forEach((route, index) => {
    if (!route.overview_polyline) return;
    const path = decodePolyline(route.overview_polyline);
    if (!path.length) return;

    const polyline = L.polyline(path, {
      color: colors[index % colors.length],
      opacity: 0.85,
      weight: 5,
    });
    polyline.addTo(map);

    path.forEach((point) => allPoints.push(point));
    polylines.push(polyline);
    routePaths.push(path);
  });

  if (allPoints.length > 0) {
    map.fitBounds(allPoints, { padding: [30, 30] });
  }

  applyRouteSelection(0, true);
}

function initMap() {
  map = L.map("map", {
    center: [35.6812, 139.7671],
    zoom: 12,
    zoomControl: true,
  });

  if (mapboxApiKey) {
    L.tileLayer("https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/256/{z}/{x}/{y}@2x?access_token={accessToken}", {
      maxZoom: 19,
      accessToken: mapboxApiKey,
      attribution:
        '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
  } else {
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);
  }

  map.on("click", (event) => {
    const latlng = event.latlng;
    const coordinateText = formatLatLng(latlng);
    const popupHtml = `
      <div>
        <div><strong>坐标</strong>: ${coordinateText}</div>
        <div class="map-select-actions">
          <button type="button" class="map-select-btn" data-pick-kind="origin" data-lat="${latlng.lat}" data-lng="${latlng.lng}">设为起点</button>
          <button type="button" class="map-select-btn" data-pick-kind="destination" data-lat="${latlng.lat}" data-lng="${latlng.lng}">设为终点</button>
        </div>
      </div>
    `;

    L.popup({ maxWidth: 260 }).setLatLng(latlng).setContent(popupHtml).openOn(map);
  });
}

initMap();

document.addEventListener("click", (event) => {
  const actionButton = event.target.closest(".map-select-btn");
  if (!actionButton) return;

  const kind = actionButton.dataset.pickKind;
  const lat = Number(actionButton.dataset.lat);
  const lng = Number(actionButton.dataset.lng);

  if (!kind || Number.isNaN(lat) || Number.isNaN(lng)) return;
  setPointAsEndpoint(kind, { lat, lng });
});

mapLocateBtn.addEventListener("click", () => {
  locateMapByAddress();
});

mapLocateInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  locateMapByAddress();
});

originInput.addEventListener("change", () => {
  autoSubmitIfReady();
});

destinationInput.addEventListener("change", () => {
  autoSubmitIfReady();
});

routeListNode.addEventListener("click", (event) => {
  const routeLink = event.target.closest(".route-link");
  if (routeLink) {
    event.preventDefault();
    event.stopPropagation();
    const index = Number(routeLink.dataset.routeIndex);
    if (!Number.isNaN(index)) {
      openRouteDetail(index);
    }
    return;
  }

  const card = event.target.closest(".route-card");
  if (!card) return;
  const index = Number(card.dataset.routeIndex);
  if (Number.isNaN(index)) return;
  applyRouteSelection(index, true);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const origin = originInput.value.trim();
  const destination = destinationInput.value.trim();
  if (!origin || !destination) {
    replyNode.textContent = "请输入起点和终点";
    return;
  }

  submitBtn.disabled = true;
  replyNode.textContent = "查询中，请稍候...";
  routeListNode.textContent = "正在加载路线...";
  updateDataSourceBadge("查询中");
  clearUserPlacedMarkers();

  try {
    const response = await fetch("/api/transit-agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ origin, destination }),
    });

    const data = await response.json();
    if (!response.ok) {
      replyNode.textContent = data.detail || "查询失败";
      routeListNode.textContent = "暂无结果";
      updateDataSourceBadge("查询失败");
      currentRoutes = [];
      clearMapObjects();
      return;
    }

    replyNode.textContent = data.reply || "已返回路线结果";
    const plan = data.plan || {};
    const routes = plan.routes || [];
    const provider = plan.provider || "google";
    const mode = plan.mode_used || "transit";
    const statusText = `${provider.toUpperCase()} / ${mode}${data.degraded ? " / 降级" : ""}`;
    updateDataSourceBadge(statusText);

    renderRouteList(routes);
    renderRoutesOnMap(routes);
  } catch (error) {
    replyNode.textContent = `请求异常: ${error}`;
    routeListNode.textContent = "暂无结果";
    updateDataSourceBadge("请求异常");
    currentRoutes = [];
    clearMapObjects();
  } finally {
    submitBtn.disabled = false;
  }
});
