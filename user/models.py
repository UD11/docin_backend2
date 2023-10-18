from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
class PDF(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    link = models.URLField()
    author = models.CharField(max_length=100)
    institution_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    upvote = models.PositiveIntegerField(default=0)
    downvote = models.PositiveIntegerField(default=0)
    upvotes = models.ManyToManyField(User, related_name='upvoted_pdfs')
    downvotes = models.ManyToManyField(User, related_name='downvoted_pdfs')
    topic = models.CharField(max_length=100)
