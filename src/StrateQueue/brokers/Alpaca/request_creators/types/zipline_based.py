from StrateQueue.brokers.Alpaca.request_creators.request_builders import BaseDataRequestBuilder, \
    SideNotionalOrQuantityRequestBuilder, OrderClassRequestBuilder, ExtraMetadataRequestBuilder, \
    LimitPriceRequestBuilder, StopPriceRequestBuilder, TrailDateRequestBuilder
from StrateQueue.brokers.Alpaca.request_creators.request_creator_base import AlpacaRequestCreatorBase


class AlpacaRequestZiplineBased(AlpacaRequestCreatorBase):

    ID = "AlpacaRequestZiplineBased"

    def request_builders(self, request_cls):
        base_builders = [
            BaseDataRequestBuilder,
            SideNotionalOrQuantityRequestBuilder,
            ExtraMetadataRequestBuilder
        ]

        from alpaca.trading.requests import (
            LimitOrderRequest,
            MarketOrderRequest,
            StopLimitOrderRequest,
            StopOrderRequest,
            TrailingStopOrderRequest
        )

        if request_cls == MarketOrderRequest:
            base_builders.append(OrderClassRequestBuilder)
        elif request_cls == LimitOrderRequest:
            base_builders.append(OrderClassRequestBuilder)
            base_builders.append(LimitPriceRequestBuilder)
        elif request_cls == StopOrderRequest:
            base_builders.append(OrderClassRequestBuilder)
            base_builders.append(StopPriceRequestBuilder)
        elif request_cls == StopLimitOrderRequest:
            base_builders.append(OrderClassRequestBuilder)
            base_builders.append(LimitPriceRequestBuilder)
            base_builders.append(StopPriceRequestBuilder)
        elif request_cls == TrailingStopOrderRequest:
            base_builders.append(TrailDateRequestBuilder)

        return base_builders
