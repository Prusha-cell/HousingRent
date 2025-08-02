from django.db import models


class ReviewRating(models.IntegerChoices):
    ONE = 1, 'Poor'
    TWO = 2, 'Fair'
    THREE = 3, 'Good'
    FOUR = 4, 'Very Good'
    FIVE = 5, 'Excellent'
