from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

# Valid trigger types - only meaningful ones that can actually trigger
TRIGGER_TYPES = {
    "price_below": "Notify when price drops below target value",
    "price_drop": "Notify when price drops (requires target value)",
    "price_rise": "Notify when price rises above target value",
    "discount": "Notify when discount percent reaches target value",
    "rating_drop": "Notify when rating drops below target value",
    "views_reach": "Notify when number of views reaches target value (OLX, PROM)",
    "reviews_reach": "Notify when number of reviews reaches target value (ALLO)",
    "in_stock": "Notify when product becomes available",
    "back_in_stock": "Alias for in_stock (product restocked)",
    "trade_in_available": "Notify when trade-in becomes available (ALLO)",
    "credit_available": "Notify when credit option becomes available (ALLO)",
    "color_change": "Notify when product color changes (ALLO)",
    "memory_variant_change": "Notify when memory variant changes (ALLO)",
    "cashback_reach": "Notify when cashback reaches target amount (ALLO)",
    "delivery_available": "Notify when delivery becomes available (Comfy/Foxtrot)",
    "pickup_available": "Notify when pickup becomes available (Comfy/Foxtrot)",
    "personal_price_available": "Notify when personal price becomes available (Comfy)",
    "gift_offer_available": "Notify when gift offer becomes available (Foxtrot)",
    "any_change": "Notify when any relevant field changes",
}


class TrackerBase(BaseModel):
    url: str
    network: str
    trigger_type: str
    trigger_value: float | None = None

    @field_validator('trigger_type')
    @classmethod
    def validate_trigger_type(cls, v: str) -> str:
        if v not in TRIGGER_TYPES:
            raise ValueError(
                f"trigger_type must be one of {list(TRIGGER_TYPES.keys())}. "
                f"Got: {v}"
            )
        return v


class TrackerCreate(TrackerBase):
    pass


class TrackerResponse(BaseModel):
    id: int
    url: str
    network: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TriggerResponse(BaseModel):
    id: int
    tracker_id: int
    trigger_type: str
    trigger_value: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TrackerWithTriggersResponse(TrackerResponse):
    triggers: list[TriggerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TrackerUpdate(BaseModel):
    title: str | None = None
    last_price: float | None = None
    last_old_price: float | None = None
    last_discount_percent: float | None = None
    last_rating: float | None = None
    last_views: int | None = None
    last_reviews_count: int | None = None
    last_cashback_amount: float | None = None
    last_trade_in_available: bool | None = None
    last_credit_available: bool | None = None
    last_color: str | None = None
    last_memory_variant: str | None = None
    last_delivery_available: bool | None = None
    last_pickup_available: bool | None = None
    last_personal_price_available: bool | None = None
    last_gift_offer_available: bool | None = None
    last_availability: bool | None = None
    last_status: str | None = None
    last_checked_at: datetime | None = None
