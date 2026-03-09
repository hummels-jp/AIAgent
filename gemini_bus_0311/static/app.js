const form = document.getElementById("route-form");
const originInput = document.getElementById("origin");
const destinationInput = document.getElementById("destination");
const replyNode = document.getElementById("agent-reply");
const routeListNode = document.getElementById("route-list");
const submitBtn = document.getElementById("submit-btn");

let map;
let polylines = [];
let markers = [];

const colors = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ea580c"];

function clearMapObjects() {
  polylines.forEach((line) => line.setMap(null));
  markers.forEach((marker) => marker.setMap(null));
  polylines = [];
  markers = [];
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
        <article class="route-card">
          <h3>方案 ${idx + 1}：${route.summary || "公交地铁换乘"}</h3>
          <div class="meta">时长：${route.duration_text || "-"} ｜ 距离：${route.distance_text || "-"} ｜ 票价：${route.fare || "未知"}</div>
          <div class="meta">出发：${route.start_address || "-"}</div>
          <div class="meta">到达：${route.end_address || "-"}</div>
          <div class="lines">线路：${transitLines || "请查看地图与步骤"}</div>
        </article>
      `;
    })
    .join("");
}

function renderRoutesOnMap(routes) {
  if (!map) return;

  clearMapObjects();

  const bounds = new google.maps.LatLngBounds();

  routes.forEach((route, index) => {
    if (!route.overview_polyline) return;
    const path = google.maps.geometry.encoding.decodePath(route.overview_polyline);

    const polyline = new google.maps.Polyline({
      path,
      geodesic: true,
      strokeColor: colors[index % colors.length],
      strokeOpacity: 0.85,
      strokeWeight: 5,
      map,
    });

    path.forEach((point) => bounds.extend(point));
    polylines.push(polyline);
  });

  if (routes.length > 0) {
    const first = routes[0];
    if (first.steps && first.steps.length > 0) {
      const firstStep = first.steps[0];
      const lastStep = first.steps[first.steps.length - 1];

      if (firstStep.polyline) {
        const startPath = google.maps.geometry.encoding.decodePath(firstStep.polyline);
        if (startPath.length > 0) {
          const marker = new google.maps.Marker({
            position: startPath[0],
            map,
            label: "起",
          });
          markers.push(marker);
        }
      }

      if (lastStep.polyline) {
        const endPath = google.maps.geometry.encoding.decodePath(lastStep.polyline);
        if (endPath.length > 0) {
          const marker = new google.maps.Marker({
            position: endPath[endPath.length - 1],
            map,
            label: "终",
          });
          markers.push(marker);
        }
      }
    }
  }

  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, 40);
  }
}

window.initMap = function initMap() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 39.9042, lng: 116.4074 },
    zoom: 12,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false,
  });
};

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
      clearMapObjects();
      return;
    }

    replyNode.textContent = data.reply || "已返回路线结果";
    const routes = (data.plan && data.plan.routes) || [];
    renderRouteList(routes);
    renderRoutesOnMap(routes);
  } catch (error) {
    replyNode.textContent = `请求异常: ${error}`;
    routeListNode.textContent = "暂无结果";
    clearMapObjects();
  } finally {
    submitBtn.disabled = false;
  }
});
