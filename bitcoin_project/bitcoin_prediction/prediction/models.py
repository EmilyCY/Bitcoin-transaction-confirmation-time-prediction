from django.db import models

# Create your models here.
class Transaction(models.Model):
    index = models.IntegerField()
    inputs = models.IntegerField()
    outputs = models.IntegerField()
    trans_version = models.IntegerField()
    trans_size = models.IntegerField()
    trans_weight = models.IntegerField()
    received_time = models.IntegerField()
    relay_node = models.IntegerField()
    locktime = models.IntegerField()
    trans_fee = models.FloatField()
    confirmed_block_height = models.IntegerField()
    index_block_height = models.IntegerField()
    confirm_time = models.IntegerField()
    waiting_time = models.FloatField()
    feerate = models.FloatField()
    enter_block_height = models.IntegerField()
    waiting_block_num = models.IntegerField()
    valid_time = models.FloatField()
    valid_block_height = models.IntegerField()
    valid_waiting = models.FloatField()
    last_block_interval = models.FloatField()

    class Meta:
        db_table = 'transaction'