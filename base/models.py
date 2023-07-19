from django.db import models


# Create your models here.

class Node(models.Model):
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name


class NodeMessage(models.Model):
    node = models.ForeignKey(Node, on_delete=models.DO_NOTHING)
    battery_level = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    illumination = models.FloatField()
    mq2PPM = models.FloatField() # 烟雾浓度
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']


