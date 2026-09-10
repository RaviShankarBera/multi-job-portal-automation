import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest


@pytest.mark.asyncio
async def test_register_user(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    data = RegisterRequest(
        email="service@example.com",
        password="password123",
        full_name="Service User",
    )
    result = await auth_service.register(data)
    assert result.access_token is not None
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    data = RegisterRequest(
        email="duplicate@example.com",
        password="password123",
        full_name="First User",
    )
    await auth_service.register(data)

    # Try to register again
    with pytest.raises(Exception) as exc_info:
        await auth_service.register(data)
    assert "Email already registered" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_login_user(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    
    # Register user
    register_data = RegisterRequest(
        email="login@example.com",
        password="password123",
        full_name="Login User",
    )
    await auth_service.register(register_data)
    
    # Login
    login_data = LoginRequest(
        email="login@example.com",
        password="password123",
    )
    result = await auth_service.login(login_data)
    assert result.access_token is not None
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    
    # Register user
    register_data = RegisterRequest(
        email="wrong@example.com",
        password="password123",
        full_name="Wrong User",
    )
    await auth_service.register(register_data)
    
    # Login with wrong password
    login_data = LoginRequest(
        email="wrong@example.com",
        password="wrongpassword",
    )
    with pytest.raises(Exception) as exc_info:
        await auth_service.login(login_data)
    assert "Incorrect email or password" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    
    # Register user
    register_data = RegisterRequest(
        email="getuser@example.com",
        password="password123",
        full_name="Get User",
    )
    token = await auth_service.register(register_data)
    
    # Get user by ID (extract from token)
    from jose import jwt
    from app.core.config import settings
    
    payload = jwt.decode(
        token.access_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    user_id = int(payload["sub"])
    
    user = await auth_service.get_current_user(user_id)
    assert user is not None
    assert user.email == "getuser@example.com"
    assert user.full_name == "Get User"