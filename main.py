from fastapi import FastAPI,Request,HTTPException,status,Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from schema import PostCreate,PostResponse
from typing import Annotated
from schema2 import UserCreate,UserResponse,PostCreate2,PostResponse2,UserUpdate,PostUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session
import models
from database import Base, engine, get_db
##creating ne table if exist not need of creation
Base.metadata.create_all(bind=engine)
##creating the object of fastapi (app)
app = FastAPI()
templates= Jinja2Templates(directory="templates")
## Declaring the list of dictionaries
posts: list[dict] = [
    {
        "id": 1,
        "title": "FastAPI is awesome",
        "content": "this framework is really easy to use and super fast.",
        "date_posted": "april 20, 2025",
    },
    {
        "id": 2,
        "author": "jane doe",
        "title": "python is great for web development",
        "content": "python is a great language for web development, and fastapi makes it even better",
        "date_posted": "april 21, 2025",
    },
]

@app.get("/",response_class=HTMLResponse,include_in_schema=False)
@app.get("/posts",response_class=HTMLResponse)
def home():
    return f"<h1>{posts[0]['title']}</h1>"
@app.get("/template")
def template(request:Request):
    return templates.TemplateResponse(request,"home.html")
@app.get("/template2")
def template2(request:Request):
    return templates.TemplateResponse(request,"home2.html",{"posts":posts})
##posts get to fetch the exisiting data
@app.get("/api/post")
def get_posts():
    return posts
##Pydantic Data Validations
@app.get("/api/pydantic/{post_id}",response_model=PostResponse)
def get_post(post_id:int):
    for post in posts:
        if post.get("id")==post_id:
           return post
    raise HTTPException (status_code=status.HTTP_404_NOT_FOUND,detail="Post Not Found")

@app.get("/api/pydantic",response_model=list[PostResponse])
def pydantic():
    return posts
## to create the post and response according to need
@app.post(
    "/api/pydantic",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": "April 23, 2025",
    }
    posts.append(new_post)
    return new_post


##User and Post With Db apps will use sqlachemdy to crate tables and data in it.
##Get User
@app.get("/api/users", response_model=list[UserResponse])
def get_all_users(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User))
    posts = result.scalars().all()
    return posts

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.id == user_id),
    )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

##enter user id and get its all posts
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse2])
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts



##create user
@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.username == user.username),
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    result = db.execute(
        select(models.User).where(models.User.email == user.email),
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    new_user = models.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
##update the user info
@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_update.username is not None and user_update.username != user.username:
        result = db.execute(
            select(models.User).where(models.User.username == user_update.username),
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(
            select(models.User).where(models.User.email == user_update.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    db.commit()
    db.refresh(user)
    return user

##delete user
@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()




##Get all the posts
@app.get("/api/sql/posts", response_model=list[PostResponse2])
def get_sql_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts




##create the post
@app.post(
    "/api/sql/posts",
    response_model=PostResponse2,
    status_code=status.HTTP_201_CREATED,
)
def create_sql_post(post: PostCreate2, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

## get post by id
@app.get("/api/sql/posts/{post_id}", response_model=PostResponse2)
def get_sql_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.put("/api/sql/posts/{post_id}", response_model=PostResponse2)
def update_post_full(
    post_id: int,
    post_data: PostCreate2,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post_data.user_id != post.user_id:
        result = db.execute(
            select(models.User).where(models.User.id == post_data.user_id),
        )
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    db.commit()
    db.refresh(post)
    return post

@app.delete("/api//sql/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    db.delete(post)
    db.commit()
