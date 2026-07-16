from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import Database
from .models import (
    ConstraintPatch,
    DestinationBootstrapRequest,
    DestinationPack,
    PlanningMessageRequest,
    PlanningSession,
    PlanningSessionCreate,
    ProviderHealth,
    ReplanRequest,
    TravelerProfile,
    TripRequest,
    TripResult,
)
from .service import TravelPlannerService


PACKAGE_DIR = Path(__file__).resolve().parent
database = Database(settings.db_path)
planner = TravelPlannerService(settings, database)

app = FastAPI(
    title="한국인 해외여행 설계 에이전트",
    version="0.3.0",
    description="검증 도시의 여행 동선을 만들고 신규 목적지는 공식 출처 기반 초기세팅부터 시작합니다.",
)
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"api_docs": "/docs"},
    )


@app.post("/api/trips", response_model=TripResult, status_code=status.HTTP_201_CREATED)
async def create_trip(payload: TripRequest) -> TripResult:
    try:
        return await planner.create_trip(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/planning-sessions", response_model=PlanningSession, status_code=status.HTTP_201_CREATED)
async def create_planning_session(payload: PlanningSessionCreate) -> PlanningSession:
    return await planner.create_planning_session(payload)


@app.get("/api/planning-sessions/{session_id}", response_model=PlanningSession)
async def get_planning_session(session_id: str) -> PlanningSession:
    session = planner.get_planning_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="여행 초안을 찾을 수 없습니다.")
    return session


@app.post("/api/planning-sessions/{session_id}/messages", response_model=PlanningSession)
async def add_planning_message(session_id: str, payload: PlanningMessageRequest) -> PlanningSession:
    session = await planner.add_planning_message(session_id, payload)
    if not session:
        raise HTTPException(status_code=404, detail="여행 초안을 찾을 수 없습니다.")
    return session


@app.patch("/api/planning-sessions/{session_id}/constraints", response_model=PlanningSession)
async def patch_planning_constraints(session_id: str, payload: ConstraintPatch) -> PlanningSession:
    session = planner.patch_planning_constraints(session_id, payload)
    if not session:
        raise HTTPException(status_code=404, detail="여행 초안을 찾을 수 없습니다.")
    return session


@app.post("/api/planning-sessions/{session_id}/finalize", response_model=TripResult)
async def finalize_planning_session(session_id: str) -> TripResult:
    try:
        result = await planner.finalize_planning_session(session_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not result:
        raise HTTPException(status_code=404, detail="여행 초안을 찾을 수 없습니다.")
    return result


@app.delete("/api/planning-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planning_session(session_id: str) -> Response:
    if not planner.delete_planning_session(session_id):
        raise HTTPException(status_code=404, detail="여행 초안을 찾을 수 없습니다.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/trips/{trip_id}", response_model=TripResult)
async def get_trip(trip_id: str) -> TripResult:
    trip = database.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="여행 계획을 찾을 수 없습니다.")
    return trip


@app.post("/api/trips/{trip_id}/refresh", response_model=TripResult)
async def refresh_trip(trip_id: str) -> TripResult:
    trip = await planner.refresh_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="여행 계획을 찾을 수 없습니다.")
    return trip


@app.post("/api/trips/{trip_id}/replan", response_model=TripResult)
async def replan_trip(trip_id: str, payload: ReplanRequest) -> TripResult:
    trip = await planner.replan_trip(trip_id, payload)
    if not trip:
        raise HTTPException(status_code=404, detail="여행 계획을 찾을 수 없습니다.")
    return trip


@app.get("/api/profile", response_model=TravelerProfile | None)
async def get_profile() -> TravelerProfile | None:
    return database.get_profile()


@app.put("/api/profile", response_model=TravelerProfile)
async def put_profile(payload: TravelerProfile) -> TravelerProfile:
    return database.save_profile(payload)


@app.delete("/api/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile() -> Response:
    database.delete_profile()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/providers/health", response_model=list[ProviderHealth])
async def provider_health() -> list[ProviderHealth]:
    return planner.provider_health()


@app.get("/api/destinations", response_model=list[DestinationPack])
async def list_destinations(include_provisional: bool = True) -> list[DestinationPack]:
    return planner.destinations.list(include_provisional=include_provisional)


@app.post("/api/destinations/bootstrap", response_model=DestinationPack, status_code=status.HTTP_201_CREATED)
async def bootstrap_destination(payload: DestinationBootstrapRequest) -> DestinationPack:
    return planner.destinations.bootstrap(payload.query)


@app.get("/api/destinations/{slug}", response_model=DestinationPack)
async def get_destination(slug: str) -> DestinationPack:
    destination = planner.destinations.get(slug)
    if not destination:
        raise HTTPException(status_code=404, detail="목적지 초기세팅 정보를 찾을 수 없습니다.")
    return destination


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
