from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from app.utils.dependencies import get_db, get_current_active_user
from app.schemas.comment import CommentCreate, CommentOut
from app.models.comment import Comment
from app.models.article import Article
from app.models.user import User

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.get("/article/{article_slug}", response_model=List[CommentOut])
def get_comments_by_article(
    article_slug: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all comments for a specific article"""
   
    article = db.query(Article).filter(Article.slug == article_slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    

    comments = (
        db.query(Comment)
        .filter(Comment.article_id == article.id)
        .order_by(desc(Comment.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return comments


@router.get("/{comment_id}", response_model=CommentOut)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    """Get specific comment by ID"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    return comment


@router.post("/article/{article_slug}", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    article_slug: str,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new comment on article"""

    article = db.query(Article).filter(Article.slug == article_slug).first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    

    new_comment = Comment(
        body=comment.body,
        article_id=article.id,
        user_id=current_user.id
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment


@router.put("/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int,
    comment_update: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update comment (only by comment author)"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
  
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment"
        )
   
    comment.body = comment_update.body
    db.commit()
    db.refresh(comment)
    
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete comment (by comment author or article author)"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    article = db.query(Article).filter(Article.id == comment.article_id).first()
    
    if comment.user_id != current_user.id and article.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    db.delete(comment)
    db.commit()
    return None


@router.get("/user/{username}", response_model=List[CommentOut])
def get_comments_by_user(
    username: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all comments by specific user"""

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    comments = (
        db.query(Comment)
        .filter(Comment.user_id == user.id)
        .order_by(desc(Comment.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return comments


@router.get("/user/me/comments", response_model=List[CommentOut])
def get_my_comments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all comments by current user"""
    comments = (
        db.query(Comment)
        .filter(Comment.user_id == current_user.id)
        .order_by(desc(Comment.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return comments