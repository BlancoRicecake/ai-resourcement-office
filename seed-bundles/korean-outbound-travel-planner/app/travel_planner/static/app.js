let cityOptions = {};

let currentTrip = null;
let currentSession = null;
let routeMap = null;
let routeLayerGroup = null;

const routeColors = ["#1f5b45", "#d86b3b", "#346b8c", "#8a5a9f", "#b28722", "#5b6b63", "#a34f58"];

const $ = (selector) => document.querySelector(selector);
const money = (value) => new Intl.NumberFormat("ko-KR").format(value || 0) + "원";
const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#039;", '"': "&quot;" }[char]));

function setDefaultDates() {
  const departure = new Date();
  departure.setDate(departure.getDate() + 30);
  const arrival = new Date(departure);
  arrival.setDate(arrival.getDate() + 3);
  $("#departure-date").value = departure.toISOString().slice(0, 10);
  $("#return-date").value = arrival.toISOString().slice(0, 10);
}

function updateCities() {
  const country = $("#destination-country").value;
  $("#destination-city").innerHTML = (cityOptions[country] || [])
    .map((city) => `<option value="${city.name}" data-code="${city.code}">${city.name}</option>`)
    .join("");
}

async function loadDestinations() {
  try {
    const destinations = await api("/api/destinations?include_provisional=false");
    cityOptions = destinations.reduce((groups, item) => {
      groups[item.country_code] ||= [];
      groups[item.country_code].push({ name: item.city_name, code: item.city_code, country: item.country_name });
      return groups;
    }, {});
    $("#destination-country").innerHTML = Object.entries(cityOptions).map(([code, cities]) => `<option value="${escapeHtml(code)}">${escapeHtml(cities[0].country)}</option>`).join("");
    updateCities();
  } catch (error) {
    setStatus(`목적지 목록을 불러오지 못했습니다: ${error.message}`);
  }
}

function csv(value) {
  return String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
}

function formPayload(form) {
  const data = new FormData(form);
  const selectedCity = $("#destination-city").selectedOptions[0];
  return {
    destination_country: data.get("destination_country"),
    destination_city: data.get("destination_city"),
    destination_code: selectedCity.dataset.code,
    origin_airport: data.get("origin_airport"),
    departure_date: data.get("departure_date"),
    return_date: data.get("return_date"),
    date_flexibility_days: Number(data.get("date_flexibility_days")),
    adults: Number(data.get("adults")),
    children: Number(data.get("children")),
    rooms: Number(data.get("rooms")),
    budget_krw: Number(data.get("budget_krw")),
    checked_baggage: data.has("checked_baggage"),
    cabin_class: data.get("cabin_class"),
    stay_types: data.getAll("stay_types"),
    pace: data.get("pace"),
    interests: csv(data.get("interests")),
    must_visit_places: csv(data.get("must_visit_places")),
    dietary_needs: csv(data.get("dietary_needs")),
    mobility_needs: csv(data.get("mobility_needs")),
    save_profile: data.has("save_profile"),
  };
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((item) => item.msg).join(" · ") : body.detail;
    throw new Error(detail || `요청 실패 (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

const constraintLabels = {
  destination_country: "국가", destination_city: "도시", destination_code: "도시·공항 코드", origin_airport: "출발 공항",
  travel_month: "여행 시기", departure_date: "출국일", return_date: "귀국일",
  nights: "숙박", trip_days: "여행일", adults: "성인", children: "아동", rooms: "객실",
  budget_krw: "총예산", pace: "여행 기준", direct_required: "직항", max_stops: "최대 환승",
  checked_baggage: "위탁수하물", bed_count: "침대", required_amenities: "필수 어메니티",
  ground_mode: "현지 이동", sports_model_preferred: "스포츠카", rental_class: "차량 등급",
  driver_age: "운전자 나이", parking_required: "주차", special_meals_per_day: "특별식",
  special_meal_budget_krw: "특별식 상한", avoid_crowds: "혼잡 회피", must_visit_places: "필수 방문지",
  stay_types: "숙소 유형", date_flexibility_days: "날짜 유연성", safety_checked: "안전 조건 확인",
};
const internalConstraintKeys = new Set(["destination_slug", "destination_status"]);

const readinessLabels = { destination: "목적지", flight: "항공", stay: "숙소", ground_transport: "현지 이동", itinerary: "일정" };

function displayConstraintValue(key, value) {
  if (value === true) return "필요";
  if (value === false) return "불필요";
  if (Array.isArray(value)) return value.join(", ");
  if (key.endsWith("_krw")) return money(value);
  if (key === "nights") return `${value}박`;
  if (key === "trip_days") return `${value}일`;
  if (key === "adults" || key === "children") return `${value}명`;
  if (key === "bed_count") return `${value}개`;
  if (key === "driver_age") return `만 ${value}세`;
  return String(value ?? "미정");
}

function constraintCard(item) {
  return `<article class="constraint-item ${escapeHtml(item.status)}" data-constraint-key="${escapeHtml(item.key)}">
    <div class="constraint-item-head"><div><span class="constraint-key">${escapeHtml(constraintLabels[item.key] || item.key)}</span><span class="constraint-value">${escapeHtml(displayConstraintValue(item.key, item.value))}</span></div>
      <div class="constraint-tools"><button type="button" data-hardness="${escapeHtml(item.key)}">${item.hardness === "hard" ? "필수" : "선호"}</button><button type="button" data-edit="${escapeHtml(item.key)}">수정</button></div>
    </div><small>${escapeHtml(item.reason || "")}</small></article>`;
}

function renderPlanningSession(session) {
  currentSession = session;
  const messages = session.messages.map((message) => `<article class="message ${escapeHtml(message.role)}"><b>${message.role === "user" ? "나" : "여행설계실"}</b><p>${escapeHtml(message.content)}</p></article>`).join("");
  $("#conversation-messages").innerHTML = messages || `<article class="message assistant"><p>여행 이야기를 들려주세요.</p></article>`;
  $("#conversation-messages").scrollTop = $("#conversation-messages").scrollHeight;

  const confirmed = Object.values(session.constraints).filter((item) => item.status === "confirmed" && !internalConstraintKeys.has(item.key));
  const proposed = Object.values(session.constraints).filter((item) => item.status === "proposed" && !internalConstraintKeys.has(item.key));
  const readiness = Object.entries(session.readiness).map(([key, value]) => `<span class="${value !== "blocked" ? "ready" : ""}">${escapeHtml(readinessLabels[key] || key)} · ${escapeHtml(value)}</span>`).join("");
  const invalidated = session.invalidated_sections?.length ? `<p class="invalidation-note">다시 계산할 영역 · ${session.invalidated_sections.map((key) => escapeHtml(readinessLabels[key] || key)).join(", ")}</p>` : "";
  $("#constraint-panel").innerHTML = `<p class="panel-label">LIVE TRIP BRIEF</p><h3>${session.preview ? escapeHtml(session.preview.headline) : "여행 조건 정리 중"}</h3>
    <div class="constraint-groups">
      <section class="constraint-group"><h4>확정</h4><div class="constraint-list">${confirmed.map(constraintCard).join("") || "<small>아직 없음</small>"}</div></section>
      <section class="constraint-group"><h4>이렇게 이해했어요</h4><div class="constraint-list">${proposed.map(constraintCard).join("") || "<small>추가 가정 없음</small>"}</div></section>
      <section class="constraint-group"><h4>준비 상태</h4><div class="readiness-list">${readiness}</div></section>
    </div>${invalidated}
    <button id="finalize-session" class="primary-button finalize-session" type="button" ${session.readiness.flight !== "search_ready" ? "disabled" : ""}>세 가지 여행안 계산하기</button>
    <p class="form-footnote">초안 ID ${escapeHtml(session.id.slice(0, 8))} · 제안값은 예약 사실로 사용하지 않습니다.</p>`;

  if (session.preview) {
    const assumptions = session.preview.assumptions.length ? `<p><b>가정</b> ${session.preview.assumptions.map(escapeHtml).join(" · ")}</p>` : "";
    const candidates = session.preview.destination_candidates.length ? `<p>${session.preview.destination_candidates.map((item) => `<b>${escapeHtml(item.city)}</b> ${escapeHtml(item.summary)}`).join("<br>")}</p>` : "";
    const statusLabels = { validated: "검증 지원", provisional: "임시 지원", researching: "조사 중", unavailable: "계획 불가" };
    const destinationStatus = session.preview.destination_status ? `<p class="destination-status ${escapeHtml(session.preview.destination_status)}"><b>${escapeHtml(statusLabels[session.preview.destination_status] || session.preview.destination_status)}</b> 목적지</p>` : "";
    const researchTasks = session.preview.research_tasks?.length ? `<div class="research-checklist"><h4>목적지 초기세팅</h4>${session.preview.research_tasks.map((task) => `<p><span class="research-state ${escapeHtml(task.status)}">${task.status === "ready" ? "완료" : task.status === "blocked" ? "중단" : "확인 필요"}</span><b>${escapeHtml(task.label)}</b><small>${escapeHtml(task.reason)}</small></p>`).join("")}</div>` : "";
    const researchSources = session.preview.research_sources?.length ? `<div class="research-sources"><h4>확인할 출처</h4>${session.preview.research_sources.slice(0, 6).map((source) => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener">${escapeHtml(source.name)} ↗</a>`).join("")}</div>` : "";
    $("#draft-preview").innerHTML = `<h3>${escapeHtml(session.preview.headline)}</h3>${destinationStatus}<p>${escapeHtml(session.preview.summary)}</p>${candidates}${assumptions}${researchTasks}${researchSources}`;
    $("#draft-preview").classList.remove("hidden");
  } else { $("#draft-preview").classList.add("hidden"); }

  const question = session.next_questions[0];
  if (question) {
    $("#next-question").innerHTML = `<h3>${escapeHtml(question.prompt)}</h3><p>${escapeHtml(question.why_asked)}</p><div class="question-options">${question.options.map((option) => `<button type="button" class="${option.recommended ? "recommended" : ""}" data-answer="${escapeHtml(option.value)}" title="${escapeHtml(option.description)}">${escapeHtml(option.label)}</button>`).join("")}</div>`;
    $("#next-question").classList.remove("hidden");
  } else { $("#next-question").classList.add("hidden"); }
}

async function sendConversation(text) {
  if (!text.trim()) return;
  const button = $("#conversation-submit");
  button.disabled = true;
  button.textContent = "조건 정리 중…";
  try {
    const session = currentSession
      ? await api(`/api/planning-sessions/${currentSession.id}/messages`, { method: "POST", body: JSON.stringify({ text }) })
      : await api("/api/planning-sessions", { method: "POST", body: JSON.stringify({ message: text, consent_to_store: $("#conversation-consent").checked }) });
    renderPlanningSession(session);
    $("#conversation-input").value = "";
  } catch (error) { setStatus(`대화 처리 실패: ${error.message}`); }
  finally { button.disabled = false; button.textContent = currentSession ? "조건 반영하기 →" : "초안 만들기 →"; }
}

async function patchConstraint(key, value, hardness = null) {
  if (!currentSession) return;
  const existing = currentSession.constraints[key];
  let parsed = value;
  if (Array.isArray(existing?.value)) parsed = String(value).split(",").map((item) => item.trim()).filter(Boolean);
  else if (typeof existing?.value === "number") parsed = Number(value);
  else if (typeof existing?.value === "boolean") parsed = ["true", "필요", "예", "yes"].includes(String(value).toLowerCase());
  renderPlanningSession(await api(`/api/planning-sessions/${currentSession.id}/constraints`, {
    method: "PATCH", body: JSON.stringify({ changes: [{ key, value: parsed, hardness: hardness || existing?.hardness || "soft", confirmed: true }] }),
  }));
}

async function finalizeSession() {
  if (!currentSession) return;
  setStatus("확정된 조건으로 항공·숙소·일정을 계산하는 중입니다…", true);
  try { renderResult(await api(`/api/planning-sessions/${currentSession.id}/finalize`, { method: "POST" })); }
  catch (error) { setStatus(`최종 계산 전 확인 필요: ${error.message}`); }
}

function setStatus(message, loading = false) {
  const status = $("#status-box");
  status.textContent = message;
  status.classList.toggle("loading", loading);
}

function offerLink(url, label) {
  return `<a class="out-link" href="${escapeHtml(url)}" target="_blank" rel="noopener">${label} ↗</a>`;
}

const priceStatusLabels = {
  live: "A · 실시간 공급자 응답",
  web_reference: "C · 웹 표시 참고가",
  estimated: "D · 계획용 추정치",
  sample: "D · 체험용 샘플",
};

function priceStatusBadge(item) {
  const status = item.price_status || "live";
  return `<span class="confidence-badge confidence-${escapeHtml((item.confidence || "E").toLowerCase())}">${escapeHtml(priceStatusLabels[status] || "E · 확인 필요")}</span>`;
}

function renderFlights(flights) {
  $("#flights").innerHTML = flights.map((flight, index) => `
    <article class="offer-card ${index === 0 ? "recommended" : ""}">
      <span class="rank">${String(index + 1).padStart(2, "0")} ${index === 0 ? "· RECOMMENDED" : ""}</span>
      <h3>${escapeHtml(flight.provider)} 항공안</h3>
      ${priceStatusBadge(flight)}
      <p class="price">${money(flight.total_price_krw)}</p>
      <dl>
        <dt>총 소요</dt><dd>${Math.floor(flight.duration_minutes / 60)}시간 ${flight.duration_minutes % 60}분</dd>
        <dt>환승</dt><dd>${flight.stops}회${flight.airport_change ? " · 공항 변경" : ""}</dd>
        <dt>위탁수하물</dt><dd>${escapeHtml(flight.baggage_status)}</dd>
        <dt>조회</dt><dd>${new Date(flight.observed_at).toLocaleString("ko-KR")}${flight.is_stale ? " · 재검색 필요" : ""}</dd>
      </dl>
      <ul class="reason-list">${flight.score_reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
      ${offerLink(flight.booking_url, "외부에서 최종 조건 확인")}
    </article>
  `).join("");
}

function renderStays(stays) {
  $("#stays").innerHTML = stays.map((stay, index) => `
    <article class="offer-card ${index === 0 ? "recommended" : ""}">
      <span class="rank">${String(index + 1).padStart(2, "0")} · ${escapeHtml(stay.accommodation_type)}</span>
      <h3>${escapeHtml(stay.name)}</h3>
      ${priceStatusBadge(stay)}
      <p class="price">${money(stay.total_price_krw)}</p>
      <dl>
        <dt>객실</dt><dd>${stay.rooms_requested}개</dd>
        <dt>침대</dt><dd>${stay.bed_count ? `${stay.bed_count}개` : "확인 필요"}</dd>
        <dt>주차</dt><dd>${stay.parking_available === true ? (stay.parking_cost_krw_per_night === 0 ? "무료" : (stay.parking_cost_krw_per_night ? `1박 ${money(stay.parking_cost_krw_per_night)}` : "요금 확인 필요")) : "확인 필요"}</dd>
        <dt>어메니티</dt><dd>${stay.amenities?.length ? escapeHtml(stay.amenities.join(", ")) : "확인 필요"}</dd>
        <dt>평점</dt><dd>${stay.rating ?? "확인 필요"}${stay.review_count ? ` (${stay.review_count.toLocaleString()}건)` : ""}</dd>
        <dt>취소</dt><dd>${escapeHtml(stay.cancellation_policy)}</dd>
        <dt>검증</dt><dd class="${stay.verified_inventory ? "verified" : "unverified"}">${stay.verified_inventory ? "현재 재고 응답" : "가격·재고 미검증"}</dd>
      </dl>
      <ul class="reason-list">${stay.score_reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
      ${offerLink(stay.booking_url, "외부 예약 페이지 보기")}
    </article>
  `).join("");
}

function initializeRouteMap() {
  if (routeMap || !window.L) return;
  routeMap = L.map("route-map", { scrollWheelZoom: false, zoomControl: true });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(routeMap);
  routeLayerGroup = L.layerGroup().addTo(routeMap);
}

function drawRouteMap(variant, daySelection = "all") {
  initializeRouteMap();
  const mapElement = $("#route-map");
  if (!routeMap || !routeLayerGroup) {
    mapElement.innerHTML = '<p class="map-unavailable">지도 라이브러리를 불러오지 못했습니다. 장소별 Google 지도 링크를 이용하세요.</p>';
    return;
  }
  routeLayerGroup.clearLayers();
  const days = variant.days
    .map((day, index) => ({ day, index }))
    .filter(({ day, index }) => day.stops.length && (daySelection === "all" || Number(daySelection) === index));
  const allPoints = [];
  const legend = [];

  days.forEach(({ day, index }) => {
    const color = routeColors[index % routeColors.length];
    const points = day.stops.map((stop) => [stop.latitude, stop.longitude]);
    allPoints.push(...points);
    if (points.length > 1) {
      L.polyline(points, { color, weight: 4, opacity: 0.82 }).addTo(routeLayerGroup);
    }
    day.stops.forEach((stop, stopIndex) => {
      L.circleMarker([stop.latitude, stop.longitude], {
        radius: 9,
        color,
        weight: 3,
        fillColor: "#fffdf8",
        fillOpacity: 1,
      })
        .bindTooltip(`${index + 1}일차 ${stopIndex + 1}. ${escapeHtml(stop.place_name)}`, { direction: "top" })
        .bindPopup(`<b>${index + 1}일차 ${stopIndex + 1}. ${escapeHtml(stop.place_name)}</b><br>${escapeHtml(stop.district || "권역 미확인")}<br>장소 ${money(stop.place_cost_krw)} · 이동 ${money(stop.transfer_cost_krw)}`)
        .addTo(routeLayerGroup);
    });
    const district = day.stops[0]?.district || "인접 지역";
    legend.push(`<span><i style="background:${color}"></i>${index + 1}일차 · ${escapeHtml(district)}</span>`);
  });

  $("#route-map-legend").innerHTML = legend.join("");
  if (allPoints.length) {
    routeMap.fitBounds(L.latLngBounds(allPoints), { padding: [28, 28], maxZoom: 13 });
  }
  setTimeout(() => routeMap.invalidateSize(), 0);
}

function renderRouteMap(variant) {
  const daySelect = $("#route-day-select");
  daySelect.innerHTML = [
    '<option value="all">전체 일정</option>',
    ...variant.days.map((day, index) => day.stops.length ? `<option value="${index}">${index + 1}일차 · ${escapeHtml(day.stops[0].district || "인접 지역")}</option>` : ""),
  ].join("");
  daySelect.onchange = () => drawRouteMap(variant, daySelect.value);
  drawRouteMap(variant, "all");
}

function costDetails(variant) {
  return `
    <dl class="cost-breakdown">
      <dt>항공</dt><dd>${money(variant.flight_cost_krw)}</dd>
      <dt>숙소</dt><dd>${money(variant.stay_cost_krw)}</dd>
      <dt>관광·식사·카페</dt><dd>${money(variant.place_cost_krw)}</dd>
      <dt>일정 내 현지 이동</dt><dd>${money(variant.local_transport_cost_krw)}</dd>
      ${variant.rental_cost_krw ? `<dt>└ 렌터카</dt><dd>${money(variant.rental_cost_krw)}</dd>` : ""}
      ${variant.fuel_cost_krw ? `<dt>└ 유류비</dt><dd>${money(variant.fuel_cost_krw)}</dd>` : ""}
      ${variant.parking_cost_krw ? `<dt>└ 주차비</dt><dd>${money(variant.parking_cost_krw)}</dd>` : ""}
      <dt class="total">계산 포함 합계</dt><dd class="total">${money(variant.trip_total_krw)}</dd>
    </dl>`;
}

function renderItineraries(variants) {
  $("#variant-tabs").innerHTML = variants.map((variant, index) => `
    <button class="${index === 0 ? "active" : ""}" role="tab" data-variant="${variant.id}">${escapeHtml(variant.name)} · ${money(variant.trip_total_krw)}</button>
  `).join("");
  $("#itineraries").innerHTML = variants.map((variant, index) => `
    <section class="variant-panel ${index === 0 ? "active" : ""}" data-panel="${variant.id}">
      <div class="variant-summary">
        <div><h3>${escapeHtml(variant.name)}</h3><p>${escapeHtml(variant.summary)}</p>${costDetails(variant)}</div>
        <div><h3>장점</h3><ul>${variant.pros.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>
        <div><h3>단점</h3><ul>${variant.cons.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>
      </div>
      <div class="cost-audit">
        <div><b>계산 가정</b><ul>${variant.cost_assumptions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>
        <div><b>합계 미포함</b><ul>${variant.excluded_costs.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>
      </div>
      ${variant.days.map((day) => `
        <article class="day-card">
          <div class="day-header"><h3>${escapeHtml(day.title)}</h3><span>${day.date} · 장소 ${money(day.place_cost_krw)} · 이동 ${money(day.local_transport_cost_krw)}${day.driving_distance_km ? ` · 운전 ${day.driving_distance_km}km` : ""} · 합계 ${money(day.daily_cost_krw)}</span></div>
          <div class="timeline">
            ${day.stops.map((stop) => `
              <div class="stop">
                <div class="stop-time">${stop.start_time}<br />${stop.end_time}</div>
                <div><h4>${escapeHtml(stop.place_name)}</h4><p>${escapeHtml(stop.reason)}</p><p>${escapeHtml(stop.transfer_mode)} ${stop.transfer_minutes}분 · ${stop.transfer_distance_km}km · ${escapeHtml(stop.drawback)}</p><p>${escapeHtml(stop.rain_alternative)}</p>${offerLink(stop.maps_url, "Google 지도")}</div>
                <div class="stop-cost"><b>${money(stop.estimated_cost_krw)}</b><small>장소 ${money(stop.place_cost_krw)}<br />이동 ${money(stop.transfer_cost_krw)}${stop.parking_cost_krw ? `<br />주차 ${money(stop.parking_cost_krw)}` : ""}</small></div>
              </div>
            `).join("")}
          </div>
          ${day.notes.map((note) => `<span class="tag">${escapeHtml(note)}</span>`).join(" ")}
        </article>
      `).join("")}
    </section>
  `).join("");
  document.querySelectorAll("#variant-tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("#variant-tabs button, .variant-panel").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelector(`[data-panel="${button.dataset.variant}"]`).classList.add("active");
      const variant = variants.find((item) => item.id === button.dataset.variant);
      if (variant) renderRouteMap(variant);
    });
  });
  if (variants.length) renderRouteMap(variants[0]);
}

const verificationCategoryLabels = {
  flight: "항공",
  stay: "숙소",
  place: "장소",
  route: "교통",
  official: "공식 정보",
};

function renderVerification(result) {
  const evidence = result.evidence || [];
  $("#evidence-summary").innerHTML = evidence.length ? `
    <div class="evidence-strip">
      ${evidence.map((item) => `
        <article>
          <span class="confidence-badge confidence-${escapeHtml(item.confidence.toLowerCase())}">${escapeHtml(item.confidence)} · ${escapeHtml(item.value_status)}</span>
          <b>${escapeHtml(item.title)}</b>
          <p>${escapeHtml(item.note)}</p>
          ${item.source_url ? offerLink(item.source_url, item.source_name) : ""}
        </article>
      `).join("")}
    </div>` : "";
  $("#verification-links").innerHTML = (result.verification_links || []).map((item) => `
    <article class="verification-card">
      <span>${escapeHtml(verificationCategoryLabels[item.category] || item.category)}</span>
      <h3>${escapeHtml(item.platform)}</h3>
      <b>${escapeHtml(item.title)}</b>
      <p>${escapeHtml(item.note)}</p>
      ${offerLink(item.url, "동일 조건 확인")}
    </article>
  `).join("");
}

function modeBanner(result) {
  if (result.data_mode === "guided_research") {
    return `<div class="mode-banner research"><b>가이드형 웹 검증 모드</b> 여행 API가 연결되지 않아 금액은 일정 계산용 추정치입니다. 앱이 비교 플랫폼의 결제 가격을 자동 수집한 것은 아니며, 아래 링크에서 날짜·인원·수하물 조건을 확인하세요.</div>`;
  }
  if (result.data_mode === "mixed") {
    return `<div class="mode-banner mixed"><b>혼합 데이터 모드</b> 일부는 실시간 공급자 응답이고, ${escapeHtml((result.sample_verticals || []).join("·"))} 영역은 계획용 추정치입니다.</div>`;
  }
  if (result.data_mode === "sample" || result.sample_mode) {
    return `<div class="mode-banner"><b>체험용 샘플 모드</b> 가격·재고는 실제 예약에 사용할 수 없습니다.</div>`;
  }
  return `<div class="mode-banner live"><b>라이브 공급자 결과</b> 검색 후 가격과 재고가 바뀔 수 있으니 예약 직전 새로고침하세요.</div>`;
}

function renderResult(result) {
  currentTrip = result;
  $("#results").classList.remove("hidden");
  $("#result-title").textContent = `${result.request.destination_city} · ${result.request.departure_date} 출발`;
  $("#mode-banner").innerHTML = modeBanner(result);
  $("#narrative").innerHTML = result.narrative ? `<div class="narrative-card">${escapeHtml(result.narrative)}</div>` : "";
  $("#warnings").innerHTML = result.warnings.length ? `<div class="warning-list"><ul>${result.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul></div>` : "";
  renderVerification(result);
  renderFlights(result.flights);
  renderStays(result.stays);
  renderItineraries(result.itineraries);
  $("#unresolved").innerHTML = `<ul class="check-list">${result.unresolved_checks.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  $("#results").scrollIntoView({ behavior: "smooth", block: "start" });
  setStatus(`계획 ${result.id.slice(0, 8)} · ${result.status === "ready" ? "계산 완료" : "부분 결과"}`);
}

async function submitTrip(event) {
  event.preventDefault();
  const button = $("#submit-button");
  button.disabled = true;
  setStatus("항공·숙소·장소를 조회하고 동선을 계산하는 중입니다…", true);
  try {
    const result = await api("/api/trips", { method: "POST", body: JSON.stringify(formPayload(event.currentTarget)) });
    renderResult(result);
  } catch (error) {
    setStatus(`설계 실패: ${error.message}`);
  } finally {
    button.disabled = false;
  }
}

async function refreshTrip() {
  if (!currentTrip) return;
  setStatus("현재 가격·재고와 장소를 다시 확인하는 중입니다…", true);
  try { renderResult(await api(`/api/trips/${currentTrip.id}/refresh`, { method: "POST" })); }
  catch (error) { setStatus(`새로고침 실패: ${error.message}`); }
}

async function replanTrip() {
  if (!currentTrip) return;
  setStatus("우천에 맞춰 실내 중심 동선을 다시 계산하는 중입니다…", true);
  try {
    renderResult(await api(`/api/trips/${currentTrip.id}/replan`, {
      method: "POST",
      body: JSON.stringify({ weather: "비", notes: "우천 기준 실내 장소 우선" }),
    }));
  } catch (error) { setStatus(`재계획 실패: ${error.message}`); }
}

async function loadProviderHealth() {
  try {
    const providers = await api("/api/providers/health");
    $("#provider-health").innerHTML = providers.map((provider) => `
      <article class="provider-card"><b><span class="provider-dot ${provider.mode === "live" ? "live" : provider.mode === "research" ? "research" : ""}"></span>${escapeHtml(provider.name)}</b><p>${escapeHtml(provider.detail)}</p></article>
    `).join("");
  } catch (error) {
    $("#provider-health").innerHTML = `<p>공급자 상태를 불러오지 못했습니다: ${escapeHtml(error.message)}</p>`;
  }
}

async function loadProfile() {
  try {
    const profile = await api("/api/profile");
    if (!profile) return;
    document.querySelector(`[name="budget_krw"]`).value = profile.budget_krw || 2000000;
    document.querySelector(`[name="pace"]`).value = profile.pace;
    document.querySelector(`[name="interests"]`).value = profile.interests.join(", ");
    document.querySelector(`[name="dietary_needs"]`).value = profile.dietary_needs.join(", ");
    document.querySelector(`[name="mobility_needs"]`).value = profile.mobility_needs.join(", ");
    document.querySelector(`[name="save_profile"]`).checked = true;
    document.querySelectorAll(`[name="stay_types"]`).forEach((input) => { input.checked = profile.stay_types.includes(input.value); });
  } catch (_) { /* First run has no profile. */ }
}

document.addEventListener("DOMContentLoaded", () => {
  setDefaultDates();
  loadDestinations();
  $("#destination-country").addEventListener("change", updateCities);
  $("#trip-form").addEventListener("submit", submitTrip);
  $("#refresh-button").addEventListener("click", refreshTrip);
  $("#replan-button").addEventListener("click", replanTrip);
  $("#conversation-form").addEventListener("submit", (event) => {
    event.preventDefault();
    sendConversation($("#conversation-input").value);
  });
  document.querySelectorAll("[data-example]").forEach((button) => button.addEventListener("click", () => sendConversation(button.dataset.example)));
  $("#next-question").addEventListener("click", (event) => {
    const button = event.target.closest("[data-answer]");
    if (button) sendConversation(button.dataset.answer);
  });
  $("#constraint-panel").addEventListener("click", async (event) => {
    const finalize = event.target.closest("#finalize-session");
    if (finalize) { await finalizeSession(); return; }
    const hardnessButton = event.target.closest("[data-hardness]");
    if (hardnessButton) {
      const key = hardnessButton.dataset.hardness;
      const item = currentSession.constraints[key];
      await patchConstraint(key, item.value, item.hardness === "hard" ? "soft" : "hard");
      return;
    }
    const editButton = event.target.closest("[data-edit]");
    if (editButton) {
      const key = editButton.dataset.edit;
      const item = currentSession.constraints[key];
      const card = editButton.closest(".constraint-item");
      if (!card.querySelector(".constraint-edit")) {
        card.insertAdjacentHTML("beforeend", `<div class="constraint-edit"><input value="${escapeHtml(Array.isArray(item.value) ? item.value.join(", ") : item.value)}" aria-label="${escapeHtml(constraintLabels[key] || key)} 수정"><button type="button" data-save-constraint="${escapeHtml(key)}">저장</button></div>`);
      }
      return;
    }
    const saveButton = event.target.closest("[data-save-constraint]");
    if (saveButton) {
      const card = saveButton.closest(".constraint-item");
      await patchConstraint(saveButton.dataset.saveConstraint, card.querySelector(".constraint-edit input").value);
    }
  });
  loadProviderHealth();
  loadProfile();
});
