from __future__ import annotations

from fastapi.testclient import TestClient

from travel_planner import main
from travel_planner.config import Settings
from travel_planner.database import Database
from travel_planner.service import TravelPlannerService


def client_for(tmp_path, monkeypatch) -> TestClient:
    settings = Settings(
        db_path=str(tmp_path / "conversation.db"),
        openai_api_key="",
        amadeus_client_id="",
        amadeus_client_secret="",
        google_maps_api_key="",
        booking_api_key="",
        booking_affiliate_id="",
        skyscanner_api_key="",
    )
    database = Database(settings.db_path)
    monkeypatch.setattr(main, "database", database)
    monkeypatch.setattr(main, "planner", TravelPlannerService(settings, database))
    return TestClient(main.app)


def test_vague_request_returns_preview_and_one_question(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    response = client.post("/api/planning-sessions", json={"message": "8월에 친구랑 LA 가고 싶어"})
    assert response.status_code == 201
    session = response.json()
    assert session["preview"]["headline"] == "로스앤젤레스 여행 가설 초안"
    assert session["constraints"]["adults"]["value"] == 2
    assert session["constraints"]["adults"]["status"] == "proposed"
    assert len(session["next_questions"]) == 1
    assert session["next_questions"][0]["key"] == "trip_days"


def test_novice_japan_request_offers_supported_city_choices(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    session = client.post(
        "/api/planning-sessions", json={"message": "처음이라 잘 모르겠어. 그냥 일본에 가고 싶어"}
    ).json()
    assert {item["city"] for item in session["preview"]["destination_candidates"]} == {"도쿄", "오사카"}
    assert session["next_questions"][0]["key"] == "destination_city"
    followup = client.post(
        f"/api/planning-sessions/{session['id']}/messages", json={"text": "추천해줘"}
    ).json()
    assert followup["constraints"]["destination_city"]["source"] == "delegated"
    assert followup["constraints"]["destination_city"]["value"] == "도쿄"
    assert followup["next_questions"][0]["id"] != session["next_questions"][0]["id"]


def test_detailed_la_request_extracts_constraints_and_finalizes(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    message = (
        "8월 LA 6박 7일 성인 남성 2명. 경유 없이 직항 필수, 침대 2개 필수, "
        "렌터카 스포츠 모델 선호, 주차 필수. 하루 특별식은 두 명 20만원 이내. "
        "사람 몰리는 곳은 피하고 유니버설은 꼭 가고 싶어."
    )
    session = client.post("/api/planning-sessions", json={"message": message}).json()
    constraints = session["constraints"]
    assert constraints["direct_required"]["value"] is True
    assert constraints["direct_required"]["hardness"] == "hard"
    assert constraints["bed_count"]["value"] == 2
    assert constraints["parking_required"]["value"] is True
    assert constraints["sports_model_preferred"]["value"] is True
    assert constraints["special_meal_budget_krw"]["value"] == 200_000
    assert constraints["avoid_crowds"]["value"] == "high"
    assert constraints["must_visit_places"]["value"] == ["유니버설 스튜디오 할리우드"]

    patched = client.patch(
        f"/api/planning-sessions/{session['id']}/constraints",
        json={"changes": [
            {"key": "departure_date", "value": "2026-08-24"},
            {"key": "return_date", "value": "2026-08-30"},
            {"key": "driver_age", "value": 30},
        ]},
    )
    assert patched.status_code == 200
    result = client.post(f"/api/planning-sessions/{session['id']}/finalize")
    assert result.status_code == 200
    trip = result.json()
    assert all(flight["stops"] == 0 for flight in trip["flights"])
    assert all((stay["bed_count"] or 0) >= 2 and stay["parking_available"] for stay in trip["stays"])
    assert all(variant["rental_cost_krw"] > 0 for variant in trip["itineraries"])
    assert all(variant["fuel_cost_krw"] > 0 for variant in trip["itineraries"])
    assert all(variant["parking_cost_krw"] > 0 for variant in trip["itineraries"])
    changed = client.patch(
        f"/api/planning-sessions/{session['id']}/constraints",
        json={"changes": [{"key": "bed_count", "value": 1}]},
    ).json()
    assert changed["final_trip_id"] is None
    assert "stay" in changed["invalidated_sections"]


def test_griffith_is_not_scheduled_before_official_sample_opening(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    trip = client.post(
        "/api/trips",
        json={
            "destination_country": "US",
            "destination_city": "로스앤젤레스",
            "destination_code": "LAX",
            "origin_airport": "ICN",
            "departure_date": "2026-08-24",
            "return_date": "2026-08-28",
            "adults": 2,
            "rooms": 1,
            "budget_krw": 6_000_000,
            "must_visit_places": ["그리피스 천문대"],
        },
    ).json()
    griffith = next(
        stop
        for day in trip["itineraries"][0]["days"]
        for stop in day["stops"]
        if "그리피스" in stop["place_name"]
    )
    assert griffith["start_time"] >= "12:00"


def test_non_consented_session_is_not_persisted_to_sqlite(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    session = client.post("/api/planning-sessions", json={"message": "도쿄 가고 싶어"}).json()
    assert main.database.get_planning_session(session["id"]) is None
    assert client.get(f"/api/planning-sessions/{session['id']}").status_code == 200


def test_provisional_destination_starts_research_without_foreign_sample_data(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    session = client.post(
        "/api/planning-sessions", json={"message": "가을에 파리로 6박 7일 가고 싶어"}
    ).json()
    assert session["constraints"]["destination_country"]["value"] == "FR"
    assert session["constraints"]["destination_status"]["value"] == "provisional"
    assert session["constraints"]["travel_month"]["value"].endswith("-10")
    assert session["destination_pack"]["slug"] == "fr-paris"
    assert session["preview"]["destination_status"] == "provisional"
    assert any(task["key"] == "entry_safety" for task in session["preview"]["research_tasks"])
    assert session["readiness"]["flight"] != "search_ready"

    result = client.post(
        "/api/trips",
        json={
            "destination_country": "FR",
            "destination_city": "파리",
            "destination_code": "PAR",
            "departure_date": "2026-10-05",
            "return_date": "2026-10-11",
            "adults": 2,
            "budget_krw": 5_000_000,
        },
    ).json()
    assert result["status"] == "partial"
    assert result["data_mode"] == "guided_research"
    assert result["flights"] == []
    assert result["stays"] == []
    assert result["places"] == []
    assert any("다른 도시의 샘플" in warning for warning in result["warnings"])


def test_unknown_destination_bootstrap_is_persisted_as_researching(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    response = client.post("/api/destinations/bootstrap", json={"query": "스페인 바르셀로나"})
    assert response.status_code == 201
    destination = response.json()
    assert destination["country_code"] == "ES"
    assert destination["city_name"] == "바르셀로나"
    assert destination["status"] == "researching"
    assert "도시·공항 코드" in destination["missing_fields"]
    assert client.get(f"/api/destinations/{destination['slug']}").status_code == 200


def test_destination_catalog_can_return_only_validated_cities(tmp_path, monkeypatch) -> None:
    client = client_for(tmp_path, monkeypatch)
    destinations = client.get("/api/destinations?include_provisional=false").json()
    assert {(item["country_code"], item["city_name"]) for item in destinations} == {
        ("JP", "도쿄"), ("JP", "오사카"), ("US", "뉴욕"), ("US", "로스앤젤레스")
    }
