from StrateQueue.brokers.Alpaca.request_creators.types.zipline_based import AlpacaRequestZiplineBased


class RequestCreatorFactory:
    _registry = {
        AlpacaRequestZiplineBased.ID: AlpacaRequestZiplineBased
    }

    @staticmethod
    def has(request_creator_id: str):
        return request_creator_id in RequestCreatorFactory._registry


    @staticmethod
    def get(request_creator_id:str, broker):
        if request_creator_id not in RequestCreatorFactory._registry:
            raise KeyError("The alpaca request creator is unknown")

        return RequestCreatorFactory._registry.get(request_creator_id)(broker)