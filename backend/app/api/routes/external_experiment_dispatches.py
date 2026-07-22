"""外部实验任务接收和查询接口。"""

from fastapi import APIRouter, Depends, Query

from app.api.external_auth import require_external_api_auth
from app.runtime import get_external_experiment_dispatch_service
from app.schemas.external_experiment_dispatch import (
    ExternalExperimentDispatchCreateRequest,
    ExternalExperimentDispatchCreateResponse,
    ExternalExperimentDispatchDetailResponse,
    ExternalExperimentDispatchListItem,
    ExternalExperimentDispatchListResponse,
)


router = APIRouter(
    prefix="/api/external-experiment-dispatches",
    tags=["external-experiment-dispatches"],
    dependencies=[Depends(require_external_api_auth)],
)


@router.post("", response_model=ExternalExperimentDispatchCreateResponse)
def create_dispatch(
    payload: ExternalExperimentDispatchCreateRequest,
) -> ExternalExperimentDispatchCreateResponse:
    """接收外部系统下发的实验任务批次。"""
    record = get_external_experiment_dispatch_service().create_dispatch(payload)
    return ExternalExperimentDispatchCreateResponse(
        dispatch_id=record["dispatch_id"],
        status=record["status"],
        received_at=record["received_at"],
    )


@router.get("", response_model=ExternalExperimentDispatchListResponse)
def list_dispatches(
    keyword: str | None = Query(default=None, max_length=200),
) -> ExternalExperimentDispatchListResponse:
    """查询已接收的外部实验任务批次。"""
    items = get_external_experiment_dispatch_service().list_dispatches(keyword)
    return ExternalExperimentDispatchListResponse(
        items=[ExternalExperimentDispatchListItem.model_validate(item) for item in items]
    )


@router.get("/{dispatch_id}", response_model=ExternalExperimentDispatchDetailResponse)
def get_dispatch(dispatch_id: str) -> ExternalExperimentDispatchDetailResponse:
    """查询指定外部实验任务批次详情。"""
    record = get_external_experiment_dispatch_service().get_dispatch(dispatch_id)
    return ExternalExperimentDispatchDetailResponse.model_validate(record)
