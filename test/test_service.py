import jwt
import bcrypt
import pytest
import config

from model import UserDao, TweetDao
from service import UserService, TweetService
from sqlalchemy import create_engine, text

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_service():
    return UserService(UserDao(database), config.test_config)

@pytest.fixture
def tweet_service():
    return TweetService(TweetDao(database))

def setup_function():
    # Create a test user
    hashed_password = bcrypt.hashpw(b"test password", bcrypt.gensalt())
    new_users = [
        {
            'id': 1,
            'email': 'songew@gmail.com',
            'hashed_password': hashed_password,
            'name': '송은우',
            'profile': 'test profile'
        },
        {
            'id': 2,
            'name': '김철수',
            'email': 'tet@gmail.com',
            'profile': 'test profile',
            'hashed_password': hashed_password
        }
    ]
    database.execute(text("""
            INSERT INTO users (
                id,
                name,
                email,
                profile,
                hashed_password
            ) VALUES (
                :id,
                :name,
                :email,
                :profile,
                :hashed_password
            )
        """), new_users)

    database.execute(text("""
            INSERT INTO tweets (
                user_id,
                tweet
            ) VALUES (
                2,
                "Hello World!"
            )
        """))


def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))

def get_user(user_id):
    row = database.execute(text("""
        SELECT 
            id,
            name,
            email,
            profile
        FROM users
        WHERE id = :user_id
    """), {
        'user_id': user_id
    }).fetchone()

    return {
        'id': row['id'],
        'name': row['name'],
        'email': row['email'],
        'profile': row['profile']
    } if row else None

def get_follow_list(user_id):
    rows = database.execute(text("""
        SELECT follow_user_id as id
        FROM users_follow_list
        WHERE user_id = :user_id
    """), {
        'user_id': user_id
    }).fetchall()

    return [int(row['id']) for row in rows]

def test_create_new_user(user_service):
    new_user = {
        'name': '홍길동',
        'email': 'hong@test.com',
        'profile': '동쪽에서 번쩍, 서쪽에서 번쩍',
        'password': 'test1234'
    }

    new_user_id = user_service.create_new_user(new_user)
    created_user = get_user(new_user_id)

    assert created_user == {
        'id': new_user_id,
        'name': new_user['name'],
        'email': new_user['email'],
        'profile': new_user['profile']
    }

def test_login(user_service):
    assert user_service.login({
        'email': 'songew@gmail.com',
        'password': 'test password'
    })

    # 잘못된 비번으로 로그인했을 때 False가 리턴되는지 테스트
    assert not user_service.login({
        'email': 'songew@gmail.com',
        'password': 'test1234'
    })


def test_generate_access_token(user_service):
    ## token 생성후 decode 해서 동일한 유저 아이디가 나오는지 테스트
    token = user_service.generate_access_token(1)
    payload = jwt.decode(token, config.JWT_SECRET_KEY, 'HS256')

    assert payload['user_id'] == 1


def test_follow(user_service):
    user_service.follow(1, 2)
    follow_list = get_follow_list(1)

    assert follow_list == [2]


def test_unfollow(user_service):
    user_service.follow(1, 2)
    user_service.unfollow(1, 2)
    follow_list = get_follow_list(1)

    assert follow_list == []


def test_tweet(tweet_service):
    tweet_service.tweet(1, "tweet test")
    timeline = tweet_service.get_timeline(1)

    assert timeline == [
        {
            'user_id': 1,
            'tweet': 'tweet test'
        }
    ]


def test_timeline(user_service, tweet_service):
    tweet_service.tweet(1, "tweet test")
    tweet_service.tweet(2, "tweet test 2")
    user_service.follow(1, 2)

    timeline = tweet_service.get_timeline(1)

    assert timeline == [
        {
            'user_id': 2,
            'tweet': 'Hello World!'
        },
        {
            'user_id': 1,
            'tweet': 'tweet test'
        },
        {
            'user_id': 2,
            'tweet': 'tweet test 2'
        }
    ]