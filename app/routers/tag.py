from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.article import Article, Tag, article_tags
from app.models.user import User
from app.schemas.tag import TagCreate, TagOut
from app.utils.dependencies import get_current_admin_user, get_db

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=list[TagOut])
def get_all_tags(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tags"""
    tags = db.query(Tag).offset(skip).limit(limit).all()
    return tags


@router.get("/popular", response_model=list[dict])
def get_popular_tags(limit: int = 20, db: Session = Depends(get_db)):
    """Get popular tags with article count"""

    popular_tags = (
        db.query(
            Tag.id,
            Tag.name,
            func.count(article_tags.c.article_id).label("article_count"),
        )
        .outerjoin(article_tags, Tag.id == article_tags.c.tag_id)
        .group_by(Tag.id, Tag.name)
        .order_by(func.count(article_tags.c.article_id).desc())
        .limit(limit)
        .all()
    )

    return [
        {"id": tag.id, "name": tag.name, "article_count": tag.article_count}
        for tag in popular_tags
    ]


@router.get("/{tag_name}", response_model=TagOut)
def get_tag_by_name(tag_name: str, db: Session = Depends(get_db)):
    """Get tag by name"""
    tag = db.query(Tag).filter(Tag.name == tag_name.lower()).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    return tag


@router.post("/", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create new tag (admin only)"""

    # Check if tag already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag.name.lower()).first()

    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tag already exists"
        )

    new_tag = Tag(name=tag.name.lower())
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)

    return new_tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete tag (admin only)"""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    db.delete(tag)
    db.commit()
    return None


@router.get("/{tag_name}/articles")
def get_articles_by_tag(
    tag_name: str, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    """Get all articles with specific tag"""
    tag = db.query(Tag).filter(Tag.name == tag_name.lower()).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    articles = (
        db.query(Article)
        .join(Article.tags)
        .filter(Tag.id == tag.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return articles
