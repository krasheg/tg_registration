from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_tg_id = models.IntegerField(null=True, blank=True)
    username = models.CharField(max_length=60, null=True, blank=True)
    first_name = models.CharField(max_length=60, null=True, blank=True)
    last_name = models.CharField(max_length=60, null=True, blank=True)
    photo = models.ImageField(blank=True, null=True, upload_to='media',
                              default='/media/base.png')

    def __str__(self):
        return f'{self.user.username}, {self.username=}, {self.first_name=}, {self.photo}'
