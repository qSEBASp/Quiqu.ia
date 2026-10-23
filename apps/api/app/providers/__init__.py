from ..models import Profile
from .base import AccountData, MatchData, ProviderError
from .demo import DemoProvider
from .henrik import HenrikProvider


def build_provider(profile: Profile, count: int = 14) -> DemoProvider | HenrikProvider:
    if profile.provider == "henrik":
        return HenrikProvider(
            api_key=profile.henrik_api_key,
            base_url="https://api.henrikdev.xyz",
        )
    return DemoProvider(count=count)


__all__ = [
    "AccountData",
    "DemoProvider",
    "HenrikProvider",
    "MatchData",
    "ProviderError",
    "build_provider",
]
