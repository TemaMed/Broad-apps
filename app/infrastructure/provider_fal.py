from app.application.ports.provider import ContentProvider, ProviderSubmission, ProviderResult
from app.domain.enums import GenerationKind
import fal_client

class FalProvider(ContentProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def submit(self, *, kind: GenerationKind, prompt: str, input_image_url: str | None,
                     webhook_url: str | None, idempotency_key: str) -> ProviderSubmission:
        import os
        os.environ["FAL_KEY"] = self.api_key

        if kind == GenerationKind.VIDEO:
            endpoint = "fal-ai/wan-25-preview/image-to-video" if input_image_url else "fal-ai/wan-25-preview/text-to-video"
            args = {"prompt": prompt}
            if input_image_url:
                args["image_url"] = input_image_url
        else:
            endpoint = "fal-ai/fast-sdxl"
            args = {"prompt": prompt}
            if input_image_url:
                args["image_url"] = input_image_url

        handle = fal_client.submit(
            endpoint,
            arguments=args,
            webhook_url=webhook_url,
            headers={"Idempotency-Key": idempotency_key},
        )
        return ProviderSubmission(request_id=handle.request_id)

    async def get_status(self, *, request_id: str) -> ProviderResult:
        import os
        os.environ["FAL_KEY"] = self.api_key

        status = fal_client.status(request_id)
        st = (status.get("status") or "").lower()
        if st in ("in_queue", "queued"):
            return ProviderResult(status="queued")
        if st in ("in_progress", "processing"):
            return ProviderResult(status="processing")
        if st in ("completed", "succeeded", "success"):
            result = fal_client.result(request_id)
            url = None
            if isinstance(result, dict):
                if "video" in result and isinstance(result["video"], dict):
                    url = result["video"].get("url")
                elif "images" in result and result["images"]:
                    url = result["images"][0].get("url")
                elif "image" in result and isinstance(result["image"], dict):
                    url = result["image"].get("url")
            return ProviderResult(status="completed", result_url=url)
        if st in ("failed", "error"):
            return ProviderResult(status="failed", error=status.get("error") or "provider failed")
        return ProviderResult(status="processing")
