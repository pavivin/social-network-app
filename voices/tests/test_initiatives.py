import asyncio
from httpx import AsyncClient
import pytest
import pytest_asyncio
from voices.app.initiatives.models import Comment, Initiative
from voices.config import settings
from voices.exceptions import ObsceneLanguageError

from voices.tests.factories.initiatives import CommentFactory, InitiativeFactory
from voices.tests.factories.user import UserFactory

PAGE_INCREMENT = 1


class TestComment:
    @pytest_asyncio.fixture
    async def pagination_comment(self):
        user = await UserFactory.create()
        initiative = await InitiativeFactory.create(user=user)
        for _ in range(settings.DEFAULT_PAGE_SIZE + PAGE_INCREMENT):
            await CommentFactory.create(user=user, initiative=initiative)
        return initiative

    @pytest_asyncio.fixture
    async def comment(self):
        initiative_user = await UserFactory.create()
        comment_user = await UserFactory.create()
        initiative = await InitiativeFactory.create(user=initiative_user)
        comment: Comment = await CommentFactory.create(user=comment_user, initiative=initiative)
        await CommentFactory.create(user=initiative_user, initiative=initiative, parent_id=comment.id)
        return comment

    @pytest.mark.asyncio
    async def test_get_success(self, client: AsyncClient, comment: Comment):
        response = await client.get(f"api/initiatives/{comment.initiative_id}/comments")
        assert response.json()["code"] == 200
        assert response.json()["payload"] is not None

    @pytest.mark.asyncio
    async def test_get_correct_replies(self, client: AsyncClient, comment: Comment):
        response = await client.get(f"api/initiatives/{comment.initiative_id}/comments")
        assert response.json()["payload"]["comments"][0]["replies"] is not None

    @pytest.mark.asyncio
    async def test_get_pagination(self, client: AsyncClient, pagination_comment: Initiative):
        response = await client.get(f"api/initiatives/{pagination_comment.id}/comments")
        comments = response.json()["payload"]["comments"]
        assert len(comments) == settings.DEFAULT_PAGE_SIZE

        response = await client.get(f"api/initiatives/{pagination_comment.id}/comments?last_id={comments[-1]['id']}")
        comments = response.json()["payload"]["comments"]
        assert len(comments) == PAGE_INCREMENT

    @pytest.mark.asyncio
    async def test_get_incorrect_last_id(self, client: AsyncClient, comment: Comment):
        response = await client.get(f"api/initiatives/{comment.initiative_id}/comments?last_id=incorrect_id")
        assert response.json()["code"] == 400
        assert response.json()["exception_class"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_get_incorrect_initiative_id(self, client: AsyncClient, comment: Comment):
        response = await client.get("api/initiatives/incorrect_id/comments")
        assert response.json()["code"] == 400
        assert response.json()["exception_class"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient, comment: Comment):
        response = await client.get(f"api/initiatives/{comment.id}/comments")
        assert response.json()["code"] == 404

    @pytest.mark.asyncio
    async def test_post_success(self, token, client: AsyncClient, comment: Comment):
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"api/initiatives/{comment.initiative_id}/comments",
            json={"main_text": "Текст комментария"},
            headers=headers,
        )
        assert response.json()["code"] == 200

    @pytest.mark.asyncio
    async def test_post_obscene(self, token, client: AsyncClient, comment: Comment):
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"api/initiatives/{comment.initiative_id}/comments",
            json={"main_text": "Хуй пизда сковорода"},
            headers=headers,
        )
        assert response.json()["code"] == 400
        assert response.json()["exception_class"] == "ObsceneLanguageError"

    @pytest.mark.asyncio
    async def test_post_nonauthorized(self, client: AsyncClient, comment: Comment):
        response = await client.post(
            "api/initiatives/incorrect_id/comments",
            json={"main_text": "Текст комментария"},
        )
        assert response.json()["code"] == 401

    @pytest.mark.asyncio
    async def test_post_not_found(self, token, client: AsyncClient, comment: Comment):
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(
            f"api/initiatives/{comment.id}/comments",
            json={"main_text": "Текст комментария"},
            headers=headers,
        )
        assert response.json()["code"] == 404

    @pytest.mark.asyncio
    async def test_post_reply(self, client: AsyncClient, comment: Comment):
        await client.post(
            f"api/initiatives/{comment.initiative_id}/comments?reply_id={comment.id}",
            json={"main_text": "Текст комментария"},
        )
        response = await client.get(
            f"api/initiatives/{comment.initiative_id}/comments",
        )
        assert response.json()["payload"]["comments"][0]["replies"] is not None

    @pytest.mark.asyncio
    async def test_post_incorrect_last_id(self, token, client: AsyncClient, comment: Comment):
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post(f"api/initiatives/{comment.id}/comments?last_id=incorrect_id", headers=headers)
        assert response.json()["code"] == 400
        assert response.json()["exception_class"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_post_incorrect_initiative_id(self, token, client: AsyncClient, comment: Comment):
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("api/initiatives/incorrect_id/comments", headers=headers)
        assert response.json()["code"] == 400
        assert response.json()["exception_class"] == "ValidationError"
