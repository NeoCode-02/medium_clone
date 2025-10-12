from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.utils.dependencies import get_db, get_current_active_user
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleOut
from app.models.article import Article, Tag
from app.models.user import User
from app.utils.redis_service import (
    increment_view,
    increment_like,
    decrement_like,
    get_views,
    get_likes
)
from slugify import slugify

router = APIRouter(prefix="/articles", tags=["Articles"])


def create_slug(title: str, db: Session) -> str:
    """Generate unique slug from title"""
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    
    while db.query(Article).filter(Article.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


def get_or_create_tags(tag_names: List[str], db: Session) -> List[Tag]:
    """Get existing tags or create new ones"""
    tags = []
    for tag_name in tag_names:
        tag_name = tag_name.strip().lower()
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
        tags.append(tag)
    return tags


@router.get("/", response_model=List[ArticleOut])
def get_articles(
    skip: int = 0,
    limit: int = 20,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all articles with optional filters"""
    query = db.query(Article)
    
    
    if tag:
        query = query.join(Article.tags).filter(Tag.name == tag.lower())
    
   
    if author:
        query = query.join(Article.author).filter(User.username == author)
    
  
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Article.title.ilike(search_term)) |
            (Article.description.ilike(search_term))
        )
    

    articles = query.order_by(desc(Article.created_at)).offset(skip).limit(limit).all()
    

    for article in articles:
        article.views_count = get_views(article.id)
        article.likes_count = get_likes(article.id)
    
    return articles


@router.get("/feed", response_model=List[ArticleOut])
def get_feed(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get personalized feed (can be enhanced with following logic)"""
    # For now, return recent articles
    # TODO: Implement following logic and filter by followed users
    articles = db.query(Article).order_by(
        desc(Article.created_at)
    ).offset(skip).limit(limit).all()
    
    for article in articles:
        article.views_count = get_views(article.id)
        article.likes_count = get_likes(article.id)
    
    return articles


@router.get("/popular", response_model=List[ArticleOut])
def get_popular_articles(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get popular articles by views"""
    articles = db.query(Article).order_by(
        desc(Article.views_count)
    ).offset(skip).limit(limit).all()
    
    for article in articles:
        article.views_count = get_views(article.id)
        article.likes_count = get_likes(article.id)
    
    return articles


@router.get("/{slug}", response_model=ArticleOut)
def get_article(slug: str, db: Session = Depends(get_db)):
    """Get article by slug and increment view count"""
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
  
    increment_view(article.id)
    article.views_count = get_views(article.id)
    article.likes_count = get_likes(article.id)
    
    return article


@router.post("/", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new article"""
    
   
    slug = create_slug(article.title, db)
    
   
    new_article = Article(
        title=article.title,
        slug=slug,
        description=article.description,
        body=article.body,
        author_id=current_user.id
    )
    
   
    if article.tags:
        new_article.tags = get_or_create_tags(article.tags, db)
    
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    
    return new_article


@router.put("/{slug}", response_model=ArticleOut)
def update_article(
    slug: str,
    article_update: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update article (only by author)"""
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    

    if article.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this article"
        )
    
    if article_update.title:
        article.title = article_update.title
        article.slug = create_slug(article_update.title, db)
    
    if article_update.description is not None:
        article.description = article_update.description
    
    if article_update.body:
        article.body = article_update.body
    
    if article_update.tags is not None:
        article.tags = get_or_create_tags(article_update.tags, db)
    
    db.commit()
    db.refresh(article)
    
    # Sync metrics
    article.views_count = get_views(article.id)
    article.likes_count = get_likes(article.id)
    
    return article


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete article (only by author)"""
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    if article.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this article"
        )
    
    db.delete(article)
    db.commit()
    return None


@router.post("/{slug}/like", status_code=status.HTTP_200_OK)
def like_article(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Like an article"""
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Increment like count in Redis
    new_count = increment_like(article.id)
    
    return {"message": "Article liked", "likes_count": new_count}


@router.delete("/{slug}/like", status_code=status.HTTP_200_OK)
def unlike_article(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Unlike an article"""
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Decrement like count in Redis
    new_count = decrement_like(article.id)
    
    return {"message": "Article unliked", "likes_count": new_count}


@router.get("/author/{username}", response_model=List[ArticleOut])
def get_articles_by_author(
    username: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all articles by specific author"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    articles = db.query(Article).filter(
        Article.author_id == user.id
    ).order_by(desc(Article.created_at)).offset(skip).limit(limit).all()
    
    for article in articles:
        article.views_count = get_views(article.id)
        article.likes_count = get_likes(article.id)
    
    return articles