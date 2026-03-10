let detailMap;
let overviewMap;
let overviewRouteLine;
let overviewCarMarker;
let overviewStartMarker;
let overviewEndMarker;
let carMarker;
let stepStartPoints = [];
let stepPaths = [];
let currentStepIndex = -1;
let isPlaying = false;
let autoStreetEnabled = true;
let activeMode = "walk";

let frameRequestId = null;
let lastFrameTs = null;
let motionPath = [];
let motionSegIndex = 0;
let motionSegRatio = 0;
let lastStreetSyncTs = 0;
let lastStreetPoint = null;
let lastHeadingDeg = 0;
let currentVehicleHeadingDeg = 0;
let lastStreetHeadingDeg = 0;
let lastStreetEmbedUrl = "";
let lastStreetRenderPoint = null;
let lastStreetRenderHeadingDeg = 0;
let currentVehiclePoint = null;
let activeStreetFrame = "a";
let streetFrameLoading = false;
let queuedStreetUrl = "";
let queuedStreetOpenUrl = "";
let streetRealtimeTimer = null;
let mapillaryApiKey = "";
let mapillaryEnabled = false;
let lastMapillaryImageId = "";
let mapillaryLastLookupTs = 0;
let mapillaryLastLookupPoint = null;
let streetUpdateToken = 0;

const WALK_SPEED_KMH = 10;
const DRIVE_SPEED_KMH = 30;
let currentSpeedKmh = WALK_SPEED_KMH;
const WALK_EYE_HEIGHT_CM = 170;
const DRIVE_EYE_HEIGHT_CM = 100;
const STREET_TARGET_FPS = 24;
// Iframe street-view sources are expensive to reload; keep updates paced to reduce jank.
const STREET_SYNC_INTERVAL_MS = Math.max(1000 / STREET_TARGET_FPS, 380);
const STREET_SYNC_MIN_MOVE_M = 3.2;
const STREET_SYNC_MIN_HEADING_DEG = 7;
const MAPILLARY_LOOKUP_INTERVAL_MS = 700;
const MAPILLARY_LOOKUP_MIN_MOVE_M = 4;
const MAPILLARY_BBOX_DELTA = 0.0015;
const MAPILLARY_CANDIDATE_LIMIT = 12;
const STREET_REALTIME_TICK_MS = 650;
const HEADING_SMOOTHING_ALPHA = 0.28;
const DRIVE_STREET_FRONT_OFFSET_M = 6;
const WALK_STREET_FRONT_OFFSET_M = 1.5;

const startBtn = document.getElementById("btn-start");
const pauseBtn = document.getElementById("btn-pause");
const resetBtn = document.getElementById("btn-reset");
const walkModeBtn = document.getElementById("btn-mode-walk");
const driveModeBtn = document.getElementById("btn-mode-drive");
const streetAutoBtn = document.getElementById("btn-street-auto");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");
const streetPreviewA = document.getElementById("street-preview-a");
const streetPreviewB = document.getElementById("street-preview-b");
const streetExternal = document.getElementById("street-external");
const streetStatus = document.getElementById("street-status");
const overviewMapNode = document.getElementById("overview-map");
const overviewMeta = document.getElementById("overview-meta");

function setStreetStatus(text, kind = "pending") {
  if (!streetStatus) return;
  streetStatus.textContent = text;
  streetStatus.classList.remove("street-status-mapillary", "street-status-google", "street-status-pending");
  if (kind === "mapillary") {
    streetStatus.classList.add("street-status-mapillary");
  } else if (kind === "google") {
    streetStatus.classList.add("street-status-google");
  } else {
    streetStatus.classList.add("street-status-pending");
  }
}

function normalizeHeadingDeg(deg) {
  return ((deg % 360) + 360) % 360;
}

function shortestHeadingDeltaDeg(fromDeg, toDeg) {
  const from = normalizeHeadingDeg(fromDeg);
  const to = normalizeHeadingDeg(toDeg);
  return ((to - from + 540) % 360) - 180;
}

function smoothHeadingDeg(fromDeg, toDeg, alpha) {
  const delta = shortestHeadingDeltaDeg(fromDeg, toDeg);
  return normalizeHeadingDeg(fromDeg + delta * alpha);
}

function updateVehicleHeading(targetHeadingDeg, immediate = false) {
  const target = normalizeHeadingDeg(targetHeadingDeg);
  currentVehicleHeadingDeg = immediate
    ? target
    : smoothHeadingDeg(currentVehicleHeadingDeg, target, HEADING_SMOOTHING_ALPHA);
  lastHeadingDeg = currentVehicleHeadingDeg;

  if (!carMarker) return;
  const iconEl = carMarker.getElement();
  if (!iconEl) return;
  const glyph = iconEl.querySelector(".vehicle-glyph");
  if (glyph) {
    glyph.style.transform = `rotate(${currentVehicleHeadingDeg.toFixed(1)}deg)`;
  }
}

function projectPointForward(point, headingDeg, distanceMeters) {
  const R = 6371000;
  const latRad = (point[0] * Math.PI) / 180;
  const headingRad = (headingDeg * Math.PI) / 180;
  const dLat = (distanceMeters * Math.cos(headingRad)) / R;
  const dLng = (distanceMeters * Math.sin(headingRad)) / (R * Math.cos(latRad));
  return [point[0] + (dLat * 180) / Math.PI, point[1] + (dLng * 180) / Math.PI];
}

function currentSpeedMps() {
  return (currentSpeedKmh * 1000) / 3600;
}

function updateOverviewMeta(point, headingDeg = 0) {
  if (!overviewMeta || !point) return;
  overviewMeta.textContent = `车辆位置：${point[0].toFixed(6)}, ${point[1].toFixed(6)} ｜ 朝向：${Math.round(headingDeg)}°`;
}

function initOverviewMap(path) {
  if (!overviewMapNode || !Array.isArray(path) || path.length === 0) return;

  if (overviewMap) {
    overviewMap.remove();
  }

  overviewMap = L.map("overview-map", {
    center: path[0],
    zoom: 15,
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false,
    touchZoom: false,
    tap: false,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(overviewMap);

  overviewRouteLine = L.polyline(path, {
    color: "#2563eb",
    weight: 4,
    opacity: 0.9,
  }).addTo(overviewMap);

  overviewStartMarker = L.circleMarker(path[0], {
    radius: 5,
    color: "#16a34a",
    fillColor: "#22c55e",
    fillOpacity: 0.9,
    weight: 2,
  }).addTo(overviewMap);

  overviewEndMarker = L.circleMarker(path[path.length - 1], {
    radius: 5,
    color: "#dc2626",
    fillColor: "#ef4444",
    fillOpacity: 0.9,
    weight: 2,
  }).addTo(overviewMap);

  overviewCarMarker = L.circleMarker(path[0], {
    radius: 6,
    color: "#1d4ed8",
    fillColor: "#60a5fa",
    fillOpacity: 0.95,
    weight: 2,
  }).addTo(overviewMap);

  overviewMap.fitBounds(path, { padding: [20, 20] });
  updateOverviewMeta(path[0], 0);
}

function updateOverviewPosition(point, headingDeg = 0) {
  if (!overviewMap || !overviewCarMarker || !point) return;
  overviewCarMarker.setLatLng(point);
  overviewMap.panTo(point, { animate: false });
  updateOverviewMeta(point, headingDeg);
}

function buildVehicleIcon() {
  return L.divIcon({
    className: "car-icon",
    html: `<span class="vehicle-glyph">${activeMode === "drive" ? "🚗" : "🚶"}</span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

function refreshVehicleIcon() {
  if (!carMarker) return;
  carMarker.setIcon(buildVehicleIcon());
  requestAnimationFrame(() => {
    updateVehicleHeading(currentVehicleHeadingDeg, true);
  });
}

function applyMotionMode(mode) {
  activeMode = mode === "drive" ? "drive" : "walk";
  currentSpeedKmh = activeMode === "drive" ? DRIVE_SPEED_KMH : WALK_SPEED_KMH;

  walkModeBtn.classList.toggle("active", activeMode === "walk");
  driveModeBtn.classList.toggle("active", activeMode === "drive");
  refreshVehicleIcon();

  if (currentStepIndex >= 0) {
    moveCarToStep(currentStepIndex);
    if (autoStreetEnabled) {
      const point = stepStartPoints[currentStepIndex];
      if (point) {
        syncStreetPreview(point, true);
      }
    }
  }
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

function getRoutePayload() {
  const params = new URLSearchParams(window.location.search);
  const key = params.get("key");
  if (!key) return null;

  const raw = localStorage.getItem(key) || sessionStorage.getItem(key);
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw);
    // One-time payload to avoid localStorage accumulation.
    localStorage.removeItem(key);
    return payload;
  } catch {
    return null;
  }
}

function renderSteps(steps) {
  const node = document.getElementById("steps");
  if (!steps || steps.length === 0) {
    node.textContent = "暂无步骤";
    return;
  }

  stepPaths = steps.map((step) => decodePolyline(step.polyline));
  stepStartPoints = stepPaths.map((path) => {
    if (path.length > 0) return path[0];
    return null;
  });

  node.innerHTML = steps
    .map((step, idx) => {
      const main = step.instruction || step.mode || "步骤";
      const sub = `${step.mode || ""} ${step.distance_text || ""} ${step.duration_text || ""}`.trim();
      const point = stepStartPoints[idx];
      const streetUrl = point
        ? `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${point[0]},${point[1]}`
        : "";
      return `
        <div class="step-item" data-step-index="${idx}">
          <div class="step-main">${idx + 1}. ${main}</div>
          <div class="step-sub">${sub || "-"}</div>
          <div class="step-actions">
            ${streetUrl ? `<a class="street-link" href="${streetUrl}" target="_blank" rel="noopener noreferrer">查看该步街景</a>` : ""}
          </div>
        </div>
      `;
    })
    .join("");
}

function renderMap(route) {
  detailMap = L.map("map", {
    center: [35.6812, 139.7671],
    zoom: 12,
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(detailMap);

  const path = decodePolyline(route.overview_polyline);
  if (path.length > 0) {
    L.polyline(path, {
      color: "#2563eb",
      opacity: 0.9,
      weight: 6,
    }).addTo(detailMap);

    L.marker(path[0]).addTo(detailMap).bindTooltip("起", { permanent: true, direction: "top" });
    L.marker(path[path.length - 1]).addTo(detailMap).bindTooltip("终", { permanent: true, direction: "top" });
    detailMap.fitBounds(path, { padding: [30, 30] });

    carMarker = L.marker(path[0], { icon: buildVehicleIcon() }).addTo(detailMap);
    initOverviewMap(path);
    updateOverviewPosition(path[0], 0);
  }
}

function moveCarToStep(stepIndex) {
  if (!carMarker || !detailMap) return false;
  const point = stepStartPoints[stepIndex];
  if (!point) return false;

  carMarker.setLatLng(point);
  currentVehiclePoint = point;

  const headingPath = stepPaths[stepIndex] || [];
  if (headingPath.length > 1) {
    const rawHeading = bearingDegrees(headingPath[0], headingPath[1]);
    updateVehicleHeading(rawHeading, true);
  }

  updateOverviewPosition(point, lastHeadingDeg);

  const targetZoom = activeMode === "drive" ? 18 : 19;
  detailMap.setView(point, Math.max(detailMap.getZoom(), targetZoom), { animate: true });

  if (autoStreetEnabled) {
    syncStreetPreview(point, true);
  }

  document.querySelectorAll(".step-item").forEach((item) => {
    const idx = Number(item.dataset.stepIndex);
    item.classList.toggle("active", idx === stepIndex);
  });

  return true;
}

function buildGoogleStreetEmbedUrl(point) {
  const heading = Number.isFinite(lastStreetRenderHeadingDeg) ? lastStreetRenderHeadingDeg : 0;
  // Use forward heading and mode-specific pitch to approximate eye-level first-person views.
  const drivePitch = DRIVE_EYE_HEIGHT_CM <= 110 ? -6 : -4;
  const pitch = activeMode === "walk" ? 0 : drivePitch;
  return `https://www.google.com/maps?q=&layer=c&cbll=${point[0]},${point[1]}&cbp=12,${heading.toFixed(1)},0,${pitch},0&output=svembed`;
}

function buildGoogleStreetOpenUrl(point) {
  const heading = Number.isFinite(lastStreetRenderHeadingDeg) ? lastStreetRenderHeadingDeg : 0;
  const drivePitch = DRIVE_EYE_HEIGHT_CM <= 110 ? -6 : -4;
  const pitch = activeMode === "walk" ? 0 : drivePitch;
  const walkFov = WALK_EYE_HEIGHT_CM >= 170 ? 90 : 95;
  const driveFov = DRIVE_EYE_HEIGHT_CM <= 110 ? 75 : 80;
  const fov = activeMode === "walk" ? walkFov : driveFov;
  return `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${point[0]},${point[1]}&heading=${heading.toFixed(1)}&pitch=${pitch}&fov=${fov}`;
}

function loadStreetEmbedUrl(embedUrl, openUrl) {
  if (!embedUrl) return;
  if (embedUrl === lastStreetEmbedUrl) {
    if (openUrl) {
      streetExternal.href = openUrl;
    }
    return;
  }

  if (streetFrameLoading) {
    queuedStreetUrl = embedUrl;
    queuedStreetOpenUrl = openUrl || "";
    return;
  }

  streetFrameLoading = true;
  const nextFrame = activeStreetFrame === "a" ? streetPreviewB : streetPreviewA;
  const currentFrame = activeStreetFrame === "a" ? streetPreviewA : streetPreviewB;

  nextFrame.onload = () => {
    currentFrame.classList.remove("active");
    nextFrame.classList.add("active");
    activeStreetFrame = activeStreetFrame === "a" ? "b" : "a";
    nextFrame.onload = null;
    streetFrameLoading = false;

    if (queuedStreetUrl && queuedStreetUrl !== lastStreetEmbedUrl) {
      const queuedUrl = queuedStreetUrl;
      const queuedOpen = queuedStreetOpenUrl;
      queuedStreetUrl = "";
      queuedStreetOpenUrl = "";
      loadStreetEmbedUrl(queuedUrl, queuedOpen);
    }
  };

  nextFrame.src = embedUrl;
  lastStreetEmbedUrl = embedUrl;
  if (openUrl) {
    streetExternal.href = openUrl;
  }
}

function buildMapillaryBbox(point, delta = MAPILLARY_BBOX_DELTA) {
  const lat = point[0];
  const lng = point[1];
  return `${(lng - delta).toFixed(6)},${(lat - delta).toFixed(6)},${(lng + delta).toFixed(6)},${(lat + delta).toFixed(6)}`;
}

async function fetchNearestMapillaryImage(point) {
  if (!mapillaryApiKey) return null;

  const fields = "id,computed_geometry,compass_angle";
  const bboxes = [buildMapillaryBbox(point), buildMapillaryBbox(point, MAPILLARY_BBOX_DELTA * 2)];

  for (const bbox of bboxes) {
    const url = `https://graph.mapillary.com/images?access_token=${encodeURIComponent(mapillaryApiKey)}&fields=${encodeURIComponent(
      fields
    )}&limit=${MAPILLARY_CANDIDATE_LIMIT}&bbox=${bbox}`;
    const response = await fetch(url);
    if (!response.ok) continue;
    const data = await response.json();
    const images = data.data || [];
    if (!images.length) continue;

    let bestImage = null;
    let bestScore = Infinity;

    for (const image of images) {
      if (!image || !image.id) continue;
      const coords = (image.computed_geometry || {}).coordinates || [];
      if (!Array.isArray(coords) || coords.length !== 2) continue;

      const imagePoint = [Number(coords[1]), Number(coords[0])];
      const distanceScore = haversineMeters(point, imagePoint);
      const imageHeading = Number(image.compass_angle || 0);
      const headingScore = headingDeltaDeg(lastHeadingDeg, imageHeading);

      // Drive mode strongly favors forward-facing imagery and penalizes reverse-facing shots.
      const headingWeight = activeMode === "drive" ? 4.0 : 0.8;
      const reversePenalty = activeMode === "drive" && headingScore > 95 ? 1800 : 0;
      const score = distanceScore + headingScore * headingWeight + reversePenalty;
      if (score < bestScore) {
        bestScore = score;
        bestImage = image;
      }
    }

    if (bestImage && bestImage.id) {
      return bestImage;
    }
  }

  return null;
}

function buildMapillaryEmbedUrl(imageId) {
  return `https://www.mapillary.com/embed?image_key=${encodeURIComponent(imageId)}&style=photo`;
}

function buildMapillaryOpenUrl(imageId) {
  return `https://www.mapillary.com/app/?pKey=${encodeURIComponent(imageId)}&focus=photo`;
}

async function updateStreetPreview(point, forceLookup = false) {
  if (!point) return;

  if (mapillaryEnabled) {
    setStreetStatus("街景源：Mapillary 检索中...", "pending");
    const now = Date.now();
    const moved = mapillaryLastLookupPoint ? haversineMeters(mapillaryLastLookupPoint, point) : Infinity;
    const shouldLookup =
      forceLookup ||
      !lastMapillaryImageId ||
      now - mapillaryLastLookupTs >= MAPILLARY_LOOKUP_INTERVAL_MS ||
      moved >= MAPILLARY_LOOKUP_MIN_MOVE_M;

    if (shouldLookup) {
      const token = ++streetUpdateToken;
      try {
        const image = await fetchNearestMapillaryImage(point);
        if (token !== streetUpdateToken) return;

        mapillaryLastLookupTs = now;
        mapillaryLastLookupPoint = point;
        if (image && image.id) {
          lastMapillaryImageId = image.id;
          const driveHint = activeMode === "drive" ? "｜行车前视（视高100cm）" : "";
          setStreetStatus(`街景源：Mapillary（实时）${driveHint}`, "mapillary");
          loadStreetEmbedUrl(buildMapillaryEmbedUrl(image.id), buildMapillaryOpenUrl(image.id));
          return;
        }

        setStreetStatus("街景源：Google（Mapillary附近无图）", "google");
      } catch {
        // Silently fallback to Google preview when Mapillary lookup fails.
        setStreetStatus("街景源：Google（Mapillary检索失败）", "google");
      }
    }

    if (lastMapillaryImageId) {
      const driveHint = activeMode === "drive" ? "｜行车前视（视高100cm）" : "";
      setStreetStatus(`街景源：Mapillary（缓存复用）${driveHint}`, "mapillary");
      loadStreetEmbedUrl(buildMapillaryEmbedUrl(lastMapillaryImageId), buildMapillaryOpenUrl(lastMapillaryImageId));
      return;
    }
  }

  if (!mapillaryEnabled) {
    setStreetStatus("街景源：Google（未配置Mapillary）", "google");
  }

  const embedUrl = buildGoogleStreetEmbedUrl(point);
  const openUrl = buildGoogleStreetOpenUrl(point);
  loadStreetEmbedUrl(embedUrl, openUrl);
}

function headingDeltaDeg(a, b) {
  const diff = Math.abs((a || 0) - (b || 0));
  return Math.min(diff, 360 - diff);
}

function interpolateHeadingDeg(fromDeg, toDeg, maxStepDeg) {
  const from = Number.isFinite(fromDeg) ? fromDeg : 0;
  const to = Number.isFinite(toDeg) ? toDeg : 0;
  let delta = ((to - from + 540) % 360) - 180;
  if (Math.abs(delta) <= maxStepDeg) return (from + delta + 360) % 360;
  delta = delta > 0 ? maxStepDeg : -maxStepDeg;
  return (from + delta + 360) % 360;
}

function interpolateTowardPoint(fromPoint, toPoint, maxStepMeters) {
  if (!fromPoint) return toPoint;
  const dist = haversineMeters(fromPoint, toPoint);
  if (dist <= maxStepMeters) return toPoint;
  const ratio = Math.max(0, Math.min(1, maxStepMeters / dist));
  return interpolatePoint(fromPoint, toPoint, ratio);
}

function syncStreetPreview(point, force = false) {
  if (!autoStreetEnabled || !point) return;

  const frontOffset = activeMode === "drive" ? DRIVE_STREET_FRONT_OFFSET_M : WALK_STREET_FRONT_OFFSET_M;
  const syncPoint = projectPointForward(point, lastHeadingDeg, frontOffset);

  const now = Date.now();
  const moved = lastStreetPoint ? haversineMeters(lastStreetPoint, syncPoint) : Infinity;
  const timeoutReached = now - lastStreetSyncTs >= STREET_SYNC_INTERVAL_MS;
  const movedEnough = moved >= STREET_SYNC_MIN_MOVE_M;
  const headingChangedEnough = headingDeltaDeg(lastStreetHeadingDeg, lastHeadingDeg) >= STREET_SYNC_MIN_HEADING_DEG;

  if (force || (timeoutReached && (movedEnough || headingChangedEnough))) {
    const pointStep = activeMode === "drive" ? 2.2 : 1.0;
    const headingStep = activeMode === "drive" ? 7 : 4;
    lastStreetRenderPoint = interpolateTowardPoint(lastStreetRenderPoint, syncPoint, pointStep);
    lastStreetRenderHeadingDeg = interpolateHeadingDeg(lastStreetRenderHeadingDeg, lastHeadingDeg, headingStep);

    updateStreetPreview(lastStreetRenderPoint, force);
    lastStreetSyncTs = now;
    lastStreetPoint = lastStreetRenderPoint;
    lastStreetHeadingDeg = lastHeadingDeg;
  }
}

function haversineMeters(a, b) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371000;
  const dLat = toRad(b[0] - a[0]);
  const dLng = toRad(b[1] - a[1]);
  const lat1 = toRad(a[0]);
  const lat2 = toRad(b[0]);

  const sinDLat = Math.sin(dLat / 2);
  const sinDLng = Math.sin(dLng / 2);
  const h = sinDLat * sinDLat + Math.cos(lat1) * Math.cos(lat2) * sinDLng * sinDLng;
  return 2 * R * Math.asin(Math.sqrt(h));
}

function bearingDegrees(a, b) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const toDeg = (rad) => (rad * 180) / Math.PI;
  const lat1 = toRad(a[0]);
  const lat2 = toRad(b[0]);
  const dLng = toRad(b[1] - a[1]);

  const y = Math.sin(dLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  const brng = (toDeg(Math.atan2(y, x)) + 360) % 360;
  return brng;
}

function interpolatePoint(a, b, t) {
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
}

function updateProgress() {
  const total = stepStartPoints.length;
  const current = total === 0 || currentStepIndex < 0 ? 0 : Math.min(currentStepIndex + 1, total);
  const percent = total === 0 ? 0 : (current / total) * 100;

  progressBar.style.width = `${percent}%`;
  progressText.textContent = `进度：${current} / ${total}`;
}

function updateButtons() {
  const total = stepStartPoints.length;
  const hasSteps = total > 0;
  const finished = currentStepIndex >= total - 1;

  startBtn.disabled = !hasSteps || isPlaying || finished;
  pauseBtn.disabled = !isPlaying;
  resetBtn.disabled = !hasSteps;
}

function stopStreetRealtimeTicker() {
  if (!streetRealtimeTimer) return;
  clearInterval(streetRealtimeTimer);
  streetRealtimeTimer = null;
}

function startStreetRealtimeTicker() {
  stopStreetRealtimeTicker();
  if (!autoStreetEnabled) return;

  streetRealtimeTimer = setInterval(() => {
    if (!isPlaying || !currentVehiclePoint) return;
    syncStreetPreview(currentVehiclePoint, true);
  }, STREET_REALTIME_TICK_MS);
}

function pausePlayback() {
  stopStreetRealtimeTicker();
  if (frameRequestId) {
    cancelAnimationFrame(frameRequestId);
    frameRequestId = null;
  }
  lastFrameTs = null;
  isPlaying = false;
  updateButtons();
}

function goToStep(stepIndex) {
  currentStepIndex = stepIndex;
  moveCarToStep(stepIndex);
  updateProgress();
  updateButtons();
}

function stepForward() {
  const total = stepStartPoints.length;
  if (total === 0) {
    pausePlayback();
    return;
  }

  if (currentStepIndex >= total - 1) {
    pausePlayback();
    return;
  }

  goToStep(currentStepIndex + 1);

  if (currentStepIndex >= total - 1) {
    pausePlayback();
    return;
  }

  if (isPlaying) {
    startStepMotion(currentStepIndex);
  }
}

function startStepMotion(stepIndex) {
  const path = stepPaths[stepIndex] || [];
  if (path.length === 0) {
    stepForward();
    return;
  }

  motionPath = path;
  motionSegIndex = 0;
  motionSegRatio = 0;
  moveCarToStep(stepIndex);

  const tick = (ts) => {
    if (!isPlaying) return;
    if (!lastFrameTs) {
      lastFrameTs = ts;
      frameRequestId = requestAnimationFrame(tick);
      return;
    }

    const dt = (ts - lastFrameTs) / 1000;
    lastFrameTs = ts;
    let moveDist = currentSpeedMps() * dt;

    while (moveDist > 0 && motionSegIndex < motionPath.length - 1) {
      const a = motionPath[motionSegIndex];
      const b = motionPath[motionSegIndex + 1];
      const segLen = Math.max(haversineMeters(a, b), 0.001);
      const used = segLen * motionSegRatio;
      const remain = segLen - used;

      if (moveDist < remain) {
        motionSegRatio = (used + moveDist) / segLen;
        moveDist = 0;
      } else {
        moveDist -= remain;
        motionSegIndex += 1;
        motionSegRatio = 0;
      }
    }

    if (motionSegIndex >= motionPath.length - 1) {
      carMarker.setLatLng(motionPath[motionPath.length - 1]);
      lastFrameTs = null;
      stepForward();
      return;
    }

    const p1 = motionPath[motionSegIndex];
    const p2 = motionPath[motionSegIndex + 1];
    const cur = interpolatePoint(p1, p2, motionSegRatio);
    const rawHeading = bearingDegrees(p1, p2);
    updateVehicleHeading(rawHeading);
    carMarker.setLatLng(cur);
    currentVehiclePoint = cur;
    updateOverviewPosition(cur, lastHeadingDeg);

    if (autoStreetEnabled) {
      syncStreetPreview(cur);
    }

    const followZoom = activeMode === "drive" ? 18 : 19;
    detailMap.setView(cur, Math.max(detailMap.getZoom(), followZoom), { animate: false });

    frameRequestId = requestAnimationFrame(tick);
  };

  frameRequestId = requestAnimationFrame(tick);
}

function startPlayback() {
  if (isPlaying || stepStartPoints.length === 0) return;

  if (currentStepIndex < 0) {
    goToStep(0);
  }

  if (currentStepIndex >= stepStartPoints.length - 1) {
    updateButtons();
    return;
  }

  if (autoStreetEnabled && currentStepIndex >= 0) {
    // Playback should drive street-view movement directly, without requiring iframe UI interaction.
    const point = stepStartPoints[currentStepIndex];
    if (point) {
      syncStreetPreview(point, true);
      setStreetStatus(
        mapillaryEnabled ? "街景源：Mapillary（播放联动中）" : "街景源：Google（播放联动中）",
        mapillaryEnabled ? "mapillary" : "google"
      );
    }
  }

  isPlaying = true;
  updateButtons();
  startStreetRealtimeTicker();

  startStepMotion(currentStepIndex);
}

function resetPlayback() {
  stopStreetRealtimeTicker();
  pausePlayback();
  if (stepStartPoints.length > 0) {
    goToStep(0);
  } else {
    currentStepIndex = -1;
    updateProgress();
    updateButtons();
  }
}

(function init() {
  const payload = getRoutePayload();
  if (!payload || !payload.route) {
    document.getElementById("meta").textContent = "未找到线路详情数据，请返回主页面重新点击链接。";
    return;
  }

  const route = payload.route;
  const title = document.getElementById("title");
  const meta = document.getElementById("meta");
  const source = document.getElementById("source");

  title.textContent = `方案 ${Number(payload.index) + 1} 详情`;
  meta.textContent = `${payload.query.origin} -> ${payload.query.destination} | 时长: ${route.duration_text || "-"} | 距离: ${route.distance_text || "-"}`;
  source.textContent = payload.source || "";
  mapillaryApiKey = (payload.mapillaryApiKey || "").trim();
  mapillaryEnabled = Boolean(mapillaryApiKey);
  setStreetStatus(
    mapillaryEnabled ? "街景源：Mapillary 已就绪（行车时优先前视）" : "街景源：Google（未配置Mapillary）",
    mapillaryEnabled ? "mapillary" : "google"
  );
  streetAutoBtn.textContent = `街景自动联动：开（${mapillaryEnabled ? "Mapillary" : "Google"}）`;

  renderMap(route);
  renderSteps(route.steps || []);

  const stepsNode = document.getElementById("steps");
  stepsNode.addEventListener("click", (event) => {
    const stepNode = event.target.closest(".step-item");
    if (!stepNode) return;
    const stepIndex = Number(stepNode.dataset.stepIndex);
    if (Number.isNaN(stepIndex)) return;
    pausePlayback();
    goToStep(stepIndex);
  });

  startBtn.addEventListener("click", startPlayback);
  pauseBtn.addEventListener("click", pausePlayback);
  resetBtn.addEventListener("click", resetPlayback);
  walkModeBtn.addEventListener("click", () => {
    applyMotionMode("walk");
  });
  driveModeBtn.addEventListener("click", () => {
    applyMotionMode("drive");
  });
  streetAutoBtn.addEventListener("click", () => {
    autoStreetEnabled = !autoStreetEnabled;
    streetAutoBtn.textContent = `街景自动联动：${autoStreetEnabled ? "开" : "关"}（${mapillaryEnabled ? "Mapillary" : "Google"}）`;
    if (autoStreetEnabled && currentStepIndex >= 0) {
      const point = stepStartPoints[currentStepIndex];
      if (point) syncStreetPreview(point, true);
    }
  });

  applyMotionMode("walk");

  if ((route.steps || []).length > 0) {
    goToStep(0);
    const firstPoint = stepStartPoints[0];
    if (firstPoint) {
      currentVehiclePoint = firstPoint;
      updateStreetPreview(firstPoint, true);
    }
  } else {
    updateProgress();
    updateButtons();
  }
})();
