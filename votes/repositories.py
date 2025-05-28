from django.db import IntegrityError, transaction

from .models import CommentVote, PostVote


class VoteRepository:
    @staticmethod
    def vote_post(post_id: int, user_id: int, is_upvote: bool) -> dict:
        """
        Add or update a vote on a post
        
        Returns:
            dict with vote details and counts
        """
        try:
            with transaction.atomic():
                # Try to get existing vote
                try:
                    vote = PostVote.objects.get(post_id=post_id, user_id=user_id)
                    
                    # If vote exists with same value, remove it (toggle off)
                    if vote.is_upvote == is_upvote:
                        vote.delete()
                        action = "removed"
                    else:
                        # If vote exists with different value, update it
                        vote.is_upvote = is_upvote
                        vote.save()
                        action = "changed"
                except PostVote.DoesNotExist:
                    # Create new vote
                    PostVote.objects.create(
                        post_id=post_id,
                        user_id=user_id,
                        is_upvote=is_upvote
                    )
                    action = "added"
                    
                # Get updated vote counts
                upvotes = PostVote.objects.filter(post_id=post_id, is_upvote=True).count()
                downvotes = PostVote.objects.filter(post_id=post_id, is_upvote=False).count()
                
                return {
                    "post_id": post_id,
                    "action": action,
                    "vote_type": "upvote" if is_upvote else "downvote",
                    "upvotes": upvotes,
                    "downvotes": downvotes,
                    "score": upvotes - downvotes
                }
        except IntegrityError:
            raise ValueError("Invalid post or user")

    @staticmethod
    def vote_comment(comment_id: int, user_id: int, is_upvote: bool) -> dict:
        """
        Add or update a vote on a comment
        
        Returns:
            dict with vote details and counts
        """
        try:
            with transaction.atomic():
                # Try to get existing vote
                try:
                    vote = CommentVote.objects.get(comment_id=comment_id, user_id=user_id)
                    
                    # If vote exists with same value, remove it (toggle off)
                    if vote.is_upvote == is_upvote:
                        vote.delete()
                        action = "removed"
                    else:
                        # If vote exists with different value, update it
                        vote.is_upvote = is_upvote
                        vote.save()
                        action = "changed"
                except CommentVote.DoesNotExist:
                    # Create new vote
                    CommentVote.objects.create(
                        comment_id=comment_id,
                        user_id=user_id,
                        is_upvote=is_upvote
                    )
                    action = "added"
                    
                # Get updated vote counts
                upvotes = CommentVote.objects.filter(comment_id=comment_id, is_upvote=True).count()
                downvotes=CommentVote.objects.filter(comment_id=comment_id, is_upvote=False).count()
                
                return {
                    "comment_id": comment_id,
                    "action": action,
                    "vote_type": "upvote" if is_upvote else "downvote",
                    "upvotes": upvotes,
                    "downvotes": downvotes,
                    "score": upvotes - downvotes
                }
        except IntegrityError:
            raise ValueError("Invalid comment or user")

    @staticmethod
    def get_post_votes(post_id: int) -> dict:
        """Get vote counts for a post"""
        upvotes = PostVote.objects.filter(post_id=post_id, is_upvote=True).count()
        downvotes = PostVote.objects.filter(post_id=post_id, is_upvote=False).count()
        
        return {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "score": upvotes - downvotes
        }

    @staticmethod
    def get_comment_votes(comment_id: int) -> dict:
        """Get vote counts for a comment"""
        upvotes = CommentVote.objects.filter(comment_id=comment_id, is_upvote=True).count()
        downvotes = CommentVote.objects.filter(comment_id=comment_id, is_upvote=False).count()
        
        return {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "score": upvotes - downvotes
        }

    @staticmethod
    def get_user_post_vote(post_id: int, user_id: int) -> dict:
        """Get a user's vote for a post"""
        try:
            vote = PostVote.objects.get(post_id=post_id, user_id=user_id)
            return {"voted": True, "is_upvote": vote.is_upvote}
        except PostVote.DoesNotExist:
            return {"voted": False}

    @staticmethod
    def get_user_comment_vote(comment_id: int, user_id: int) -> dict:
        """Get a user's vote for a comment"""
        try:
            vote = CommentVote.objects.get(comment_id=comment_id, user_id=user_id)
            return {"voted": True, "is_upvote": vote.is_upvote}
        except CommentVote.DoesNotExist:
            return {"voted": False}